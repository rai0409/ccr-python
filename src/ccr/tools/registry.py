from __future__ import annotations

from ccr.tools.base import BaseTool
from ccr.tools.builtins.glob_tool import GlobTool
from ccr.tools.builtins.grep_tool import GrepTool
from ccr.tools.builtins.ls_tool import LSTool
from ccr.tools.builtins.read_tool import ReadTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {
            "Read": ReadTool(),
            "LS": LSTool(),
            "Glob": GlobTool(),
            "Grep": GrepTool(),
        }

    def get(self, tool_name: str) -> BaseTool | None:
        return self._tools.get(tool_name)
