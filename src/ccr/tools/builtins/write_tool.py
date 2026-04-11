from __future__ import annotations

from pathlib import Path
from typing import Any

from ccr.tools.base import BaseTool, ToolExecutionContext


class WriteTool(BaseTool):
    name = "Write"
    is_read_only = False

    def execute(self, tool_input: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
        path = Path(str(tool_input["path"]))
        if not path.is_absolute():
            path = Path(context.cwd) / path
        content = str(tool_input["content"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {
            "status": "success",
            "path": str(path.resolve()),
            "bytes_written": len(content.encode("utf-8")),
        }
