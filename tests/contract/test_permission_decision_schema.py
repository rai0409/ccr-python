from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, validate


def _load_schema(name: str) -> dict:
    p = Path(__file__).resolve().parents[2] / "src" / "ccr" / "contracts" / name
    return json.loads(p.read_text(encoding="utf-8"))


def test_permission_decision_schema_valid() -> None:
    schema = _load_schema("permission_decision.schema.json")
    Draft202012Validator.check_schema(schema)
    validate(
        {
            "mode": "auto",
            "decision": "allow",
            "reason_code": "auto_safe",
            "precedence_rank": 7,
            "decision_source": "auto_label",
            "risk_label": "safe_read",
            "request_hash": "sha256:abc",
        },
        schema,
    )
