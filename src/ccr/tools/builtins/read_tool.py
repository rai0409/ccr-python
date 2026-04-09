from __future__ import annotations

from pathlib import Path
from typing import Any

from ccr.tools.base import BaseTool, ToolExecutionContext


MAX_BYTES = 262144
MAX_LINES = 5000


class ReadTool(BaseTool):
    name = "Read"

    def execute(self, tool_input: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
        path = Path(str(tool_input["path"]))
        if not path.is_absolute():
            path = Path(context.cwd) / path
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        total_bytes = len(data)
        total_lines = len(text.splitlines())

        bytes_returned = min(total_bytes, MAX_BYTES)
        lines_returned = min(total_lines, MAX_LINES)
        truncated = total_bytes > MAX_BYTES or total_lines > MAX_LINES

        content = data[:bytes_returned].decode("utf-8", errors="replace")
        content_lines = content.splitlines()[:lines_returned]
        content = "\n".join(content_lines)
        if content_lines and text.endswith("\n"):
            content += "\n"

        return {
            "status": "success",
            "content": content,
            "truncation": {
                "bytes_returned": bytes_returned,
                "lines_returned": lines_returned,
                "truncated": truncated,
            },
        }
