from __future__ import annotations

import io
import json
import shlex
import sys
from pathlib import Path
from unittest import mock

from ccr.cli import main
from ccr.cli.main import run_cli
from ccr.policy.engine import PermissionEngine
from ccr.storage.transcript_store import TranscriptStore
from ccr.tools.executor import ToolExecutor, ToolIntent
from ccr.tools.registry import ToolRegistry
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


def test_tool_executor_allow_session_replays_without_permission_required() -> None:
    first: list[dict] = []
    second: list[dict] = []

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: first.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    intent = ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"})
    outcome1 = executor.execute(
        intent=intent,
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_session",
    )
    assert outcome1.status == "success"
    assert [e["type"] for e in first] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]

    executor.emit = lambda event_type, **kwargs: second.append({"type": event_type, **kwargs})  # type: ignore[method-assign]
    outcome2 = executor.execute(
        intent=ToolIntent(tool_call_id="TC2", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: None,
    )
    assert outcome2.status == "success"
    assert [e["type"] for e in second] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert second[1]["payload"]["decision"] == "allow"
    assert second[1]["payload"]["reason_code"] == "session_rule_allow"


def test_tool_executor_deny_session_replays_without_permission_required() -> None:
    first: list[dict] = []
    second: list[dict] = []

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: first.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome1 = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "deny_session",
    )
    assert outcome1.status == "denied"
    assert [e["type"] for e in first] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]

    executor.emit = lambda event_type, **kwargs: second.append({"type": event_type, **kwargs})  # type: ignore[method-assign]
    outcome2 = executor.execute(
        intent=ToolIntent(tool_call_id="TC2", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )
    assert outcome2.status == "denied"
    assert [e["type"] for e in second] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert second[1]["payload"]["decision"] == "deny"
    assert second[1]["payload"]["reason_code"] == "session_rule_deny"


def test_tool_executor_allow_persistent_replays_without_permission_required() -> None:
    first: list[dict] = []
    second: list[dict] = []

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: first.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome1 = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_persistent",
    )
    assert outcome1.status == "success"
    assert [e["type"] for e in first] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]

    executor.emit = lambda event_type, **kwargs: second.append({"type": event_type, **kwargs})  # type: ignore[method-assign]
    outcome2 = executor.execute(
        intent=ToolIntent(tool_call_id="TC2", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: None,
    )
    assert outcome2.status == "success"
    assert [e["type"] for e in second] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert second[1]["payload"]["decision"] == "allow"
    assert second[1]["payload"]["reason_code"] == "persistent_rule_allow"


def test_tool_executor_deny_persistent_replays_without_permission_required() -> None:
    first: list[dict] = []
    second: list[dict] = []

    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: first.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome1 = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "deny_persistent",
    )
    assert outcome1.status == "denied"
    assert [e["type"] for e in first] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]

    executor.emit = lambda event_type, **kwargs: second.append({"type": event_type, **kwargs})  # type: ignore[method-assign]
    outcome2 = executor.execute(
        intent=ToolIntent(tool_call_id="TC2", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )
    assert outcome2.status == "denied"
    assert [e["type"] for e in second] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert second[1]["payload"]["decision"] == "deny"
    assert second[1]["payload"]["reason_code"] == "persistent_rule_deny"


def test_tool_executor_hard_boundary_overrides_replayed_allow() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    boundary = executor.permission_engine.decide(
        tool_name="Write",
        tool_input={"path": "/etc/hosts", "content": "x"},
        mode="ask",
        interactive_available=True,
    )
    executor._session_allow_hashes.add(boundary.request_hash)

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Write", tool_input={"path": "/etc/hosts", "content": "x"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_session",
    )
    assert outcome.status == "denied"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["reason_code"] == "hard_boundary_path_outside_root"


def test_tool_executor_hard_boundary_overrides_replayed_persistent_allow() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    boundary = executor.permission_engine.decide(
        tool_name="Write",
        tool_input={"path": "/etc/hosts", "content": "x"},
        mode="ask",
        interactive_available=True,
    )
    executor._persistent_allow_hashes.add(boundary.request_hash)

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Write", tool_input={"path": "/etc/hosts", "content": "x"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_persistent",
    )
    assert outcome.status == "denied"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["reason_code"] == "hard_boundary_path_outside_root"


def test_tool_executor_deny_precedence_over_allow_when_both_match() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    decision = executor.permission_engine.decide(
        tool_name="Read",
        tool_input={"path": "/tmp/ccr_ws/a.txt"},
        mode="ask",
        interactive_available=True,
    )
    executor._session_allow_hashes.add(decision.request_hash)
    executor._session_deny_hashes.add(decision.request_hash)

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )
    assert outcome.status == "denied"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["reason_code"] == "session_rule_deny"


