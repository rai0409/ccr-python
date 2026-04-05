from __future__ import annotations

import pytest

from ccr.runtime.turn_fsm import TurnState, TurnStateMachine


def test_turn_fsm_happy_path() -> None:
    fsm = TurnStateMachine()
    assert fsm.transition("session_start") == TurnState.STARTED
    assert fsm.transition("user_message") == TurnState.USER
    assert fsm.transition("assistant_delta") == TurnState.STREAMING
    assert fsm.transition("assistant_message") == TurnState.STREAMING
    assert fsm.transition("session_completed") == TurnState.DONE


def test_turn_fsm_invalid_transition() -> None:
    fsm = TurnStateMachine()
    with pytest.raises(RuntimeError):
        fsm.transition("assistant_message")
