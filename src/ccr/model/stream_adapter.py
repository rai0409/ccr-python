from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator

from .provider_base import ModelChunk


@dataclass(frozen=True)
class AdaptedChunk:
    kind: str
    content: Any


class ModelStreamAdapter:
    def adapt(self, chunks: Iterable[ModelChunk]) -> Iterator[AdaptedChunk]:
        saw_delta = False
        for chunk in chunks:
            if chunk.kind == "delta":
                saw_delta = True
                yield AdaptedChunk(kind="assistant_delta", content=chunk.content)
            elif chunk.kind == "message":
                if not saw_delta:
                    yield AdaptedChunk(kind="assistant_delta", content=chunk.content)
                yield AdaptedChunk(kind="assistant_message", content=chunk.content)
                saw_delta = False
            elif chunk.kind == "tool":
                yield AdaptedChunk(kind="tool_call", content=chunk.content)
            else:
                raise RuntimeError(f"unsupported chunk kind: {chunk.kind}")
