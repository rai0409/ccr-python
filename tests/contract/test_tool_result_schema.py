from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, validate


def _load_schema(name: str) -> dict:
    p = Path(__file__).resolve().parents[2] / "src" / "ccr" / "contracts" / name
    return json.loads(p.read_text(encoding="utf-8"))


def test_tool_result_schema_valid() -> None:
    schema = _load_schema("tool_result.schema.json")
    Draft202012Validator.check_schema(schema)
    validate(
        {
            "status": "success",
            "truncation": {"bytes_returned": 262144, "lines_returned": 5000, "truncated": True},
        },
        schema,
    )


def test_tool_result_schema_denied_valid() -> None:
    schema = _load_schema("tool_result.schema.json")
    validate({"status": "denied"}, schema)
