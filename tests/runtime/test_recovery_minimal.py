from __future__ import annotations

import pytest

from ccr.runtime.recovery import classify_tool_call_recovery


def test_recovery_completed_when_finished_exists() -> None:
    records = [
        {"type": "tool_call_requested", "tool_call_id": "TC1"},
        {"type": "tool_execution_started", "tool_call_id": "TC1"},
        {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "success"}},
    ]
    result = classify_tool_call_recovery(records, "TC1")
    assert result.state == "completed"


def test_recovery_denied_on_deny_terminal_path() -> None:
    records = [
        {"type": "tool_call_requested", "tool_call_id": "TC1"},
        {"type": "tool_permission_decided", "tool_call_id": "TC1", "payload": {"decision": "deny"}},
        {"type": "tool_result", "tool_call_id": "TC1", "payload": {"result": {"status": "denied"}}},
        {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "denied"}},
    ]
    result = classify_tool_call_recovery(records, "TC1")
    assert result.state == "denied"


def test_recovery_interrupted_when_started_without_finished() -> None:
    records = [
        {"type": "tool_call_requested", "tool_call_id": "TC1"},
        {"type": "tool_execution_started", "tool_call_id": "TC1"},
    ]
    result = classify_tool_call_recovery(records, "TC1")
    assert result.state == "interrupted"


def test_recovery_not_found_for_unknown_tool_call_id() -> None:
    records = [{"type": "tool_call_requested", "tool_call_id": "TC1"}]
    result = classify_tool_call_recovery(records, "TC2")
    assert result.state == "not_found"


def test_recovery_isolates_multiple_tool_calls() -> None:
    records = [
        {"type": "tool_call_requested", "tool_call_id": "TC1"},
        {"type": "tool_execution_started", "tool_call_id": "TC1"},
        {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "success"}},
        {"type": "tool_call_requested", "tool_call_id": "TC2"},
        {"type": "tool_execution_started", "tool_call_id": "TC2"},
    ]
    assert classify_tool_call_recovery(records, "TC1").state == "completed"
    assert classify_tool_call_recovery(records, "TC2").state == "interrupted"


def test_recovery_terminal_finished_wins_over_partial_started() -> None:
    records = [
        {"type": "tool_call_requested", "tool_call_id": "TC1"},
        {"type": "tool_execution_started", "tool_call_id": "TC1"},
        {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "error"}},
    ]
    result = classify_tool_call_recovery(records, "TC1")
    assert result.state == "completed"


def test_recovery_pre_start_partial_records_are_not_interrupted() -> None:
    records = [
        {"type": "tool_call_requested", "tool_call_id": "TC1"},
        {"type": "tool_permission_decided", "tool_call_id": "TC1", "payload": {"decision": "allow"}},
    ]
    with pytest.raises(ValueError, match="unclassifiable pre-start partial records"):
        classify_tool_call_recovery(records, "TC1")