def test_tool_executor_deny_precedence_over_persistent_allow_when_both_match() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    decision = executor.permission_engine.decide(
        tool_name="Read",
        tool_input={"path": "/tmp/ccr_ws/a.txt"},
        mode="ask",
        interactive_available=True,
    )
    executor._persistent_allow_hashes.add(decision.request_hash)
    executor._persistent_deny_hashes.add(decision.request_hash)

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )
    assert outcome.status == "denied"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["reason_code"] == "persistent_rule_deny"


def test_tool_executor_mixed_source_persistent_deny_over_session_allow() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=_StaticRegistry(_OkTool()),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    decision = executor.permission_engine.decide(
        tool_name="Read",
        tool_input={"path": "/tmp/ccr_ws/a.txt"},
        mode="ask",
        interactive_available=True,
    )
    executor._session_allow_hashes.add(decision.request_hash)
    executor._persistent_deny_hashes.add(decision.request_hash)

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Read", tool_input={"path": "/tmp/ccr_ws/a.txt"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )
    assert outcome.status == "denied"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["reason_code"] == "persistent_rule_deny"


def test_tool_executor_write_success_and_lifecycle() -> None:
    emitted: list[dict] = []
    target = Path("/tmp/ccr_ws/write.txt")
    if target.exists():
        target.unlink()

    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC1",
            tool_name="Write",
            tool_input={"path": "/tmp/ccr_ws/write.txt", "content": "alpha\n"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )

    assert outcome.status == "success"
    assert target.read_text(encoding="utf-8") == "alpha\n"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[4]["payload"]["result"]["status"] == "success"


def test_tool_executor_edit_success_replaces_first_match() -> None:
    emitted: list[dict] = []
    target = Path("/tmp/ccr_ws/edit.txt")
    target.write_text("one two one\n", encoding="utf-8")

    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC1",
            tool_name="Edit",
            tool_input={"path": "/tmp/ccr_ws/edit.txt", "find": "one", "replace": "ONE"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )

    assert outcome.status == "success"
    assert target.read_text(encoding="utf-8") == "ONE two one\n"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[4]["payload"]["result"]["status"] == "success"


def test_tool_executor_edit_failure_when_find_target_missing() -> None:
    emitted: list[dict] = []
    target = Path("/tmp/ccr_ws/edit_missing_target.txt")
    target.write_text("alpha beta\n", encoding="utf-8")

    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC1",
            tool_name="Edit",
            tool_input={"path": "/tmp/ccr_ws/edit_missing_target.txt", "find": "gamma", "replace": "G"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )

    assert outcome.status == "error"
    assert target.read_text(encoding="utf-8") == "alpha beta\n"
    assert emitted[4]["payload"]["result"]["status"] == "error"
    assert emitted[4]["payload"]["result"]["error"]["code"] == "FIND_TARGET_NOT_FOUND"


def test_tool_executor_bash_success_runs_in_cwd() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Bash", tool_input={"command": "pwd"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )

    assert outcome.status == "success"
    result = emitted[4]["payload"]["result"]
    assert result["status"] == "success"
    assert result["exit_code"] == 0
    assert str(result["stdout"]).strip() == "/tmp/ccr_ws"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]


def test_tool_executor_bash_nonzero_exit_returns_error_with_exit_code() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )
    command = f"{shlex.quote(sys.executable)} -c \"import sys; sys.exit(7)\""

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Bash", tool_input={"command": command}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )

    assert outcome.status == "error"
    result = emitted[4]["payload"]["result"]
    assert result["status"] == "error"
    assert result["exit_code"] == 7
    assert "stdout" in result
    assert "stderr" in result


def test_tool_executor_bash_invalid_command_returns_execution_failed_error() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC1",
            tool_name="Bash",
            tool_input={"command": "ccr_nonexistent_command_12345"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )

    assert outcome.status == "error"
    result = emitted[4]["payload"]["result"]
    assert result["status"] == "error"
    assert result["exit_code"] is None
    assert result["error"]["code"] == "COMMAND_EXECUTION_FAILED"


def test_tool_executor_bash_timeout_returns_timeout_error() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )
    command = f"{shlex.quote(sys.executable)} -c \"import time; time.sleep(0.2)\""

    with mock.patch("ccr.tools.builtins.bash_tool._BASH_TIMEOUT_SECONDS", 0.01):
        outcome = executor.execute(
            intent=ToolIntent(tool_call_id="TC1", tool_name="Bash", tool_input={"command": command}),
            mode="ask",
            interactive_available=True,
            turn_index=1,
            resolve_permission=lambda _tcid: "allow_once",
        )

    assert outcome.status == "error"
    result = emitted[4]["payload"]["result"]
    assert result["status"] == "error"
    assert result["exit_code"] is None
    assert result["error"]["code"] == "COMMAND_TIMEOUT"


