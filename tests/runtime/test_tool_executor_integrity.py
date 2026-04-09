from __future__ import annotations

from ccr.policy.engine import PermissionEngine
from ccr.tools.executor import ToolExecutor, ToolIntent


class _MissingToolRegistry:
    def get(self, tool_name: str):
        return None


def test_tool_executor_no_decision_divergence_when_tool_missing() -> None:
    emitted: list[dict] = []

    def _emit(event_type: str, **kwargs):
        emitted.append({"type": event_type, **kwargs})

    executor = ToolExecutor(
        registry=_MissingToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=_emit,
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="auto",
        interactive_available=False,
        turn_index=1,
    )

    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["decision"] == "allow"
    assert emitted[1]["payload"]["reason_code"] == "auto_safe"
    assert emitted[3]["payload"]["result"]["status"] == "error"
    assert emitted[4]["payload"]["status"] == "error"

    assert outcome.status == "error"
    assert outcome.decision.decision == "allow"
    assert outcome.decision.reason_code == "auto_safe"


def test_tool_executor_ask_mode_denied_without_permission_required() -> None:
    emitted: list[dict] = []

    def _emit(event_type: str, **kwargs):
        emitted.append({"type": event_type, **kwargs})

    executor = ToolExecutor(
        registry=_MissingToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=_emit,
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
    )

    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["decision"] == "deny"
    assert emitted[1]["payload"]["reason_code"] == "ask_unavailable"
    assert emitted[2]["payload"]["result"]["status"] == "denied"
    assert emitted[3]["payload"]["status"] == "denied"
    assert outcome.status == "denied"
