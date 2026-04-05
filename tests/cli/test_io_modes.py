from __future__ import annotations

from ccr.cli.io_modes import InputMode, OutputMode


def test_io_modes_literals() -> None:
    assert InputMode.TEXT.value == "text"
    assert InputMode.STREAM_JSON.value == "stream-json"
    assert OutputMode.TEXT.value == "text"
    assert OutputMode.JSON.value == "json"
    assert OutputMode.STREAM_JSON.value == "stream-json"
