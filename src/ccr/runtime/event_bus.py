from __future__ import annotations

from collections.abc import Callable

from .events import EventEnvelope


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[EventEnvelope], None]] = []

    def subscribe(self, fn: Callable[[EventEnvelope], None]) -> None:
        self._subscribers.append(fn)

    def emit(self, event: EventEnvelope) -> None:
        for fn in self._subscribers:
            fn(event)
