from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    model: str


@dataclass(frozen=True)
class ModelChunk:
    kind: str
    content: str


class ProviderBase(ABC):
    @abstractmethod
    def stream(self, request: ModelRequest) -> Iterator[ModelChunk]:
        raise NotImplementedError


class EchoProvider(ProviderBase):
    def stream(self, request: ModelRequest) -> Iterator[ModelChunk]:
        yield ModelChunk(kind="message", content="OK")
