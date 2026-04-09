from __future__ import annotations

import pytest

from ccr.policy.engine import PermissionEngine

pytestmark = pytest.mark.skip(reason="Phase 2B behavior is out of active Phase 2A scope")


def test_permission_ask_mode_interactive_requires_user() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Bash",
        tool_input={"command": "git status"},
        mode="ask",
        interactive_available=True,
    )
    assert d.decision == "ask"
    assert d.reason_code == "mode_ask"
    assert d.precedence_rank == 5
    assert d.risk_label == "dangerous_exec"


def test_permission_auto_mode_interactive_requires_user() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Bash",
        tool_input={"command": "git status"},
        mode="auto",
        interactive_available=True,
    )
    assert d.decision == "ask"
    assert d.reason_code == "auto_requires_user"
    assert d.precedence_rank == 8
    assert d.risk_label == "dangerous_exec"


def test_permission_ask_mode_noninteractive_denies() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Bash",
        tool_input={"command": "git status"},
        mode="ask",
        interactive_available=False,
    )
    assert d.decision == "deny"
    assert d.reason_code == "ask_unavailable"
    assert d.precedence_rank == 6


def test_permission_auto_mode_noninteractive_dangerous_denies() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Bash",
        tool_input={"command": "git status"},
        mode="auto",
        interactive_available=False,
    )
    assert d.decision == "deny"
    assert d.reason_code == "ask_unavailable"
    assert d.precedence_rank == 9
