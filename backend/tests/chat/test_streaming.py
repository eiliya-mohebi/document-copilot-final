"""AI SDK UI message stream adapter emits the expected SSE event sequence."""

from __future__ import annotations

import json

import pytest

from app.chat.streaming import stub_ui_message_stream


@pytest.mark.asyncio
async def test_stub_stream_yields_text_deltas_then_done() -> None:
    chunks = [chunk async for chunk in stub_ui_message_stream("Hello world")]
    body = "".join(chunks)
    events: list[dict | str] = []
    for block in body.split("\n\n"):
        line = block.strip()
        if not line.startswith("data: "):
            continue
        payload = line.removeprefix("data: ").strip()
        if payload == "[DONE]":
            events.append("[DONE]")
        else:
            events.append(json.loads(payload))

    assert events[-1] == "[DONE]"
    typed = [e for e in events if isinstance(e, dict)]
    assert typed[0]["type"] == "start"
    assert "messageId" in typed[0]

    text_ids = {e["id"] for e in typed if e["type"] in {"text-start", "text-delta", "text-end"}}
    assert len(text_ids) == 1

    deltas = "".join(e["delta"] for e in typed if e["type"] == "text-delta")
    assert deltas == "Hello world"
    assert typed[-1]["type"] == "finish"
