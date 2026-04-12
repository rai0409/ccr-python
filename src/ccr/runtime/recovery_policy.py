from __future__ import annotations

from typing import Literal

from ccr.runtime.recovery import ToolCallRecovery


RecoveryAction = Literal["noop", "error", "eligible_for_retry", "manual_review_required"]

_RETRY_ELIGIBLE_TOOLS = frozenset({"Read", "LS", "Glob", "Grep"})
_MANUAL_REVIEW_TOOLS = frozenset({"Write", "Edit", "Bash"})


def decide_recovery_action(recovery: ToolCallRecovery, tool_name: str) -> RecoveryAction:
    if recovery.state in {"completed", "denied"}:
        return "noop"

    if recovery.state == "not_found":
        return "error"

    if recovery.state != "interrupted":
        return "error"

    if tool_name in _RETRY_ELIGIBLE_TOOLS:
        return "eligible_for_retry"

    if tool_name in _MANUAL_REVIEW_TOOLS:
        return "manual_review_required"

    return "error"