def test_tool_executor_permission_deny_blocks_bash_execution() -> None:
    emitted: list[dict] = []
    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Bash", tool_input={"command": "pwd"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "deny_once",
    )

    assert outcome.status == "denied"
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]


def test_tool_executor_bash_allow_session_replay_avoids_permission_required() -> None:
    first: list[dict] = []
    second: list[dict] = []
    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: first.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome1 = executor.execute(
        intent=ToolIntent(tool_call_id="TC1", tool_name="Bash", tool_input={"command": "pwd"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_session",
    )
    assert outcome1.status == "success"

    executor.emit = lambda event_type, **kwargs: second.append({"type": event_type, **kwargs})  # type: ignore[method-assign]
    outcome2 = executor.execute(
        intent=ToolIntent(tool_call_id="TC2", tool_name="Bash", tool_input={"command": "pwd"}),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: None,
    )
    assert outcome2.status == "success"
    assert [e["type"] for e in second] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert second[1]["payload"]["reason_code"] == "session_rule_allow"


def test_tool_executor_permission_deny_blocks_write_execution() -> None:
    emitted: list[dict] = []
    target = Path("/tmp/ccr_ws/blocked_write.txt")
    if target.exists():
        target.unlink()

    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC1",
            tool_name="Write",
            tool_input={"path": "/tmp/ccr_ws/blocked_write.txt", "content": "blocked"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "deny_once",
    )

    assert outcome.status == "denied"
    assert not target.exists()
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]


def test_tool_executor_replay_allows_write_without_permission_required() -> None:
    first: list[dict] = []
    second: list[dict] = []
    target = Path("/tmp/ccr_ws/replay_write.txt")

    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: first.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome1 = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC1",
            tool_name="Write",
            tool_input={"path": "/tmp/ccr_ws/replay_write.txt", "content": "v1"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_session",
    )
    assert outcome1.status == "success"

    executor.emit = lambda event_type, **kwargs: second.append({"type": event_type, **kwargs})  # type: ignore[method-assign]
    outcome2 = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC2",
            tool_name="Write",
            tool_input={"path": "/tmp/ccr_ws/replay_write.txt", "content": "v1"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: None,
    )
    assert outcome2.status == "success"
    assert target.read_text(encoding="utf-8") == "v1"
    assert [e["type"] for e in second] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
    ]
    assert second[1]["payload"]["reason_code"] == "session_rule_allow"


def test_tool_executor_hard_boundary_denies_out_of_root_write() -> None:
    emitted: list[dict] = []
    out_path = Path("/tmp/ccr_outside_write.txt")
    if out_path.exists():
        out_path.unlink()

    executor = ToolExecutor(
        registry=ToolRegistry(),
        permission_engine=PermissionEngine(cwd="/tmp/ccr_ws"),
        emit=lambda event_type, **kwargs: emitted.append({"type": event_type, **kwargs}),
        cwd="/tmp/ccr_ws",
    )

    outcome = executor.execute(
        intent=ToolIntent(
            tool_call_id="TC1",
            tool_name="Write",
            tool_input={"path": str(out_path), "content": "x"},
        ),
        mode="ask",
        interactive_available=True,
        turn_index=1,
        resolve_permission=lambda _tcid: "allow_once",
    )
    assert outcome.status == "denied"
    assert not out_path.exists()
    assert [e["type"] for e in emitted] == [
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
    ]
    assert emitted[1]["payload"]["reason_code"] == "hard_boundary_path_outside_root"


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


