from __future__ import annotations

from enum import StrEnum


class TurnState(StrEnum):
    INIT = "init"
    STARTED = "started"
    USER = "user"
    STREAMING = "streaming"
    DONE = "done"
    FAILED = "failed"


class TurnStateMachine:
    def __init__(self) -> None:
        self.state = TurnState.INIT

    def transition(self, event_type: str) -> TurnState:
        if self.state == TurnState.INIT and event_type in {"session_start", "session_resumed"}:
            self.state = TurnState.STARTED
        elif self.state == TurnState.STARTED and event_type == "user_message":
            self.state = TurnState.USER
        elif self.state in {TurnState.USER, TurnState.STREAMING} and event_type == "assistant_delta":
            self.state = TurnState.STREAMING
        elif self.state in {TurnState.USER, TurnState.STREAMING} and event_type == "assistant_message":
            self.state = TurnState.STREAMING
        elif event_type == "session_completed":
            self.state = TurnState.DONE
        elif event_type == "session_failed":
            self.state = TurnState.FAILED
        else:
            raise RuntimeError(f"illegal transition from {self.state} via {event_type}")
        return self.state
