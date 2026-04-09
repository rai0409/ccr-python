from __future__ import annotations

from pathlib import Path

from ccr.tools.base import BaseTool, ToolExecutionContext


class LSTool(BaseTool):
    name = "LS"

    def execute(self, tool_input: dict, context: ToolExecutionContext) -> dict:
        path = Path(str(tool_input["path"]))
        if not path.is_absolute():
            path = Path(context.cwd) / path
        entries = sorted(p.name for p in path.iterdir())
        return {"status": "success", "entries": entries}
