from __future__ import annotations

from enum import StrEnum


class InputMode(StrEnum):
    TEXT = "text"
    STREAM_JSON = "stream-json"


class OutputMode(StrEnum):
    TEXT = "text"
    JSON = "json"
    STREAM_JSON = "stream-json"
