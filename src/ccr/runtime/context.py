from __future__ import annotations

from dataclasses import dataclass

from ccr.cli.io_modes import InputMode, OutputMode


@dataclass(frozen=True)
class SessionConfig:
    prompt: str
    print_mode: bool
    input_mode: InputMode
    output_mode: OutputMode
    permission_mode: str
    model: str
    fallback_model: str | None
    cwd: str
    transcript_dir: str
    no_session_persistence: bool
    do_continue: bool
    resume_session_id: str | None
    fork_session: bool
    forced_session_id: str | None
