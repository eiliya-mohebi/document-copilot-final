"""Emit AI SDK UI message stream (SSE) events."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any


def _sse(payload: dict[str, Any] | str) -> str:
    if isinstance(payload, str):
        return f"data: {payload}\n\n"
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


async def stub_ui_message_stream(
    text: str,
    *,
    chunk_size: int = 12,
    chunk_delay_s: float = 0.03,
) -> AsyncIterator[str]:
    """Yield a stubbed assistant reply as AI SDK UI message stream SSE chunks."""
    message_id = f"msg_{uuid.uuid4().hex}"
    text_id = f"text_{uuid.uuid4().hex}"

    yield _sse({"type": "start", "messageId": message_id})
    yield _sse({"type": "text-start", "id": text_id})

    for start in range(0, len(text), chunk_size):
        delta = text[start : start + chunk_size]
        yield _sse({"type": "text-delta", "id": text_id, "delta": delta})
        if chunk_delay_s > 0:
            await asyncio.sleep(chunk_delay_s)

    yield _sse({"type": "text-end", "id": text_id})
    yield _sse({"type": "finish"})
    yield _sse("[DONE]")


STUB_REPLY = (
    "This is a stubbed Document Copilot reply. "
    "Retrieval and grounded generation are not wired up yet."
)
