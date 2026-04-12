from __future__ import annotations

import pytest

from ccr.runtime.recovery import RecoveryState, ToolCallRecovery
from ccr.runtime.recovery_policy import RecoveryAction, decide_recovery_action


ACTION_MATRIX: list[tuple[RecoveryState, str, RecoveryAction]] = [
    ("completed", "Read", "noop"),
    ("denied", "Bash", "noop"),
    ("not_found", "Read", "error"),
    ("interrupted", "Read", "eligible_for_retry"),
    ("interrupted", "LS", "eligible_for_retry"),
    ("interrupted", "Glob", "eligible_for_retry"),
    ("interrupted", "Grep", "eligible_for_retry"),
    ("interrupted", "Write", "manual_review_required"),
    ("interrupted", "Edit", "manual_review_required"),
    ("interrupted", "Bash", "manual_review_required"),
]


@pytest.mark.parametrize(
    ("state", "tool_name", "expected_action"),
    ACTION_MATRIX,
)
def test_decide_recovery_action_matrix(
    state: RecoveryState,
    tool_name: str,
    expected_action: RecoveryAction,
) -> None:
    recovery = ToolCallRecovery(tool_call_id="TC1", state=state)
    assert decide_recovery_action(recovery, tool_name) == expected_action
