from __future__ import annotations

import io
from pathlib import Path

from ccr.cli import main
from ccr.cli.main import run_cli
from ccr.storage.transcript_store import TranscriptStore
from helpers.fake_provider import ScriptedProvider


def test_event_ordering_and_stream_only_delta(monkeypatch) -> None:
    monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg: ScriptedProvider([{"emit": "assistant_message", "content": "OK"}]))

    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=["-p", "hello", "--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"],
        stdin=io.StringIO(""),
        stdout=out,
        stderr=err,
    )
    assert code == 0
    assert out.getvalue() == "OK\n"

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S1")
    assert [r["seq"] for r in records] == [1, 2, 4, 5]
    assert [r["type"] for r in records] == ["session_start", "user_message", "assistant_message", "session_completed"]
    assert records[0]["parent_id"] is None
    assert records[1]["parent_id"] == "E1"
    assert records[2]["parent_id"] == "E2"
    assert records[3]["parent_id"] == "E4"
    for rec in records:
        assert rec["record_id"] == rec["event_id"]
        assert rec["parent_id"] == rec["parent_event_id"]
