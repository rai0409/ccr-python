from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


TERMINAL_EVENT_TYPES = {"session_completed", "session_failed"}
STREAM_ONLY_EVENT_TYPES = {"assistant_delta"}


@dataclass
class EventEnvelope:
    event_id: str
    session_id: str
    run_id: str
    seq: int
    ts: str
    type: str
    turn_index: int
    payload: dict[str, Any] = field(default_factory=dict)
    parent_event_id: str | None = None
    message_id: str | None = None
    tool_call_id: str | None = None
    model: str | None = None
    provider: str | None = None
    meta: dict[str, Any] | None = None

    @property
    def persisted(self) -> bool:
        return self.type not in STREAM_ONLY_EVENT_TYPES

    @property
    def terminal(self) -> bool:
        return self.type in TERMINAL_EVENT_TYPES

    def to_stream_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "seq": self.seq,
            "ts": self.ts,
            "type": self.type,
            "turn_index": self.turn_index,
            "payload": self.payload,
        }
        if self.parent_event_id is not None:
            data["parent_event_id"] = self.parent_event_id
        if self.message_id is not None:
            data["message_id"] = self.message_id
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        if self.model is not None:
            data["model"] = self.model
        if self.provider is not None:
            data["provider"] = self.provider
        if self.meta is not None:
            data["meta"] = self.meta
        return data
