from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from ccr.cli import main
from ccr.cli.main import run_cli
from ccr.storage.transcript_store import TranscriptStore
from helpers.fake_provider import ScriptedProvider
from helpers.transcript_assertions import assert_parent_chain, assert_record_identity

pytestmark = pytest.mark.skip(reason="Phase 2B golden subset is out of active Phase 2A scope")

PHASE2B_CASES = {
    "cli_ask_unavailable_exit6",
    "event_permission_required_only_when_askable",
    "permission_auto_dangerous_ask",
    "permission_auto_dangerous_noninteractive",
}


def _load_cases() -> list[dict[str, Any]]:
    p = Path(__file__).resolve().parents[2] / "docs" / "golden-tests.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return [c for c in data["tests"] if c["test_name"] in PHASE2B_CASES]


def _script_from_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    script = case.get("environment_state", {}).get("model_script")
    if script is None:
        return [{"emit": "assistant_message", "content": "OK"}]
    return script


def _assert_subset(expected: Any, actual: Any) -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict)
        for k, v in expected.items():
            assert k in actual
            _assert_subset(v, actual[k])
        return
    if isinstance(expected, list):
        assert expected == actual
        return
    assert expected == actual


def _extract_executed_tool_calls(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requested: dict[str, dict[str, Any]] = {}
    for rec in records:
        if rec["type"] == "tool_call_requested":
            requested[str(rec["tool_call_id"])] = dict(rec["payload"])

    executed: list[dict[str, Any]] = []
    for rec in records:
        if rec["type"] != "tool_execution_started":
            continue
        tcid = str(rec["tool_call_id"])
        req = requested.get(tcid, {})
        executed.append({"tool_name": str(rec["payload"]["tool_name"]), "input": dict(req.get("input", {}))})
    return executed


def _run_variant(case: dict[str, Any], variant: str | None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg, s=_script_from_case(case): ScriptedProvider(s))

    cli_input = case["cli_input"][variant] if variant is not None else case["cli_input"]
    env_root = dict(case.get("environment_state", {}))
    env = dict(env_root.get(variant, {})) if variant is not None else env_root

    argv = list(cli_input)
    if argv and argv[0] == "ccr":
        argv = argv[1:]
    if variant == "case_a":
        session_id = "S_CASE_A"
    elif variant == "case_b":
        session_id = "S_CASE_B"
    else:
        session_id = "S1"
    argv.extend(["--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions", "--session-id", session_id])

    stdin_text = str(env.get("stdin_text", ""))
    if env.get("stdin_ndjson"):
        stdin_text = "\n".join(json.dumps(x) for x in env["stdin_ndjson"]) + "\n"

    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(argv=argv, stdin=io.StringIO(stdin_text), stdout=out, stderr=err)

    expected_outputs_all = case["expected_outputs"]
    expected_outputs = expected_outputs_all[variant] if variant is not None else expected_outputs_all
    assert code == int(expected_outputs["exit_code"]), case["test_name"]

    if expected_outputs.get("stderr_text_regex"):
        assert str(expected_outputs["stderr_text_regex"]) in err.getvalue(), case["test_name"]

    expected_seq_all = case["expected_ordered_event_sequence"]
    expected_seq = expected_seq_all[variant] if variant is not None else expected_seq_all

    stream_lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
    if expected_outputs.get("stream_json") not in (None, []):
        stream_events = [json.loads(ln) for ln in stream_lines]
        expected_types = list(expected_outputs["stream_json"]["ordered_types"])
        assert [e["type"] for e in stream_events] == expected_types, case["test_name"]
        assert [(int(e["seq"]), str(e["type"])) for e in stream_events] == [
            (int(seq), str(tp)) for seq, tp in expected_seq
        ], case["test_name"]

    records = TranscriptStore("/tmp/ccr_sessions").load_records(session_id)
    assert_record_identity(records)
    assert_parent_chain(records)
    assert all(rec["type"] != "assistant_delta" for rec in records)

    expected_persisted = [(int(seq), str(tp)) for seq, tp in expected_seq if str(tp) != "assistant_delta"]
    assert [(int(rec["seq"]), str(rec["type"])) for rec in records] == expected_persisted, case["test_name"]

    expected_jsonl = case["expected_jsonl_transcript_entries"]
    if variant is None and "lines" in expected_jsonl:
        by_seq = {int(rec["seq"]): rec for rec in records}
        for line in expected_jsonl["lines"]:
            _assert_subset(line, by_seq[int(line["seq"])])

    if variant == "case_a":
        assert any(rec["type"] == "tool_permission_required" for rec in records), case["test_name"]
    if variant == "case_b":
        assert all(rec["type"] != "tool_permission_required" for rec in records), case["test_name"]
        decided = [rec for rec in records if rec["type"] == "tool_permission_decided"]
        assert decided and decided[0]["payload"]["reason_code"] == "ask_unavailable", case["test_name"]

    expected_tools_all = case.get("expected_tool_calls", [])
    expected_tools = expected_tools_all[variant] if variant is not None else expected_tools_all
    executed = _extract_executed_tool_calls(records)
    assert len(executed) == len(expected_tools), case["test_name"]
    for i, exp in enumerate(expected_tools):
        assert executed[i]["tool_name"] == str(exp["tool_name"]), case["test_name"]
        if "input" in exp:
            assert executed[i]["input"] == dict(exp["input"]), case["test_name"]


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: str(c["test_name"]))
def test_phase2b_golden_subset(case: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    if case["test_name"] == "event_permission_required_only_when_askable":
        _run_variant(case, "case_a", monkeypatch)
        _run_variant(case, "case_b", monkeypatch)
        return
    _run_variant(case, None, monkeypatch)
