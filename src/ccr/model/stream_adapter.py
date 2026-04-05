from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from .provider_base import ModelChunk


@dataclass(frozen=True)
class AdaptedChunk:
    kind: str
    content: str


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
            else:
                raise RuntimeError(f"unsupported chunk kind: {chunk.kind}")
