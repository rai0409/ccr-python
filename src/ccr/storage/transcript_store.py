from __future__ import annotations

from pathlib import Path
from typing import Any

from ccr.runtime.events import EventEnvelope
from ccr.util import jsonl

from .lockfile import session_lock
from .schema_version import ensure_supported_schema


class TranscriptStore:
    def __init__(self, transcript_dir: str, *, persistence_enabled: bool = True) -> None:
        self.transcript_dir = Path(transcript_dir)
        self.persistence_enabled = persistence_enabled

    def _session_path(self, session_id: str) -> Path:
        return self.transcript_dir / f"{session_id}.jsonl"

    def _lock_path(self, session_id: str) -> Path:
        return self.transcript_dir / f"{session_id}.lock"

    def load_records(self, session_id: str) -> list[dict[str, Any]]:
        records = jsonl.read_jsonl(self._session_path(session_id))
        for rec in records:
            ensure_supported_schema(str(rec.get("schema_version", "1.0")))
        return records

    def get_next_seq(self, session_id: str) -> int:
        records = self.load_records(session_id)
        if not records:
            return 1
        return int(records[-1]["seq"]) + 1

    def get_last_persisted_event_id(self, session_id: str) -> str | None:
        records = self.load_records(session_id)
        if not records:
            return None
        return str(records[-1]["record_id"])

    def append_event(self, event: EventEnvelope) -> dict[str, Any] | None:
        if not self.persistence_enabled or not event.persisted:
            return None
        record: dict[str, Any] = {
            "schema_version": "1.0",
            "record_id": event.event_id,
            "event_id": event.event_id,
            "session_id": event.session_id,
            "run_id": event.run_id,
            "seq": event.seq,
            "ts": event.ts,
            "type": event.type,
            "turn_index": event.turn_index,
            "payload": event.payload,
            "parent_id": event.parent_event_id,
            "parent_event_id": event.parent_event_id,
        }
        if event.message_id is not None:
            record["message_id"] = event.message_id
        if event.tool_call_id is not None:
            record["tool_call_id"] = event.tool_call_id
        if event.meta is not None and isinstance(event.meta.get("permission_meta"), dict):
            record["permission_meta"] = dict(event.meta["permission_meta"])

        with session_lock(self._lock_path(event.session_id)):
            jsonl.append_jsonl(self._session_path(event.session_id), record, fsync=True)
        return record
