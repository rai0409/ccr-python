from __future__ import annotations

import io
import json

from ccr.cli import main
from ccr.cli.main import run_cli
from ccr.policy.engine import PermissionEngine
from ccr.storage.transcript_store import TranscriptStore
from ccr.tools.executor import ToolExecutor, ToolIntent
from helpers.fake_provider import ScriptedProvider


class _MissingToolRegistry:
    def get(self, tool_name: str):
        return None


class _StaticRegistry:
    def __init__(self, tool):
        self._tool = tool

    def get(self, tool_name: str):
        if tool_name == "Read":
            return self._tool
        return None


class _OkTool:
    name = "Read"

    def execute(self, tool_input: dict, context) -> dict:
        return {"status": "success", "content": "ok"}


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


def test_tool_executor_ask_mode_allow_once_executes() -> None:
    emitted: list[dict] = []

    def _emit(event_type: str, **kwargs):
        emitted.append({"type": event_type, **kwargs})

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=_emit,
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )

    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[2]["payload"]["decision"] == "allow"
    assert emitted[3]["payload"]["tool_name"] == "Read"
    assert emitted[4]["payload"]["result"]["status"] == "success"
    assert emitted[5]["payload"]["status"] == "success"
    assert outcome.status == "success"


def test_tool_executor_ask_mode_deny_once_denies() -> None:
    emitted: list[dict] = []

    def _emit(event_type: str, **kwargs):
        emitted.append({"type": event_type, **kwargs})

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=_emit,
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "deny_once",
    )

    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[2]["payload"]["decision"] == "deny"
    assert emitted[3]["payload"]["result"]["status"] == "denied"
    assert emitted[4]["payload"]["status"] == "denied"
    assert outcome.status == "denied"


def test_tool_executor_ask_mode_missing_decision_denies_ask_unavailable() -> None:
    emitted: list[dict] = []

    def _emit(event_type: str, **kwargs):
        emitted.append({"type": event_type, **kwargs})

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=_emit,
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: None,
    )

    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[2]["payload"]["decision"] == "deny"
    assert emitted[2]["payload"]["reason_code"] == "ask_unavailable"
    assert emitted[3]["payload"]["result"]["status"] == "denied"
    assert emitted[4]["payload"]["status"] == "denied"
    assert outcome.status == "denied"


def test_tool_executor_ask_mode_noninteractive_denies_without_required() -> None:
    emitted: list[dict] = []

    def _emit(event_type: str, **kwargs):
        emitted.append({"type": event_type, **kwargs})

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=_emit,
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=False,
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
    assert outcome.status == "denied"


def test_runtime_ask_mode_stream_allow_once_persists_permission_required(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider(
            [{"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}}, {"emit": "assistant_message", "content": "OK"}]
        ),
    )

    with open("/tmp/ccr_ws/a.txt", "w", encoding="utf-8") as f:
        f.write("alpha\n")

    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=["-p", "--permission-mode", "ask", "--input-format", "stream-json", "--output-format", "stream-json", "--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"],
        stdin=io.StringIO(
            "\n".join(
                [
                    json.dumps({"type": "user_message", "content": "read"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "allow_once"}),
                ]
            )
            + "\n"
        ),
        stdout=out,
        stderr=err,
    )
    assert code == 0

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S1")
    assert [r["type"] for r in records] == [
        "session_start",
        "user_message",
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
        "assistant_message",
        "session_completed",
    ]
    decided = [r for r in records if r["type"] == "tool_permission_decided"][0]
    assert decided["payload"]["decision"] == "allow"
    assert decided["tool_call_id"] == "TC1"


def test_runtime_ask_mode_stream_deny_once(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider([{"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}}]),
    )

    with open("/tmp/ccr_ws/a.txt", "w", encoding="utf-8") as f:
        f.write("alpha\n")

    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=["-p", "--permission-mode", "ask", "--input-format", "stream-json", "--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"],
        stdin=io.StringIO(
            "\n".join(
                [
                    json.dumps({"type": "user_message", "content": "read"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "deny_once"}),
                ]
            )
            + "\n"
        ),
        stdout=out,
        stderr=err,
    )
    assert code == 5

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S1")
    assert [r["type"] for r in records] == [
        "session_start",
        "user_message",
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
        "session_failed",
    ]
    decided = [r for r in records if r["type"] == "tool_permission_decided"][0]
    assert decided["payload"]["decision"] == "deny"


def test_runtime_ask_mode_stream_missing_decision_denies_ask_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider([{"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}}]),
    )

    with open("/tmp/ccr_ws/a.txt", "w", encoding="utf-8") as f:
        f.write("alpha\n")

    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=["-p", "--permission-mode", "ask", "--input-format", "stream-json", "--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"],
        stdin=io.StringIO(json.dumps({"type": "user_message", "content": "read"}) + "\n"),
        stdout=out,
        stderr=err,
    )
    assert code == 6

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S1")
    decided = [r for r in records if r["type"] == "tool_permission_decided"][0]
    assert decided["payload"]["decision"] == "deny"
    assert decided["payload"]["reason_code"] == "ask_unavailable"
