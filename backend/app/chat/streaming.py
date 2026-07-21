"""AI SDK UI message stream (SSE) event helpers."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

DEFAULT_DELTA_SIZE = 24


def sse_event(payload: dict[str, Any] | str) -> str:
    if isinstance(payload, str):
        return f"data: {payload}\n\n"
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


def split_deltas(text: str, size: int = DEFAULT_DELTA_SIZE) -> Iterator[str]:
    """Split answer text into small deltas so the UI renders incrementally."""
    for start in range(0, len(text), size):
        yield text[start : start + size]
