from __future__ import annotations

from collections import deque
from threading import Lock


_lock = Lock()
_session_ids: deque[str] | None = None
_run_ids: deque[str] | None = None
_event_template = "E{n}"
_event_counter = 1
_session_counter = 1
_run_counter = 1


def configure_deterministic_ids(
    *,
    session_ids: list[str] | None = None,
    run_ids: list[str] | None = None,
    event_template: str = "E{n}",
    event_start: int = 1,
) -> None:
    global _session_ids, _run_ids, _event_template, _event_counter, _session_counter, _run_counter
    with _lock:
        _session_ids = deque(session_ids or [])
        _run_ids = deque(run_ids or [])
        _event_template = event_template
        _event_counter = event_start
        _session_counter = 1
        _run_counter = 1


def reset_ids() -> None:
    configure_deterministic_ids(session_ids=None, run_ids=None, event_template="E{n}", event_start=1)


def new_session_id() -> str:
    global _session_counter
    with _lock:
        if _session_ids is not None and len(_session_ids) > 0:
            return _session_ids.popleft()
        sid = f"S{_session_counter}"
        _session_counter += 1
        return sid


def new_run_id() -> str:
    global _run_counter
    with _lock:
        if _run_ids is not None and len(_run_ids) > 0:
            return _run_ids.popleft()
        rid = f"R{_run_counter}"
        _run_counter += 1
        return rid


def new_event_id() -> str:
    global _event_counter
    with _lock:
        eid = _event_template.format(n=_event_counter)
        _event_counter += 1
        return eid
