from __future__ import annotations

from pathlib import Path

from ccr.util import jsonl


class SessionIndex:
    def __init__(self, transcript_dir: str) -> None:
        self._path = Path(transcript_dir) / "session_index.jsonl"

    def update(self, *, session_id: str, cwd: str, ts: str) -> None:
        jsonl.append_jsonl(self._path, {"session_id": session_id, "cwd": cwd, "ts": ts}, fsync=True)

    def get_latest_for_cwd(self, cwd: str) -> str | None:
        rows = jsonl.read_jsonl(self._path)
        latest: str | None = None
        latest_ts: str | None = None
        for row in rows:
            if row.get("cwd") != cwd:
                continue
            ts = str(row.get("ts"))
            if latest_ts is None or ts >= latest_ts:
                latest_ts = ts
                latest = str(row.get("session_id"))
        return latest
