from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ccr.cli import exit_codes
from ccr.cli.io_modes import InputMode
from ccr.model.provider_base import ModelRequest, ProviderBase
from ccr.model.retry_fallback import RetryFallbackManager
from ccr.model.stream_adapter import ModelStreamAdapter
from ccr.policy.engine import PermissionEngine
from ccr.runtime.recovery import classify_tool_call_recovery
from ccr.runtime.recovery_policy import decide_recovery_action
from ccr.storage.permission_rule_store import PermissionRuleStore
from ccr.storage.session_index import SessionIndex
from ccr.storage.transcript_store import TranscriptStore
from ccr.tools.executor import ToolExecutionOutcome, ToolExecutor, ToolIntent
from ccr.tools.registry import ToolRegistry
from ccr.util.ids import new_run_id, new_session_id
from ccr.util.time import now_rfc3339

from .context import SessionConfig
from .event_bus import EventBus
from .events import EventEnvelope
from .turn_fsm import TurnStateMachine


_SESSION_REPLAY_STATE: dict[str, dict[str, set[str]]] = {}


@dataclass(frozen=True)
class RunResult:
    status: str
    exit_code: int
    session_id: str
    run_id: str
    final_assistant_message: str | None


class SessionOrchestrator:
    def __init__(
        self,
        *,
        config: SessionConfig,
        provider: ProviderBase,
        transcript_store: TranscriptStore,
        session_index: SessionIndex,
        event_bus: EventBus,
    ) -> None:
        self.config = config
        self.provider = provider
        self.transcript_store = transcript_store
        self.session_index = session_index
        self.event_bus = event_bus

        self.retry_manager = RetryFallbackManager()
        self.stream_adapter = ModelStreamAdapter()
        self.fsm = TurnStateMachine()

        self.permission_engine = PermissionEngine(cwd=config.cwd)
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(
            registry=self.tool_registry,
            permission_engine=self.permission_engine,
            emit=self._emit,
            cwd=config.cwd,
        )
        self.permission_rule_store = PermissionRuleStore(
            config.transcript_dir,
            enabled=not config.no_session_persistence,
        )

        self._seq = 0
        self._last_persisted_event_id: str | None = None
        self._run_terminal_emitted = False
        self._tool_call_counter = 0
        self._permission_decisions: dict[str, list[str]] = {}

    def _interactive_available(self) -> bool:
        return self.config.input_mode is InputMode.STREAM_JSON or not self.config.print_mode

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _next_tool_call_id(self) -> str:
        self._tool_call_counter += 1
        return f"TC{self._tool_call_counter}"

    def _emit(
        self,
        event_type: str,
        *,
        payload: dict[str, Any],
        turn_index: int,
        message_id: str | None = None,
        tool_call_id: str | None = None,
        permission_meta: dict[str, Any] | None = None,
    ) -> EventEnvelope:
        if event_type in {"session_completed", "session_failed"}:
            if self._run_terminal_emitted:
                raise RuntimeError("terminal event already emitted for run")
            self._run_terminal_emitted = True

        seq = self._next_seq()
        evt = EventEnvelope(
            event_id=f"E{seq}",
            session_id=self._session_id,
            run_id=self._run_id,
            seq=seq,
            ts=now_rfc3339(),
            type=event_type,
            turn_index=turn_index,
            payload=payload,
            parent_event_id=self._last_persisted_event_id,
            message_id=message_id,
            tool_call_id=tool_call_id,
            model=self.config.model,
            meta={"permission_meta": permission_meta} if permission_meta is not None else None,
        )

        self.fsm.transition(event_type)
        self.transcript_store.append_event(evt)
        if evt.persisted:
            self._last_persisted_event_id = evt.event_id
        self.event_bus.emit(evt)
        return evt

    def _resolve_session_and_run(self) -> tuple[str, str, bool]:
        resumed = False
        if self.config.do_continue:
            sid = self.session_index.get_latest_for_cwd(self.config.cwd)
            if sid is None:
                raise RuntimeError("no session to continue")
            resumed = True
        elif self.config.resume_session_id:
            sid = self.config.resume_session_id
            resumed = True
        else:
            sid = self.config.forced_session_id or new_session_id()

        if resumed:
            records = self.transcript_store.load_records(sid)
            run_nums: list[int] = []
            for rec in records:
                rid = str(rec.get("run_id", ""))
                if rid.startswith("R") and rid[1:].isdigit():
                    run_nums.append(int(rid[1:]))
            if run_nums:
                return sid, f"R{max(run_nums) + 1}", resumed
        return sid, new_run_id(), resumed

    def _extract_prompt(self, stream_messages: list[dict]) -> str:
        if self.config.input_mode is InputMode.TEXT:
            return self.config.prompt
        for msg in stream_messages:
            if msg.get("type") == "user_message":
                return str(msg.get("content", ""))
        raise RuntimeError("missing user_message")

    def _load_permission_decisions(self, stream_messages: list[dict]) -> None:
        self._permission_decisions = {}
        for msg in stream_messages:
            if msg.get("type") != "permission_decision":
                continue
            tool_call_id = str(msg.get("tool_call_id", ""))
            if tool_call_id == "":
                continue
            decision = str(msg.get("decision", ""))
            self._permission_decisions.setdefault(tool_call_id, []).append(decision)

    def _consume_permission_decision(self, tool_call_id: str) -> str | None:
        queue = self._permission_decisions.get(tool_call_id)
        if not queue:
            return None
        value = queue.pop(0)
        if not queue:
            self._permission_decisions.pop(tool_call_id, None)
        return value

    def _failure_result_for_tool_outcome(self, *, outcome: ToolExecutionOutcome, turn_index: int) -> RunResult | None:
        if outcome.status == "denied":
            if outcome.decision.reason_code == "ask_unavailable":
                exit_code = exit_codes.PERMISSION_UNAVAILABLE
            else:
                exit_code = exit_codes.PERMISSION_DENIED
            self._emit(
                "session_failed",
                payload={"error_code": "PERMISSION_DENIED", "error_message": outcome.decision.reason_code},
                turn_index=turn_index,
            )
            self.session_index.update(session_id=self._session_id, cwd=self.config.cwd, ts=now_rfc3339())
            return RunResult(
                status="failed",
                exit_code=exit_code,
                session_id=self._session_id,
                run_id=self._run_id,
                final_assistant_message=None,
            )
        if outcome.status != "success":
            self._emit(
                "session_failed",
                payload={"error_code": "TOOL_RUNTIME_FAILURE", "error_message": "tool failed"},
                turn_index=turn_index,
            )
            self.session_index.update(session_id=self._session_id, cwd=self.config.cwd, ts=now_rfc3339())
            return RunResult(
                status="failed",
                exit_code=exit_codes.TOOL_RUNTIME_FAILURE,
                session_id=self._session_id,
                run_id=self._run_id,
                final_assistant_message=None,
            )
        return None

    def _recover_interrupted_safe_read_once(self, *, turn_index: int) -> ToolExecutionOutcome | None:
        records = self.transcript_store.load_records(self._session_id)
        last_request: dict[str, Any] | None = None
        for rec in reversed(records):
            if str(rec.get("type", "")) == "tool_call_requested":
                last_request = rec
                break
        if last_request is None:
            return None

        tool_call_id = str(last_request.get("tool_call_id", ""))
        if tool_call_id == "":
            return None
        payload = last_request.get("payload")
        if not isinstance(payload, dict):
            return None

        tool_name = str(payload.get("tool_name", ""))
        tool_input = payload.get("input")
        if tool_name == "" or not isinstance(tool_input, dict):
            return None

        try:
            recovery = classify_tool_call_recovery(records, tool_call_id)
        except ValueError:
            return None

        action = decide_recovery_action(recovery, tool_name)
        if action != "eligible_for_retry":
            return None

        outcome = self.tool_executor.execute(
            intent=ToolIntent(
                tool_call_id=self._next_tool_call_id(),
                tool_name=tool_name,
                tool_input=dict(tool_input),
            ),
            mode=self.config.permission_mode,
            interactive_available=self._interactive_available(),
            turn_index=turn_index,
            resolve_permission=self._consume_permission_decision,
        )
        return outcome

    def run(self, *, stream_messages: list[dict]) -> RunResult:
        self._session_id, self._run_id, resumed = self._resolve_session_and_run()
        next_seq = self.transcript_store.get_next_seq(self._session_id)
        self._seq = next_seq - 1
        self._last_persisted_event_id = self.transcript_store.get_last_persisted_event_id(self._session_id)
        self._tool_call_counter = 0
        self._load_permission_decisions(stream_messages)

        if next_seq == 1:
            _SESSION_REPLAY_STATE[self._session_id] = {"allow": set(), "deny": set()}
        replay_state = _SESSION_REPLAY_STATE.setdefault(self._session_id, {"allow": set(), "deny": set()})
        self.tool_executor.bind_session_replay_state(
            allow_hashes=replay_state["allow"],
            deny_hashes=replay_state["deny"],
        )
        persistent_allow_hashes, persistent_deny_hashes = self.permission_rule_store.load_hash_sets()
        self.tool_executor.bind_persistent_replay_state(
            allow_hashes=persistent_allow_hashes,
            deny_hashes=persistent_deny_hashes,
            persist_rule=self.permission_rule_store.append_rule,
        )

        if resumed:
            self._emit(
                "session_resumed",
                payload={"resume_from_session_id": self._session_id, "forked": False},
                turn_index=0,
            )
        else:
            self._emit(
                "session_start",
                payload={
                    "cwd": self.config.cwd,
                    "permission_mode": self.config.permission_mode,
                    "model": self.config.model,
                },
                turn_index=0,
            )

        prompt = self._extract_prompt(stream_messages)
        self._emit(
            "user_message",
            payload={
                "content": prompt,
                "input_mode": self.config.input_mode.value,
            },
            turn_index=1,
            message_id="M_USER_1",
        )

        recovery_had_tool_call = False
        if resumed:
            recovery_outcome = self._recover_interrupted_safe_read_once(turn_index=1)
            if recovery_outcome is not None:
                recovery_had_tool_call = True
                failed = self._failure_result_for_tool_outcome(outcome=recovery_outcome, turn_index=1)
                if failed is not None:
                    return failed

        request = ModelRequest(prompt=prompt, model=self.config.model)
        chunks = self.retry_manager.run(self.provider, request).chunks

        final_message: str | None = None
        had_tool_call = recovery_had_tool_call
        assistant_msg_id = "M_ASSISTANT_1"

        for adapted in self.stream_adapter.adapt(chunks):
            if adapted.kind == "assistant_delta":
                self._emit(
                    "assistant_delta",
                    payload={"delta": str(adapted.content)},
                    turn_index=1,
                    message_id=assistant_msg_id,
                )
            elif adapted.kind == "assistant_message":
                final_message = str(adapted.content)
                self._emit(
                    "assistant_message",
                    payload={"content": final_message},
                    turn_index=1,
                    message_id=assistant_msg_id,
                )
            elif adapted.kind == "tool_call":
                had_tool_call = True
                payload = dict(adapted.content)
                intent = ToolIntent(
                    tool_call_id=self._next_tool_call_id(),
                    tool_name=str(payload["tool_name"]),
                    tool_input=dict(payload.get("input", {})),
                )
                outcome = self.tool_executor.execute(
                    intent=intent,
                    mode=self.config.permission_mode,
                    interactive_available=self._interactive_available(),
                    turn_index=1,
                    resolve_permission=self._consume_permission_decision,
                )
                failed = self._failure_result_for_tool_outcome(outcome=outcome, turn_index=1)
                if failed is not None:
                    return failed
            else:
                raise RuntimeError(f"unsupported adapted kind: {adapted.kind}")

        if final_message is None and not had_tool_call:
            self._emit(
                "session_failed",
                payload={"error_code": "MODEL_NO_MESSAGE", "error_message": "provider produced no assistant message"},
                turn_index=1,
            )
            self.session_index.update(session_id=self._session_id, cwd=self.config.cwd, ts=now_rfc3339())
            return RunResult(
                status="failed",
                exit_code=exit_codes.MODEL_FAILURE,
                session_id=self._session_id,
                run_id=self._run_id,
                final_assistant_message=None,
            )

        self._emit("session_completed", payload={"status": "completed"}, turn_index=1)
        self.session_index.update(session_id=self._session_id, cwd=self.config.cwd, ts=now_rfc3339())

        return RunResult(
            status="completed",
            exit_code=exit_codes.SUCCESS,
            session_id=self._session_id,
            run_id=self._run_id,
            final_assistant_message=final_message,
        )
