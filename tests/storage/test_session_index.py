from __future__ import annotations

from ccr.storage.session_index import SessionIndex


def test_session_index_latest_for_cwd() -> None:
    idx = SessionIndex("/tmp/ccr_sessions")
    idx.update(session_id="S1", cwd="/tmp/ccr_ws", ts="2026-01-01T00:00:00.000000Z")
    idx.update(session_id="S2", cwd="/tmp/ccr_ws", ts="2026-01-01T00:00:00.001000Z")
    assert idx.get_latest_for_cwd("/tmp/ccr_ws") == "S2"
