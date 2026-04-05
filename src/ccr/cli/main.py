from __future__ import annotations

import io
import json
import sys
from dataclasses import asdict
from typing import Callable, TextIO

from ccr.model.provider_base import EchoProvider, ProviderBase
from ccr.runtime.context import SessionConfig
from ccr.runtime.event_bus import EventBus
from ccr.runtime.orchestrator import SessionOrchestrator
from ccr.storage.session_index import SessionIndex
from ccr.storage.transcript_store import TranscriptStore

from . import exit_codes
from .io_modes import InputMode, OutputMode
from .parser import CliValidationError, build_parser, validate_args


PROVIDER_FACTORY: Callable[[SessionConfig], ProviderBase] = lambda _cfg: EchoProvider()


def _load_stream_json_messages(stdin_text: str) -> list[dict]:
    msgs: list[dict] = []
    if not stdin_text.strip():
        return msgs
    for line in stdin_text.splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        t = obj.get("type")
        if t not in {"user_message", "permission_decision", "interrupt"}:
            raise CliValidationError("unknown control message type")
        msgs.append(obj)
    return msgs


def run_cli(
    argv: list[str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        validate_args(args)
    except CliValidationError as exc:
        stderr.write(f"{exc}\n")
        return exit_codes.CLI_USAGE_ERROR
    except SystemExit:
        return exit_codes.CLI_USAGE_ERROR

    input_mode = InputMode(args.input_format)
    output_mode = OutputMode(args.output_format)

    stdin_blob = stdin.read()
    stream_messages: list[dict] = []
    if input_mode is InputMode.STREAM_JSON:
        try:
            stream_messages = _load_stream_json_messages(stdin_blob)
        except (json.JSONDecodeError, CliValidationError) as exc:
            stderr.write(f"{exc}\n")
            return exit_codes.CLI_USAGE_ERROR

    if input_mode is InputMode.TEXT:
        prompt = args.prompt if args.prompt is not None else stdin_blob
        if prompt == "":
            stderr.write("usage error: missing prompt\n")
            return exit_codes.CLI_USAGE_ERROR
    else:
        user_msgs = [m for m in stream_messages if m.get("type") == "user_message"]
        if not user_msgs:
            stderr.write("usage error: missing user_message\n")
            return exit_codes.CLI_USAGE_ERROR
        prompt = str(user_msgs[0].get("content", ""))

    config = SessionConfig(
        prompt=prompt,
        print_mode=bool(args.print_mode),
        input_mode=input_mode,
        output_mode=output_mode,
        permission_mode=args.permission_mode,
        model=args.model,
        fallback_model=args.fallback_model,
        cwd=args.cwd,
        transcript_dir=args.transcript_dir,
        no_session_persistence=bool(args.no_session_persistence),
        do_continue=bool(args.do_continue),
        resume_session_id=args.resume_session_id,
        fork_session=bool(args.fork_session),
        forced_session_id=args.session_id,
    )

    event_bus = EventBus()
    if output_mode is OutputMode.STREAM_JSON:
        def _emit_line(evt) -> None:
            stdout.write(json.dumps(evt.to_stream_dict(), separators=(",", ":")) + "\n")
        event_bus.subscribe(_emit_line)

    transcript_store = TranscriptStore(config.transcript_dir, persistence_enabled=not config.no_session_persistence)
    session_index = SessionIndex(config.transcript_dir)
    provider = PROVIDER_FACTORY(config)

    orchestrator = SessionOrchestrator(
        config=config,
        provider=provider,
        transcript_store=transcript_store,
        session_index=session_index,
        event_bus=event_bus,
    )

    try:
        result = orchestrator.run(stream_messages=stream_messages)
    except Exception as exc:  # pragma: no cover - top-level boundary
        stderr.write(f"internal invariant failure: {exc}\n")
        return exit_codes.INVARIANT_FAILURE

    if output_mode is OutputMode.TEXT:
        if result.final_assistant_message is not None:
            stdout.write(result.final_assistant_message + "\n")
    elif output_mode is OutputMode.JSON:
        payload = {
            "status": result.status,
            "session_id": result.session_id,
            "run_id": result.run_id,
            "assistant_message": {"content": result.final_assistant_message or ""},
        }
        stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")

    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run_cli())
