from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from .provider_base import ModelChunk, ModelRequest, ProviderBase


@dataclass(frozen=True)
class RetryResult:
    chunks: list[ModelChunk]


class RetryFallbackManager:
    """Phase 1 minimal path: single attempt, no fallback execution."""

    def run(self, provider: ProviderBase, request: ModelRequest) -> RetryResult:
        return RetryResult(chunks=list(provider.stream(request)))
