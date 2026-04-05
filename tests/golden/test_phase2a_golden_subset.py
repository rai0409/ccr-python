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

PHASE2A_CASES = {
    "event_tool_lifecycle_allow_order",
    "event_tool_lifecycle_deny_order",
    "permission_auto_read_allow",
    "tool_read_truncation",
    "tool_ls_sorted",
    "tool_glob_sorted",
    "tool_grep_ordering",
}


def _load_cases() -> list[dict[str, Any]]:
    p = Path(__file__).resolve().parents[2] / "docs" / "golden-tests.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return [c for c in data["tests"] if c["test_name"] in PHASE2A_CASES]


def _script_from_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    script = case.get("environment_state", {}).get("model_script")
    if script is None:
        return [{"emit": "assistant_message", "content": "OK"}]
    return script


def _materialize_files(file_specs: list[dict[str, Any]]) -> None:
    for spec in file_specs:
        path = Path(str(spec["path"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        if "content" in spec:
            path.write_text(str(spec["content"]), encoding="utf-8")
            continue
        if "bytes" in spec:
            target_bytes = int(spec["bytes"])
            lines = int(spec.get("lines", 1))
            pattern = str(spec.get("pattern", "x\n"))
            raw = (pattern * max(lines, 1)).encode("utf-8")
            if len(raw) < target_bytes:
                raw = raw + (b"x" * (target_bytes - len(raw)))
            else:
                raw = raw[:target_bytes]
            path.write_bytes(raw)
            continue
        path.write_text("", encoding="utf-8")


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
        executed.append(
            {
                "tool_name": str(rec["payload"]["tool_name"]),
                "input": dict(req.get("input", {})),
            }
        )
    return executed


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: str(c["test_name"]))
def test_phase2a_golden_subset(case: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg, s=_script_from_case(case): ScriptedProvider(s))

    env = dict(case.get("environment_state", {}))
    _materialize_files(list(env.get("files", [])))

    argv = list(case["cli_input"])
    if argv and argv[0] == "ccr":
        argv = argv[1:]
    argv.extend(["--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"])

    stdin_text = env.get("stdin_text", "")
    if env.get("stdin_ndjson"):
        stdin_text = "\n".join(json.dumps(x) for x in env["stdin_ndjson"]) + "\n"

    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(argv=argv, stdin=io.StringIO(stdin_text), stdout=out, stderr=err)

    expected = dict(case["expected_outputs"])
    assert code == int(expected["exit_code"]), case["test_name"]

    stream_lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
    stream_events = [json.loads(ln) for ln in stream_lines]

    if expected.get("stream_json") not in (None, []):
        types = [e["type"] for e in stream_events]
        assert types == list(expected["stream_json"]["ordered_types"]), case["test_name"]
        expected_seq_types = [(int(seq), str(tp)) for seq, tp in case["expected_ordered_event_sequence"]]
        got_seq_types = [(int(e["seq"]), str(e["type"])) for e in stream_events]
        assert got_seq_types == expected_seq_types, case["test_name"]

    records = TranscriptStore("/tmp/ccr_sessions").load_records("S1")
    assert_record_identity(records)
    assert_parent_chain(records)
    assert all(rec["type"] != "assistant_delta" for rec in records)

    expected_persisted = [
        (int(seq), str(tp))
        for seq, tp in case["expected_ordered_event_sequence"]
        if str(tp) != "assistant_delta"
    ]
    got_persisted = [(int(rec["seq"]), str(rec["type"])) for rec in records]
    assert got_persisted == expected_persisted, case["test_name"]

    expected_lines = list(case["expected_jsonl_transcript_entries"]["lines"])
    by_seq = {int(rec["seq"]): rec for rec in records}
    for line in expected_lines:
        rec = by_seq[int(line["seq"])]
        _assert_subset(line, rec)

    expected_calls = list(case.get("expected_tool_calls", []))
    executed_calls = _extract_executed_tool_calls(records)
    assert len(executed_calls) == len(expected_calls), case["test_name"]
    for i, exp in enumerate(expected_calls):
        got = executed_calls[i]
        assert got["tool_name"] == str(exp["tool_name"]), case["test_name"]
        if "input" in exp:
            assert got["input"] == dict(exp["input"]), case["test_name"]
