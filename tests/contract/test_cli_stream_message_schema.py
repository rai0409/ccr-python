from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError, validate


def _load_schema(name: str) -> dict:
    p = Path(__file__).resolve().parents[2] / "src" / "ccr" / "contracts" / name
    return json.loads(p.read_text(encoding="utf-8"))


def test_cli_stream_schema_valid_variants() -> None:
    schema = _load_schema("cli_stream_message.schema.json")
    Draft202012Validator.check_schema(schema)
    validate({"type": "user_message", "content": "hello"}, schema)
    validate({"type": "permission_decision", "tool_call_id": "TC1", "decision": "allow_once"}, schema)
    validate({"type": "interrupt"}, schema)


def test_cli_stream_schema_rejects_unknown_type() -> None:
    schema = _load_schema("cli_stream_message.schema.json")
    with pytest.raises(ValidationError):
        validate({"type": "bad_type", "x": 1}, schema)
