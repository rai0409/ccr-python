from __future__ import annotations

from pathlib import Path
from typing import Any

from ccr.tools.base import BaseTool, ToolExecutionContext


class EditTool(BaseTool):
    name = "Edit"
    is_read_only = False

    def execute(self, tool_input: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
        path = Path(str(tool_input["path"]))
        if not path.is_absolute():
            path = Path(context.cwd) / path
        find = str(tool_input["find"])
        replace = str(tool_input["replace"])

        if not path.exists():
            return {
                "status": "error",
                "error": {"code": "FILE_NOT_FOUND", "message": f"file not found: {path}"},
            }
        if not path.is_file():
            return {
                "status": "error",
                "error": {"code": "NOT_A_FILE", "message": f"path is not a file: {path}"},
            }
        if find == "":
            return {
                "status": "error",
                "error": {"code": "EMPTY_FIND", "message": "find string must not be empty"},
            }

        original = path.read_text(encoding="utf-8", errors="replace")
        idx = original.find(find)
        if idx < 0:
            return {
                "status": "error",
                "error": {"code": "FIND_TARGET_NOT_FOUND", "message": "find target not found"},
            }
        updated = original.replace(find, replace, 1)
        path.write_text(updated, encoding="utf-8")
        return {"status": "success", "path": str(path.resolve()), "replaced": True}
