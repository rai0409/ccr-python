from __future__ import annotations

from pathlib import Path

from ccr.util.jsonl import read_jsonl


def read_session_records(transcript_dir: str, session_id: str) -> list[dict]:
    return read_jsonl(Path(transcript_dir) / f"{session_id}.jsonl")


def assert_record_identity(records: list[dict]) -> None:
    for rec in records:
        assert rec["record_id"] == rec["event_id"]


def assert_parent_chain(records: list[dict]) -> None:
    prev = None
    for i, rec in enumerate(records):
        if i == 0:
            assert rec.get("parent_id") is None
            assert rec.get("parent_event_id") is None
        else:
            assert rec.get("parent_id") == prev
            assert rec.get("parent_event_id") == prev
        prev = rec["record_id"]
