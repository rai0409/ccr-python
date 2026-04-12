from __future__ import annotations

import pytest

from ccr.runtime.events import EventEnvelope
from ccr.runtime.recovery import classify_tool_call_recovery_from_transcript
from ccr.storage.transcript_store import TranscriptStore


def _append_events(
    store: TranscriptStore,
    *,
    session_id: str,
    events: list[dict[str, object]],
) -> None:
    for seq, event in enumerate(events, start=1):
        store.append_event(
            EventEnvelope(
                event_id=f"E{seq}",
                session_id=session_id,
                run_id="R1",
                seq=seq,
                ts=f"2026-01-01T00:00:00.{seq:06d}Z",
                type=str(event["type"]),
                turn_index=1,
                payload=dict(event.get("payload", {})),
                parent_event_id=f"E{seq - 1}" if seq > 1 else None,
                tool_call_id=str(event["tool_call_id"]) if "tool_call_id" in event else None,
            )
        )


def test_transcript_recovery_completed_when_finished_exists() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_events(
        store,
        session_id="S1",
        events=[
            {"type": "tool_call_requested", "tool_call_id": "TC1"},
            {"type": "tool_execution_started", "tool_call_id": "TC1"},
            {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "success"}},
        ],
    )

    result = classify_tool_call_recovery_from_transcript(store, "S1", "TC1")
    assert result.state == "completed"


def test_transcript_recovery_denied_on_terminal_deny_path() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_events(
        store,
        session_id="S1",
        events=[
            {"type": "tool_call_requested", "tool_call_id": "TC1"},
            {"type": "tool_permission_decided", "tool_call_id": "TC1", "payload": {"decision": "deny"}},
            {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "denied"}},
        ],
    )

    result = classify_tool_call_recovery_from_transcript(store, "S1", "TC1")
    assert result.state == "denied"


def test_transcript_recovery_interrupted_when_started_without_finished() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_events(
        store,
        session_id="S1",
        events=[
            {"type": "tool_call_requested", "tool_call_id": "TC1"},
            {"type": "tool_execution_started", "tool_call_id": "TC1"},
        ],
    )

    result = classify_tool_call_recovery_from_transcript(store, "S1", "TC1")
    assert result.state == "interrupted"


def test_transcript_recovery_not_found_for_unknown_tool_call_id() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_events(
        store,
        session_id="S1",
        events=[{"type": "tool_call_requested", "tool_call_id": "TC1"}],
    )

    result = classify_tool_call_recovery_from_transcript(store, "S1", "TC2")
    assert result.state == "not_found"


def test_transcript_recovery_isolates_multiple_tool_call_ids() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_events(
        store,
        session_id="S1",
        events=[
            {"type": "tool_call_requested", "tool_call_id": "TC1"},
            {"type": "tool_execution_started", "tool_call_id": "TC1"},
            {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "success"}},
            {"type": "tool_call_requested", "tool_call_id": "TC2"},
            {"type": "tool_execution_started", "tool_call_id": "TC2"},
        ],
    )

    assert classify_tool_call_recovery_from_transcript(store, "S1", "TC1").state == "completed"
    assert classify_tool_call_recovery_from_transcript(store, "S1", "TC2").state == "interrupted"


def test_transcript_recovery_pre_start_partial_records_raise_error() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_events(
        store,
        session_id="S1",
        events=[
            {"type": "tool_call_requested", "tool_call_id": "TC1"},
            {"type": "tool_permission_decided", "tool_call_id": "TC1", "payload": {"decision": "allow"}},
        ],
    )

    with pytest.raises(ValueError, match="unclassifiable pre-start partial records"):
        classify_tool_call_recovery_from_transcript(store, "S1", "TC1")


def test_transcript_recovery_finished_precedence_over_interrupted() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_events(
        store,
        session_id="S1",
        events=[
            {"type": "tool_call_requested", "tool_call_id": "TC1"},
            {"type": "tool_execution_started", "tool_call_id": "TC1"},
            {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "error"}},
            {"type": "tool_execution_started", "tool_call_id": "TC1"},
        ],
    )

    result = classify_tool_call_recovery_from_transcript(store, "S1", "TC1")
    assert result.state == "completed"
