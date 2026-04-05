from __future__ import annotations

from pathlib import Path

from ccr.tools.base import BaseTool, ToolExecutionContext


class GrepTool(BaseTool):
    name = "Grep"

    def execute(self, tool_input: dict, context: ToolExecutionContext) -> dict:
        pattern = str(tool_input["pattern"])
        root = Path(str(tool_input["path"]))
        if not root.is_absolute():
            root = Path(context.cwd) / root

        matches_order: list[list] = []
        files = sorted([p for p in root.rglob("*") if p.is_file()], key=lambda p: str(p.resolve()))
        for f in files:
            content = f.read_text(encoding="utf-8", errors="replace")
            for line_idx, line in enumerate(content.splitlines(), start=1):
                col = line.find(pattern)
                if col >= 0:
                    matches_order.append([str(f.resolve()), line_idx, col + 1])
        return {"status": "success", "matches_order": matches_order}
