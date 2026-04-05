from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ccr.cli import exit_codes
from ccr.cli.io_modes import InputMode
from ccr.model.provider_base import ModelRequest, ProviderBase
from ccr.model.retry_fallback import RetryFallbackManager
from ccr.model.stream_adapter import ModelStreamAdapter
from ccr.storage.session_index import SessionIndex
from ccr.storage.transcript_store import TranscriptStore
from ccr.util.ids import new_run_id, new_session_id
from ccr.util.time import now_rfc3339

from .context import SessionConfig
from .event_bus import EventBus
from .events import EventEnvelope
from .turn_fsm import TurnStateMachine


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

        self._seq = 0
        self._last_persisted_event_id: str | None = None
        self._run_terminal_emitted = False

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _emit(self, event_type: str, *, payload: dict[str, Any], turn_index: int, message_id: str | None = None) -> EventEnvelope:
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
            model=self.config.model,
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

    def run(self, *, stream_messages: list[dict]) -> RunResult:
        self._session_id, self._run_id, resumed = self._resolve_session_and_run()
        self._seq = self.transcript_store.get_next_seq(self._session_id) - 1
        self._last_persisted_event_id = self.transcript_store.get_last_persisted_event_id(self._session_id)

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
        user_msg_id = "M_USER_1"
        self._emit(
            "user_message",
            payload={
                "content": prompt,
                "input_mode": self.config.input_mode.value,
            },
            turn_index=1,
            message_id=user_msg_id,
        )

        request = ModelRequest(prompt=prompt, model=self.config.model)
        chunks = self.retry_manager.run(self.provider, request).chunks

        final_message: str | None = None
        assistant_msg_id = "M_ASSISTANT_1"
        for adapted in self.stream_adapter.adapt(chunks):
            if adapted.kind == "assistant_delta":
                self._emit(
                    "assistant_delta",
                    payload={"delta": adapted.content},
                    turn_index=1,
                    message_id=assistant_msg_id,
                )
            elif adapted.kind == "assistant_message":
                final_message = adapted.content
                self._emit(
                    "assistant_message",
                    payload={"content": adapted.content},
                    turn_index=1,
                    message_id=assistant_msg_id,
                )

        if final_message is None:
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
