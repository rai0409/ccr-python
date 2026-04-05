from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolExecutionContext:
    cwd: str


class BaseTool(ABC):
    name: str
    is_read_only: bool = True

    @abstractmethod
    def execute(self, tool_input: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
        raise NotImplementedError
