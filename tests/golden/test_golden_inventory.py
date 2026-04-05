from __future__ import annotations

import io
import json
from pathlib import Path

import yaml

from ccr.cli import main
from ccr.cli.main import run_cli
from ccr.storage.transcript_store import TranscriptStore
from helpers.fake_provider import ScriptedProvider

PHASE1_CASES = {
    "cli_text_prompt_arg",
    "cli_text_prompt_stdin",
    "cli_json_output",
    "cli_stream_json_basic",
    "cli_invalid_flag_combo",
}


def _load_cases() -> list[dict]:
    p = Path(__file__).resolve().parents[2] / "docs" / "golden-tests.yaml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return [c for c in data["tests"] if c["test_name"] in PHASE1_CASES]


def _script_from_case(case: dict) -> list[dict]:
    script = case.get("environment_state", {}).get("model_script")
    if script is None:
        return [{"emit": "assistant_message", "content": "OK"}]
    return script


def test_phase1_golden_subset(monkeypatch) -> None:
    for case in _load_cases():
        monkeypatch.setattr(main, "PROVIDER_FACTORY", lambda _cfg, s=_script_from_case(case): ScriptedProvider(s))

        argv = list(case["cli_input"])
        if argv and argv[0] == "ccr":
            argv = argv[1:]
        argv.extend(["--cwd", "/tmp/ccr_ws", "--transcript-dir", "/tmp/ccr_sessions"])

        env = case.get("environment_state", {})
        stdin_text = env.get("stdin_text", "")
        if env.get("stdin_ndjson"):
            stdin_text = "\n".join(json.dumps(x) for x in env["stdin_ndjson"]) + "\n"

        out = io.StringIO()
        err = io.StringIO()
        code = run_cli(argv=argv, stdin=io.StringIO(stdin_text), stdout=out, stderr=err)

        expected = case["expected_outputs"]
        assert code == expected["exit_code"], case["test_name"]
        if expected.get("json_output") is None and expected.get("stream_json") in (None, []):
            if "stdout_text" in expected:
                assert out.getvalue() == expected["stdout_text"], case["test_name"]
        if "stderr_text" in expected:
            assert err.getvalue() == expected["stderr_text"], case["test_name"]
        if expected.get("stderr_text_regex"):
            assert expected["stderr_text_regex"] in err.getvalue(), case["test_name"]

        if expected.get("json_output") is not None:
            obj = json.loads(out.getvalue())
            assert set(obj.keys()) == set(expected["json_output"]["exact_keys"]), case["test_name"]
            assert obj["status"] == expected["json_output"]["exact_values"]["status"], case["test_name"]
            assert obj["assistant_message"]["content"] == expected["json_output"]["exact_values"]["assistant_message"]["content"], case["test_name"]

        if expected.get("stream_json") not in (None, []):
            lines = [ln for ln in out.getvalue().splitlines() if ln.strip()]
            assert len(lines) == expected["stream_json"]["line_count"], case["test_name"]
            types = [json.loads(ln)["type"] for ln in lines]
            assert types == expected["stream_json"]["ordered_types"], case["test_name"]

    # One representative persistence check from canonical golden
    recs = TranscriptStore("/tmp/ccr_sessions").load_records("S1")
    assert [r["seq"] for r in recs][:4] == [1, 2, 4, 5]
    assert [r["type"] for r in recs][:4] == ["session_start", "user_message", "assistant_message", "session_completed"]
