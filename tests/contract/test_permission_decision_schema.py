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


def test_permission_decision_schema_ask_valid() -> None:
    schema = _load_schema("permission_decision.schema.json")
    validate(
        {
            "mode": "ask",
            "decision": "ask",
            "reason_code": "mode_ask",
            "precedence_rank": 5,
            "decision_source": "mode",
            "risk_label": "dangerous_exec",
            "request_hash": "sha256:def",
        },
        schema,
    )


def test_permission_decision_schema_session_rule_valid() -> None:
    schema = _load_schema("permission_decision.schema.json")
    validate(
        {
            "mode": "ask",
            "decision": "allow",
            "reason_code": "session_rule_allow",
            "precedence_rank": 3,
            "decision_source": "session_rule",
            "risk_label": "safe_read",
            "request_hash": "sha256:xyz",
        },
        schema,
    )


def test_permission_decision_schema_persistent_rule_valid() -> None:
    schema = _load_schema("permission_decision.schema.json")
    validate(
        {
            "mode": "ask",
            "decision": "deny",
            "reason_code": "persistent_rule_deny",
            "precedence_rank": 2,
            "decision_source": "persistent_rule",
            "risk_label": "safe_read",
            "request_hash": "sha256:persist",
        },
        schema,
    )
