from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock


_lock = Lock()
_frozen_start: datetime | None = None
_step_ms: int = 1
_tick: int = 0


def configure_frozen_clock(start_rfc3339: str, step_ms: int = 1) -> None:
    global _frozen_start, _step_ms, _tick
    start = datetime.fromisoformat(start_rfc3339.replace("Z", "+00:00")).astimezone(timezone.utc)
    with _lock:
        _frozen_start = start
        _step_ms = step_ms
        _tick = 0


def reset_clock() -> None:
    global _frozen_start, _step_ms, _tick
    with _lock:
        _frozen_start = None
        _step_ms = 1
        _tick = 0


def now_rfc3339() -> str:
    global _tick
    with _lock:
        if _frozen_start is None:
            dt = datetime.now(timezone.utc)
        else:
            dt = _frozen_start + timedelta(milliseconds=_tick * _step_ms)
            _tick += 1
    return dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
