from __future__ import annotations

import io
from pathlib import Path

from ccr.cli import main
from ccr.cli.main import run_cli
from ccr.storage.session_index import SessionIndex
from ccr.util.jsonl import append_jsonl, read_jsonl
from helpers.fake_provider import ScriptedProvider


def test_run_scoped_terminality_continue(monkeypatch) -> None:
    # Pre-state: completed run R1
    append_jsonl(
        Path("/tmp/ccr_sessions/S1.jsonl"),
        {
            "schema_version": "1.0",
            "record_id": "E1",
            "event_id": "E1",
            "session_id": "S1",
            "run_id": "R1",
            "seq": 1,
            "ts": "2026-01-01T00:00:00.000000Z",
            "type": "session_start",
            "turn_index": 0,
            "parent_id": None,
            "parent_event_id": None,
            "payload": {"cwd": "/tmp/ccr_ws", "permission_mode": "ask", "model": "test-model"},
        },
    )
    append_jsonl(
        Path("/tmp/ccr_sessions/S1.jsonl"),
        {
            "schema_version": "1.0",
            "record_id": "E2",
            "event_id": "E2",
            "session_id": "S1",
            "run_id": "R1",
            "seq": 2,
            "ts": "2026-01-01T00:00:00.001000Z",
            "type": "user_message",
            "turn_index": 1,
            "parent_id": "E1",
            "parent_event_id": "E1",
            "payload": {"content": "old"},
        },
    )
    append_jsonl(
        Path("/tmp/ccr_sessions/S1.jsonl"),
        {
            "schema_version": "1.0",
            "record_id": "E3",
            "event_id": "E3",
            "session_id": "S1",
            "run_id": "R1",
            "seq": 3,
            "ts": "2026-01-01T00:00:00.002000Z",
            "type": "assistant_message",
            "turn_index": 1,
            "parent_id": "E2",
            "parent_event_id": "E2",
            "payload": {"content": "old"},
        },
    )
    append_jsonl(
        Path("/tmp/ccr_sessions/S1.jsonl"),
        {
            "schema_version": "1.0",
            "record_id": "E4",
            "event_id": "E4",
            "session_id": "S1",
            "run_id": "R1",
            "seq": 4,
            "ts": "2026-01-01T00:00:00.003000Z",
            "type": "session_completed",
            "turn_index": 1,
            "parent_id": "E3",
            "parent_event_id": "E3",
            "payload": {"status": "completed"},
        },
    )
    SessionIndex("/tmp/ccr_sessions").update(session_id="S1", cwd="/tmp/ccr_ws", ts="2026-01-01T00:00:00.003000Z")

    monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg: ScriptedProvider([{"emit": "assistant_message", "content": "R2 OK"}]))

    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=["--continue", "-p", "next", "--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"],
        stdin=io.StringIO(""),
        stdout=out,
        stderr=err,
    )
    assert code == 0
    assert out.getvalue() == "R2 OK\n"

    recs = read_jsonl(Path("/tmp/ccr_sessions/S1.jsonl"))
    r1_terms = [r for r in recs if r["run_id"] == "R1" and r["type"] in {"session_completed", "session_failed"}]
    r2_terms = [r for r in recs if r["run_id"] == "R2" and r["type"] in {"session_completed", "session_failed"}]
    assert len(r1_terms) == 1
    assert len(r2_terms) == 1
