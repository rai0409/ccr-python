from __future__ import annotations

from ccr.policy.engine import PermissionEngine


def test_permission_auto_safe_allow() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Read",
        tool_input={"path": "/tmp/ccr_ws/a.txt"},
        mode="auto",
        interactive_available=False,
    )
    assert d.decision == "allow"
    assert d.reason_code == "auto_safe"
    assert d.precedence_rank == 7
    assert d.risk_label == "safe_read"


def test_permission_hard_boundary_deny() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Write",
        tool_input={"path": "/etc/hosts", "content": "x"},
        mode="auto",
        interactive_available=False,
    )
    assert d.decision == "deny"
    assert d.reason_code == "hard_boundary_path_outside_root"
    assert d.precedence_rank == 1


def test_permission_ask_unavailable_fallback() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Write",
        tool_input={"path": "/tmp/ccr_ws/a.txt", "content": "x"},
        mode="auto",
        interactive_available=False,
    )
    assert d.decision == "deny"
    assert d.reason_code == "ask_unavailable"
    assert d.precedence_rank == 9


def test_permission_ask_mode_denies_with_ask_unavailable() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Read",
        tool_input={"path": "/tmp/ccr_ws/a.txt"},
        mode="ask",
        interactive_available=True,
    )
    assert d.decision == "deny"
    assert d.reason_code == "ask_unavailable"
    assert d.precedence_rank == 6


def test_permission_bypass_mode_safe_read_is_auto_safe() -> None:
    engine = PermissionEngine(cwd="/tmp/ccr_ws")
    d = engine.decide(
        tool_name="Read",
        tool_input={"path": "/tmp/ccr_ws/a.txt"},
        mode="bypass",
        interactive_available=False,
    )
    assert d.decision == "allow"
    assert d.reason_code == "auto_safe"
    assert d.precedence_rank == 7
