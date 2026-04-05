from __future__ import annotations

from ccr.runtime.events import EventEnvelope
from ccr.storage.transcript_store import TranscriptStore


def test_transcript_store_persists_only_persisted_events() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")

    e1 = EventEnvelope(
        event_id="E1",
        session_id="S1",
        run_id="R1",
        seq=1,
        ts="2026-01-01T00:00:00.000000Z",
        type="session_start",
        turn_index=0,
        payload={"cwd": "/tmp/ccr_ws", "permission_mode": "ask", "model": "test-model"},
        parent_event_id=None,
    )
    e2 = EventEnvelope(
        event_id="E2",
        session_id="S1",
        run_id="R1",
        seq=2,
        ts="2026-01-01T00:00:00.001000Z",
        type="assistant_delta",
        turn_index=1,
        payload={"delta": "x"},
        parent_event_id="E1",
    )
    e3 = EventEnvelope(
        event_id="E3",
        session_id="S1",
        run_id="R1",
        seq=3,
        ts="2026-01-01T00:00:00.002000Z",
        type="assistant_message",
        turn_index=1,
        payload={"content": "x"},
        parent_event_id="E1",
    )

    store.append_event(e1)
    store.append_event(e2)
    store.append_event(e3)

    recs = store.load_records("S1")
    assert [r["type"] for r in recs] == ["session_start", "assistant_message"]
    assert [r["seq"] for r in recs] == [1, 3]
    for rec in recs:
        assert rec["record_id"] == rec["event_id"]


def test_transcript_next_seq_from_existing() -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    assert store.get_next_seq("S1") >= 1