def test_runtime_ask_mode_stream_allow_session_replays_in_same_session(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider(
            [
                {"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}},
                {"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}},
                {"emit": "assistant_message", "content": "OK"},
            ]
        ),
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
                    json.dumps({"type": "user_message", "content": "read twice"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "allow_session"}),
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
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
        "assistant_message",
        "session_completed",
    ]
    decided = [r for r in records if r["type"] == "tool_permission_decided"]
    assert decided[0]["payload"]["decision"] == "allow"
    assert decided[1]["payload"]["decision"] == "allow"
    assert decided[1]["payload"]["reason_code"] == "session_rule_allow"


def test_runtime_allow_session_replays_across_runs_with_same_session_id(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider(
            [{"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}}, {"emit": "assistant_message", "content": "OK"}]
        ),
    )

    with open("/tmp/ccr_ws/a.txt", "w", encoding="utf-8") as f:
        f.write("alpha\n")

    code1 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_REPLAY",
        ],
        stdin=io.StringIO(
            "\n".join(
                [
                    json.dumps({"type": "user_message", "content": "read once"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "allow_session"}),
                ]
            )
            + "\n"
        ),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code1 == 0

    code2 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_REPLAY",
        ],
        stdin=io.StringIO(json.dumps({"type": "user_message", "content": "read again"}) + "\n"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code2 == 0

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S_REPLAY")
    run2 = [r for r in records if r["run_id"] == "R2"]
    assert [r["type"] for r in run2] == [
        "session_start",
        "user_message",
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
        "assistant_message",
        "session_completed",
    ]
    decided = [r for r in run2 if r["type"] == "tool_permission_decided"]
    assert len(decided) == 1
    assert decided[0]["payload"]["decision"] == "allow"
    assert decided[0]["payload"]["reason_code"] == "session_rule_allow"


def test_runtime_allow_session_does_not_leak_across_different_session_ids(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider(
            [{"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}}, {"emit": "assistant_message", "content": "OK"}]
        ),
    )

    with open("/tmp/ccr_ws/a.txt", "w", encoding="utf-8") as f:
        f.write("alpha\n")

    code1 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_ALLOW",
        ],
        stdin=io.StringIO(
            "\n".join(
                [
                    json.dumps({"type": "user_message", "content": "seed allow"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "allow_session"}),
                ]
            )
            + "\n"
        ),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code1 == 0

    code2 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_OTHER",
        ],
        stdin=io.StringIO(json.dumps({"type": "user_message", "content": "no decision"}) + "\n"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code2 == 6

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S_OTHER")
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
    decided = [r for r in records if r["type"] == "tool_permission_decided"]
    assert len(decided) == 1
    assert decided[0]["payload"]["decision"] == "deny"
    assert decided[0]["payload"]["reason_code"] == "ask_unavailable"


def test_runtime_allow_persistent_replays_across_different_session_ids(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider(
            [{"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}}, {"emit": "assistant_message", "content": "OK"}]
        ),
    )

    with open("/tmp/ccr_ws/a.txt", "w", encoding="utf-8") as f:
        f.write("alpha\n")

    code1 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_PERSIST_A",
        ],
        stdin=io.StringIO(
            "\n".join(
                [
                    json.dumps({"type": "user_message", "content": "seed persistent allow"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "allow_persistent"}),
                ]
            )
            + "\n"
        ),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code1 == 0

    code2 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_PERSIST_B",
        ],
        stdin=io.StringIO(json.dumps({"type": "user_message", "content": "read"}) + "\n"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code2 == 0

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S_PERSIST_B")
    assert [r["type"] for r in records] == [
        "session_start",
        "user_message",
        "tool_call_requested",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
        "assistant_message",
        "session_completed",
    ]
    decided = [r for r in records if r["type"] == "tool_permission_decided"]
    assert len(decided) == 1
    assert decided[0]["payload"]["decision"] == "allow"
    assert decided[0]["payload"]["reason_code"] == "persistent_rule_allow"


def test_runtime_deny_persistent_replays_across_different_session_ids(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "PROVIDER_FACTORY",
        lambda _cfg: ScriptedProvider([{"emit_tool": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}}}]),
    )

    with open("/tmp/ccr_ws/a.txt", "w", encoding="utf-8") as f:
        f.write("alpha\n")

    code1 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_PERSIST_DENY_A",
        ],
        stdin=io.StringIO(
            "\n".join(
                [
                    json.dumps({"type": "user_message", "content": "seed persistent deny"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "deny_persistent"}),
                ]
            )
            + "\n"
        ),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code1 == 5

    code2 = run_cli(
        argv=[
            "-p",
            "--permission-mode",
            "ask",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
            "--session-id",
            "S_PERSIST_DENY_B",
        ],
        stdin=io.StringIO(json.dumps({"type": "user_message", "content": "read"}) + "\n"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code2 == 5

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S_PERSIST_DENY_B")
    assert [r["type"] for r in records] == [
        "session_start",
        "user_message",
        "tool_call_requested",
        "tool_permission_decided",
        "tool_result",
        "tool_execution_finished",
        "session_failed",
    ]
    decided = [r for r in records if r["type"] == "tool_permission_decided"]
    assert len(decided) == 1
    assert decided[0]["payload"]["decision"] == "deny"
    assert decided[0]["payload"]["reason_code"] == "persistent_rule_deny"


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
