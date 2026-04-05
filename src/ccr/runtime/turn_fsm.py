from __future__ import annotations

from enum import StrEnum


class TurnState(StrEnum):
    INIT = "init"
    STARTED = "started"
    USER = "user"
    STREAMING = "streaming"
    TOOL_REQUESTED = "tool_requested"
    TOOL_DECIDED = "tool_decided"
    TOOL_RUNNING = "tool_running"
    TOOL_RESULT = "tool_result"
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
        elif self.state in {TurnState.USER, TurnState.STREAMING, TurnState.TOOL_RESULT} and event_type == "assistant_delta":
            self.state = TurnState.STREAMING
        elif self.state in {TurnState.USER, TurnState.STREAMING, TurnState.TOOL_RESULT} and event_type == "assistant_message":
            self.state = TurnState.STREAMING
        elif self.state in {TurnState.USER, TurnState.STREAMING, TurnState.TOOL_RESULT} and event_type == "tool_call_requested":
            self.state = TurnState.TOOL_REQUESTED
        elif self.state == TurnState.TOOL_REQUESTED and event_type == "tool_permission_decided":
            self.state = TurnState.TOOL_DECIDED
        elif self.state == TurnState.TOOL_DECIDED and event_type in {"tool_execution_started", "tool_result"}:
            self.state = TurnState.TOOL_RUNNING if event_type == "tool_execution_started" else TurnState.TOOL_RESULT
        elif self.state == TurnState.TOOL_RUNNING and event_type == "tool_result":
            self.state = TurnState.TOOL_RESULT
        elif self.state == TurnState.TOOL_RESULT and event_type == "tool_execution_finished":
            self.state = TurnState.TOOL_RESULT
        elif event_type == "session_completed":
            self.state = TurnState.DONE
        elif event_type == "session_failed":
            self.state = TurnState.FAILED
        else:
            raise RuntimeError(f"illegal transition from {self.state} via {event_type}")
        return self.state
