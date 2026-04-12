from __future__ import annotations

import io
import json
from pathlib import Path

from ccr.cli import main
from ccr.cli.main import run_cli
from ccr.runtime.events import EventEnvelope
from ccr.storage.transcript_store import TranscriptStore
from helpers.fake_provider import ScriptedProvider


def _append_seed_events(
    store: TranscriptStore,
    *,
    session_id: str,
    events: list[dict[str, object]],
) -> None:
    for seq, event in enumerate(events, start=1):
        store.append_event(
            EventEnvelope(
                event_id=f"E{seq}",
                session_id=session_id,
                run_id="R1",
                seq=seq,
                ts=f"2026-01-01T00:00:00.{seq:06d}Z",
                type=str(event["type"]),
                turn_index=int(event.get("turn_index", 1)),
                payload=dict(event.get("payload", {})),
                parent_event_id=f"E{seq - 1}" if seq > 1 else None,
                message_id=str(event["message_id"]) if "message_id" in event else None,
                tool_call_id=str(event["tool_call_id"]) if "tool_call_id" in event else None,
            )
        )


def test_resume_recovery_retries_interrupted_safe_read_once(monkeypatch) -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    Path("/tmp/ccr_ws/a.txt").write_text("alpha\n", encoding="utf-8")
    _append_seed_events(
        store,
        session_id="S1",
        events=[
            {"type": "session_start", "turn_index": 0, "payload": {"cwd": "/tmp/ccr_ws", "permission_mode": "ask", "model": "test-model"}},
            {"type": "user_message", "message_id": "M_USER_1", "payload": {"content": "read"}},
            {
                "type": "tool_call_requested",
                "tool_call_id": "TC1",
                "payload": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}},
            },
            {
                "type": "tool_permission_decided",
                "tool_call_id": "TC1",
                "payload": {"decision": "allow", "reason_code": "auto_safe"},
            },
            {"type": "tool_execution_started", "tool_call_id": "TC1", "payload": {"tool_name": "Read"}},
        ],
    )
    before = store.load_records("S1")

    monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg: ScriptedProvider([{"emit": "assistant_message", "content": "resumed"}]))
    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=[
            "--resume",
            "S1",
            "--input-format",
            "stream-json",
            "--cwd",
            "/tmp/ccr_ws",
            "--transcript-dir",
            "/tmp/ccr_sessions",
        ],
        stdin=io.StringIO(
            "\n".join(
                [
                    json.dumps({"type": "user_message", "content": "next"}),
                    json.dumps({"type": "permission_decision", "tool_call_id": "TC1", "decision": "allow_once"}),
                ]
            )
            + "\n"
        ),
        stdout=out,
        stderr=err,
    )
    assert code == 0
    assert out.getvalue() == "resumed\n"

    after = store.load_records("S1")
    assert after[: len(before)] == before

    appended = after[len(before) :]
    assert [r["type"] for r in appended] == [
        "session_resumed",
        "user_message",
        "tool_call_requested",
        "tool_permission_required",
        "tool_permission_decided",
        "tool_execution_started",
        "tool_result",
        "tool_execution_finished",
        "assistant_message",
        "session_completed",
    ]
    run2_started = [r for r in appended if r["type"] == "tool_execution_started"]
    assert len(run2_started) == 1
    assert run2_started[0]["payload"]["tool_name"] == "Read"


def test_resume_recovery_does_not_auto_resume_interrupted_write(monkeypatch) -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    _append_seed_events(
        store,
        session_id="S1",
        events=[
            {"type": "session_start", "turn_index": 0, "payload": {"cwd": "/tmp/ccr_ws", "permission_mode": "ask", "model": "test-model"}},
            {"type": "user_message", "message_id": "M_USER_1", "payload": {"content": "write"}},
            {
                "type": "tool_call_requested",
                "tool_call_id": "TC1",
                "payload": {"tool_name": "Write", "input": {"path": "/tmp/ccr_ws/recovered.txt", "content": "x"}},
            },
            {
                "type": "tool_permission_decided",
                "tool_call_id": "TC1",
                "payload": {"decision": "allow", "reason_code": "mode_ask"},
            },
            {"type": "tool_execution_started", "tool_call_id": "TC1", "payload": {"tool_name": "Write"}},
        ],
    )
    before = store.load_records("S1")

    monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg: ScriptedProvider([{"emit": "assistant_message", "content": "no auto write"}]))
    code = run_cli(
        argv=["--resume", "S1", "--input-format", "stream-json", "--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"],
        stdin=io.StringIO(json.dumps({"type": "user_message", "content": "next"}) + "\n"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code == 0
    assert not Path("/tmp/ccr_ws/recovered.txt").exists()

    after = store.load_records("S1")
    appended = after[len(before) :]
    assert [r["type"] for r in appended] == [
        "session_resumed",
        "user_message",
        "assistant_message",
        "session_completed",
    ]


def test_resume_recovery_does_not_auto_run_non_interrupted_completed_tool(monkeypatch) -> None:
    store = TranscriptStore("/tmp/ccr_sessions")
    Path("/tmp/ccr_ws/a.txt").write_text("alpha\n", encoding="utf-8")
    _append_seed_events(
        store,
        session_id="S1",
        events=[
            {"type": "session_start", "turn_index": 0, "payload": {"cwd": "/tmp/ccr_ws", "permission_mode": "ask", "model": "test-model"}},
            {"type": "user_message", "message_id": "M_USER_1", "payload": {"content": "read"}},
            {
                "type": "tool_call_requested",
                "tool_call_id": "TC1",
                "payload": {"tool_name": "Read", "input": {"path": "/tmp/ccr_ws/a.txt"}},
            },
            {"type": "tool_execution_started", "tool_call_id": "TC1", "payload": {"tool_name": "Read"}},
            {"type": "tool_result", "tool_call_id": "TC1", "payload": {"result": {"status": "success", "content": "alpha\n"}}},
            {"type": "tool_execution_finished", "tool_call_id": "TC1", "payload": {"status": "success"}},
        ],
    )
    before = store.load_records("S1")

    monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg: ScriptedProvider([{"emit": "assistant_message", "content": "already complete"}]))
    code = run_cli(
        argv=["--resume", "S1", "--input-format", "stream-json", "--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"],
        stdin=io.StringIO(json.dumps({"type": "user_message", "content": "next"}) + "\n"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert code == 0

    after = store.load_records("S1")
    appended = after[len(before) :]
    assert [r["type"] for r in appended] == [
        "session_resumed",
        "user_message",
        "assistant_message",
        "session_completed",
    ]
