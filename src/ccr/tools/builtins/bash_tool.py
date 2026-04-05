from __future__ import annotations

import subprocess
from typing import Any

from ccr.tools.base import BaseTool, ToolExecutionContext


class BashTool(BaseTool):
    name = "Bash"
    is_read_only = False

    def execute(self, tool_input: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
        command = str(tool_input["command"])
        completed = subprocess.run(
            command,
            shell=True,
            cwd=context.cwd,
            capture_output=True,
            text=True,
        )
        return {
            "status": "success",
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
