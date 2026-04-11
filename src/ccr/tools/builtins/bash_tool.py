from __future__ import annotations

import os
import shlex
import subprocess
from typing import Any

from ccr.tools.base import BaseTool, ToolExecutionContext


_BASH_TIMEOUT_SECONDS = 5


def _to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _is_path_like_token(token: str) -> bool:
    if token.startswith("-"):
        return False
    if os.path.isabs(token):
        return True
    return token.startswith(".") or "/" in token


def _normalize_from_cwd(raw_path: str, cwd: str) -> str:
    if os.path.isabs(raw_path):
        return os.path.realpath(raw_path)
    return os.path.realpath(os.path.join(cwd, raw_path))


def _is_within_root(path: str, root: str) -> bool:
    return path == root or path.startswith(root + os.sep)


class BashTool(BaseTool):
    name = "Bash"
    is_read_only = False

    def execute(self, tool_input: dict[str, Any], context: ToolExecutionContext) -> dict[str, Any]:
        command = str(tool_input["command"])
        root = os.path.realpath(context.cwd)
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return {
                "status": "error",
                "exit_code": None,
                "stdout": "",
                "stderr": "",
                "error": {
                    "code": "COMMAND_EXECUTION_FAILED",
                    "message": f"failed to parse command: {exc}",
                },
            }

        if not argv:
            return {
                "status": "error",
                "exit_code": None,
                "stdout": "",
                "stderr": "",
                "error": {
                    "code": "COMMAND_EXECUTION_FAILED",
                    "message": "failed to execute command: empty command",
                },
            }

        for token in argv[1:]:
            if not _is_path_like_token(token):
                continue
            resolved = _normalize_from_cwd(token, root)
            if _is_within_root(resolved, root):
                continue
            return {
                "status": "error",
                "exit_code": None,
                "stdout": "",
                "stderr": "",
                "error": {
                    "code": "COMMAND_PATH_OUTSIDE_ROOT",
                    "message": f"path argument outside workspace root: {token}",
                },
            }

        try:
            completed = subprocess.run(
                argv,
                shell=False,
                cwd=context.cwd,
                capture_output=True,
                text=True,
                timeout=_BASH_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            timeout_stdout = exc.stdout if exc.stdout is not None else exc.output
            return {
                "status": "error",
                "exit_code": None,
                "stdout": _to_text(timeout_stdout),
                "stderr": _to_text(exc.stderr),
                "error": {
                    "code": "COMMAND_TIMEOUT",
                    "message": f"command timed out after {_BASH_TIMEOUT_SECONDS} seconds",
                },
            }
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "status": "error",
                "exit_code": None,
                "stdout": "",
                "stderr": "",
                "error": {
                    "code": "COMMAND_EXECUTION_FAILED",
                    "message": f"failed to execute command: {exc}",
                },
            }

        status = "success" if completed.returncode == 0 else "error"
        return {
            "status": status,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
