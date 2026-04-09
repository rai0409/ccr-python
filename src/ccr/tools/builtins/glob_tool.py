from __future__ import annotations

from pathlib import Path

from ccr.tools.base import BaseTool, ToolExecutionContext


class GlobTool(BaseTool):
    name = "Glob"

    def execute(self, tool_input: dict, context: ToolExecutionContext) -> dict:
        pattern = str(tool_input["pattern"])
        base = Path(str(tool_input.get("base_path", context.cwd)))
        if not base.is_absolute():
            base = Path(context.cwd) / base
        matches = sorted(str(p.resolve()) for p in base.glob(pattern))
        return {"status": "success", "matches": matches}
