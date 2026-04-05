from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ccr.util.ids import configure_deterministic_ids, reset_ids
from ccr.util.time import configure_frozen_clock, reset_clock


@pytest.fixture(autouse=True)
def deterministic_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ws = Path("/tmp/ccr_ws")
    tr = Path("/tmp/ccr_sessions")
    cfg = Path("/tmp/ccr_config")
    data = Path("/tmp/ccr_data")
    for p in (ws, tr, cfg, data):
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)

    configure_deterministic_ids(
        session_ids=["S1", "S2", "S3"],
        run_ids=["R1", "R2", "R3"],
        event_template="E{n}",
        event_start=1,
    )
    configure_frozen_clock("2026-01-01T00:00:00.000000Z", step_ms=1)

    yield {"cwd": str(ws), "transcript_dir": str(tr), "config_dir": str(cfg), "data_dir": str(data)}

    reset_ids()
    reset_clock()
