from __future__ import annotations

import io

from ccr.cli.main import run_cli


def test_cli_invalid_flag_combo() -> None:
    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=["-p", "hello", "--input-format", "stream-json"],
        stdin=io.StringIO(""),
        stdout=out,
        stderr=err,
    )
    assert code == 2
    assert "invalid flag combination" in err.getvalue()


def test_cli_stream_json_unknown_type_exits_2() -> None:
    out = io.StringIO()
    err = io.StringIO()
    code = run_cli(
        argv=["-p", "--input-format", "stream-json", "--output-format", "stream-json"],
        stdin=io.StringIO('{"type":"bad_type","x":1}\n'),
        stdout=out,
        stderr=err,
    )
    assert code == 2
    assert "unknown control message type" in err.getvalue()
