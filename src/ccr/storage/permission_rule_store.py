from __future__ import annotations

from pathlib import Path

from ccr.util import jsonl

from .lockfile import session_lock


class PermissionRuleStore:
    def __init__(self, transcript_dir: str, *, enabled: bool = True) -> None:
        self._enabled = enabled
        self._path = Path(transcript_dir) / "permission_rules.jsonl"
        self._lock_path = Path(transcript_dir) / "permission_rules.lock"

    def load_hash_sets(self) -> tuple[set[str], set[str]]:
        allow_hashes: set[str] = set()
        deny_hashes: set[str] = set()
        if not self._enabled:
            return allow_hashes, deny_hashes

        for row in jsonl.read_jsonl(self._path):
            request_hash = str(row.get("request_hash", ""))
            decision = str(row.get("decision", ""))
            if request_hash == "":
                continue
            if decision == "allow":
                allow_hashes.add(request_hash)
            elif decision == "deny":
                deny_hashes.add(request_hash)
        return allow_hashes, deny_hashes

    def append_rule(self, request_hash: str, decision: str) -> None:
        if not self._enabled:
            return
        if decision not in {"allow", "deny"}:
            raise ValueError("invalid persistent rule decision")
        with session_lock(self._lock_path):
            jsonl.append_jsonl(
                self._path,
                {"request_hash": request_hash, "decision": decision},
                fsync=True,
            )
