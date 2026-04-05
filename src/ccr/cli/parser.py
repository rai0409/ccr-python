from __future__ import annotations

import argparse
import os
from pathlib import Path

from .io_modes import InputMode, OutputMode


class CliValidationError(ValueError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ccr")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("-p", "--print", action="store_true", dest="print_mode")
    parser.add_argument("--output-format", choices=[m.value for m in OutputMode], default=OutputMode.TEXT.value)
    parser.add_argument("--input-format", choices=[m.value for m in InputMode], default=InputMode.TEXT.value)
    parser.add_argument("-c", "--continue", action="store_true", dest="do_continue")
    parser.add_argument("-r", "--resume", dest="resume_session_id")
    parser.add_argument("--fork-session", action="store_true")
    parser.add_argument("--session-id")
    parser.add_argument("--permission-mode", choices=["ask", "auto", "bypass"], default="ask")
    parser.add_argument("--allowed-tools", default="")
    parser.add_argument("--disallowed-tools", default="")
    parser.add_argument("--model", default="test-model")
    parser.add_argument("--fallback-model")
    parser.add_argument("--max-turns", type=int, default=32)
    parser.add_argument("--system-prompt")
    parser.add_argument("--append-system-prompt")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--add-dir", action="append", default=[])
    parser.add_argument("--transcript-dir", default=str(Path.home() / ".ccr" / "sessions"))
    parser.add_argument("--no-session-persistence", action="store_true")
    parser.add_argument("--tool-timeout-ms", type=int)
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.input_format == InputMode.STREAM_JSON.value and args.prompt:
        raise CliValidationError("invalid flag combination")
    if args.do_continue and args.resume_session_id:
        raise CliValidationError("invalid flag combination")
