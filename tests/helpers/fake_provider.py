from __future__ import annotations

from collections.abc import Iterator

from ccr.model.provider_base import ModelChunk, ModelRequest, ProviderBase


class ScriptedProvider(ProviderBase):
    def __init__(self, script: list[dict]) -> None:
        self.script = script

    def stream(self, request: ModelRequest) -> Iterator[ModelChunk]:
        for step in self.script:
            if "emit_delta" in step:
                yield ModelChunk(kind="delta", content=str(step["emit_delta"]))
            elif step.get("emit") == "assistant_message":
                yield ModelChunk(kind="message", content=str(step.get("content", "")))
            elif "emit_tool" in step:
                spec = step["emit_tool"]
                yield ModelChunk(
                    kind="tool",
                    content={
                        "tool_name": str(spec["tool_name"]),
                        "input": dict(spec.get("input", {})),
                    },
                )
            else:
                raise RuntimeError(f"unsupported scripted step: {step}")
