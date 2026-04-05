from __future__ import annotations


def parse_schema_version(v: str) -> tuple[int, int]:
    major, minor = v.split(".", 1)
    return int(major), int(minor)


def ensure_supported_schema(v: str) -> None:
    major, _ = parse_schema_version(v)
    if major != 1:
        raise RuntimeError("unsupported schema major version")
