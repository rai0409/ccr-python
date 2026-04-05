from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, validate


def _load_schema(name: str) -> dict:
    p = Path(__file__).resolve().parents[2] / "src" / "ccr" / "contracts" / name
    return json.loads(p.read_text(encoding="utf-8"))


def test_events_schema_valid() -> None:
    schema = _load_schema("events.schema.json")
    Draft202012Validator.check_schema(schema)
    validate(
        {
            "event_id": "E1",
            "session_id": "S1",
            "run_id": "R1",
            "seq": 1,
            "ts": "2026-01-01T00:00:00.000000Z",
            "type": "session_start",
            "turn_index": 0,
            "payload": {"cwd": "/tmp/ccr_ws", "permission_mode": "ask", "model": "test-model"},
            "parent_event_id": None,
        },
        schema,
    )
