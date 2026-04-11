from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


RecoveryState = Literal["completed", "denied", "interrupted", "not_found"]


@dataclass(frozen=True)
class ToolCallRecovery:
    tool_call_id: str
    state: RecoveryState


def classify_tool_call_recovery(records: list[dict[str, Any]], tool_call_id: str) -> ToolCallRecovery:
    matched = [rec for rec in records if str(rec.get("tool_call_id", "")) == tool_call_id]
    if not matched:
        return ToolCallRecovery(tool_call_id=tool_call_id, state="not_found")

    has_started = False
    has_finished = False
    has_permission_deny = False
    has_result_denied = False

    for rec in matched:
        event_type = str(rec.get("type", ""))
        if event_type == "tool_execution_started":
            has_started = True
        elif event_type == "tool_execution_finished":
            has_finished = True
        elif event_type == "tool_permission_decided":
            payload = rec.get("payload")
            if isinstance(payload, dict) and str(payload.get("decision", "")) == "deny":
                has_permission_deny = True
        elif event_type == "tool_result":
            payload = rec.get("payload")
            if not isinstance(payload, dict):
                continue
            result = payload.get("result")
            if isinstance(result, dict) and str(result.get("status", "")) == "denied":
                has_result_denied = True

    if has_permission_deny and not has_started and (has_finished or has_result_denied):
        return ToolCallRecovery(tool_call_id=tool_call_id, state="denied")

    if has_finished:
        return ToolCallRecovery(tool_call_id=tool_call_id, state="completed")

    if has_started:
        return ToolCallRecovery(tool_call_id=tool_call_id, state="interrupted")

    raise ValueError(f"unclassifiable pre-start partial records for tool_call_id={tool_call_id}")
