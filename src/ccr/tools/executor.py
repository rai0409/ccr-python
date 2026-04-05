from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ccr.policy.engine import PermissionDecision, PermissionEngine
from ccr.tools.base import ToolExecutionContext
from ccr.tools.registry import ToolRegistry


@dataclass(frozen=True)
class ToolIntent:
    tool_call_id: str
    tool_name: str
    tool_input: dict[str, Any]


@dataclass(frozen=True)
class ToolExecutionOutcome:
    status: str
    decision: PermissionDecision


class ToolExecutor:
    def __init__(
        self,
        *,
        registry: ToolRegistry,
        permission_engine: PermissionEngine,
        emit: Callable[..., Any],
        cwd: str,
    ) -> None:
        self.registry = registry
        self.permission_engine = permission_engine
        self.emit = emit
        self.context = ToolExecutionContext(cwd=cwd)

    def execute(
        self,
        *,
        intent: ToolIntent,
        mode: str,
        interactive_available: bool,
        turn_index: int,
    ) -> ToolExecutionOutcome:
        self.emit(
            "tool_call_requested",
            payload={"tool_name": intent.tool_name, "input": intent.tool_input},
            turn_index=turn_index,
            tool_call_id=intent.tool_call_id,
        )

        decision = self.permission_engine.decide(
            tool_name=intent.tool_name,
            tool_input=intent.tool_input,
            mode=mode,
            interactive_available=interactive_available,
        )

        self.emit(
            "tool_permission_decided",
            payload=decision.to_payload() | {"tool_call_id": intent.tool_call_id},
            turn_index=turn_index,
            tool_call_id=intent.tool_call_id,
            permission_meta={
                "mode": decision.mode,
                "decision": decision.decision,
                "reason_code": decision.reason_code,
                "precedence_rank": decision.precedence_rank,
                "decision_source": decision.decision_source,
                "risk_label": decision.risk_label,
                "request_hash": decision.request_hash,
            },
        )

        if decision.decision != "allow":
            self.emit(
                "tool_result",
                payload={"result": {"status": "denied"}},
                turn_index=turn_index,
                tool_call_id=intent.tool_call_id,
            )
            self.emit(
                "tool_execution_finished",
                payload={"status": "denied"},
                turn_index=turn_index,
                tool_call_id=intent.tool_call_id,
            )
            return ToolExecutionOutcome(status="denied", decision=decision)

        tool = self.registry.get(intent.tool_name)
        if tool is None:
            # Phase 2A keeps unsupported tools denied via ask_unavailable fallback semantics.
            fallback = PermissionDecision(
                mode=mode,
                decision="deny",
                reason_code="ask_unavailable",
                precedence_rank=9 if mode != "ask" else 6,
                decision_source="mode",
                risk_label="unknown",
                request_hash=decision.request_hash,
            )
            self.emit(
                "tool_result",
                payload={"result": {"status": "denied"}},
                turn_index=turn_index,
                tool_call_id=intent.tool_call_id,
            )
            self.emit(
                "tool_execution_finished",
                payload={"status": "denied"},
                turn_index=turn_index,
                tool_call_id=intent.tool_call_id,
            )
            return ToolExecutionOutcome(status="denied", decision=fallback)

        self.emit(
            "tool_execution_started",
            payload={"tool_name": intent.tool_name},
            turn_index=turn_index,
            tool_call_id=intent.tool_call_id,
        )

        result = tool.execute(intent.tool_input, self.context)
        status = str(result.get("status", "success"))

        self.emit(
            "tool_result",
            payload={"result": result},
            turn_index=turn_index,
            tool_call_id=intent.tool_call_id,
        )
        self.emit(
            "tool_execution_finished",
            payload={"status": status},
            turn_index=turn_index,
            tool_call_id=intent.tool_call_id,
        )
        return ToolExecutionOutcome(status=status, decision=decision)
