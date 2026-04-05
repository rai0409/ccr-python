from __future__ import annotations

import io
from dataclasses import dataclass

from ccr.cli.main import run_cli


@dataclass(frozen=True)
class CliRunCapture:
    exit_code: int
    stdout: str
    stderr: str


def run_cli_capture(argv: list[str], *, stdin_text: str = "") -> CliRunCapture:
    stdin = io.StringIO(stdin_text)
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_cli(argv=argv, stdin=stdin, stdout=stdout, stderr=stderr)
    return CliRunCapture(exit_code=code, stdout=stdout.getvalue(), stderr=stderr.getvalue())
