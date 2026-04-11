from __future__ import annotations

from ccr.tools.base import BaseTool
from ccr.tools.builtins.bash_tool import BashTool
from ccr.tools.builtins.edit_tool import EditTool
from ccr.tools.builtins.glob_tool import GlobTool
from ccr.tools.builtins.grep_tool import GrepTool
from ccr.tools.builtins.ls_tool import LSTool
from ccr.tools.builtins.read_tool import ReadTool
from ccr.tools.builtins.write_tool import WriteTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {
            "Read": ReadTool(),
            "LS": LSTool(),
            "Glob": GlobTool(),
            "Grep": GrepTool(),
            "Write": WriteTool(),
            "Edit": EditTool(),
            "Bash": BashTool(),
        }

    def get(self, tool_name: str) -> BaseTool | None:
        return self._tools.get(tool_name)
