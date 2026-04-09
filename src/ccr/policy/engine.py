from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any


SAFE_READ_TOOLS = {"Read", "LS", "Glob", "Grep"}


@dataclass(frozen=True)
class PermissionDecision:
    mode: str
    decision: str
    reason_code: str
    precedence_rank: int
    decision_source: str
    risk_label: str
    request_hash: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "reason_code": self.reason_code,
            "precedence_rank": self.precedence_rank,
            "decision_source": self.decision_source,
            "risk_label": self.risk_label,
            "request_hash": self.request_hash,
            "mode": self.mode,
        }


class PermissionEngine:
    """Phase 2A minimal deterministic permission engine."""

    def __init__(self, *, cwd: str) -> None:
        self.cwd = os.path.realpath(cwd)

    def _request_hash(self, *, tool_name: str, tool_input: dict[str, Any]) -> str:
        blob = json.dumps({"tool_name": tool_name, "input": tool_input}, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _extract_path(self, tool_input: dict[str, Any]) -> str | None:
        if isinstance(tool_input.get("path"), str):
            return str(tool_input["path"])
        if isinstance(tool_input.get("base_path"), str):
            return str(tool_input["base_path"])
        return None

    def _normalize_path(self, raw_path: str) -> str:
        if not os.path.isabs(raw_path):
            raw_path = os.path.join(self.cwd, raw_path)
        return os.path.realpath(raw_path)

    def _is_in_cwd(self, raw_path: str) -> bool:
        rp = self._normalize_path(raw_path)
        return rp == self.cwd or rp.startswith(self.cwd + os.sep)

    def _risk_label(self, tool_name: str) -> str:
        if tool_name in SAFE_READ_TOOLS:
            return "safe_read"
        return "unknown"

    def decide(
        self,
        *,
        tool_name: str,
        tool_input: dict[str, Any],
        mode: str,
        interactive_available: bool,
    ) -> PermissionDecision:
        del interactive_available
        request_hash = self._request_hash(tool_name=tool_name, tool_input=tool_input)
        risk_label = self._risk_label(tool_name)

        path = self._extract_path(tool_input)
        if path is not None and not self._is_in_cwd(path):
            return PermissionDecision(
                mode=mode,
                decision="deny",
                reason_code="hard_boundary_path_outside_root",
                precedence_rank=1,
                decision_source="hard_boundary",
                risk_label=risk_label,
                request_hash=request_hash,
            )

        if mode in {"auto", "bypass"} and tool_name in SAFE_READ_TOOLS:
            return PermissionDecision(
                mode=mode,
                decision="allow",
                reason_code="auto_safe",
                precedence_rank=7,
                decision_source="auto_label",
                risk_label="safe_read",
                request_hash=request_hash,
            )

        rank = 6 if mode == "ask" else 9
        return PermissionDecision(
            mode=mode,
            decision="deny",
            reason_code="ask_unavailable",
            precedence_rank=rank,
            decision_source="mode",
            risk_label=risk_label,
            request_hash=request_hash,
        )
