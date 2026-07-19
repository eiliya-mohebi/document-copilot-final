"""Stub chat stream seam: authenticated POST /chat/stream emits AI SDK UI events."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database.session import get_session
from app.main import app

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
THREAD_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_EMAIL = "analyst@driftwood.com"


@pytest.fixture
def client() -> TestClient:
    async def override_user() -> CurrentUser:
        return CurrentUser(id=USER_ID, email=USER_EMAIL)

    async def override_session():
        yield MagicMock()

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _parse_sse_events(body: str) -> list[dict | str]:
    events: list[dict | str] = []
    for block in body.split("\n\n"):
        line = block.strip()
        if not line.startswith("data: "):
            continue
        payload = line.removeprefix("data: ").strip()
        if payload == "[DONE]":
            events.append("[DONE]")
            continue
        events.append(json.loads(payload))
    return events


def test_stream_rejects_missing_bearer() -> None:
    with TestClient(app) as bare_client:
        response = bare_client.post(
            "/chat/stream",
            json={
                "threadId": str(THREAD_ID),
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "parts": [{"type": "text", "text": "Hello"}],
                    }
                ],
            },
        )

    assert response.status_code == 401


def test_stream_rejects_unknown_thread(client: TestClient) -> None:
    with patch(
        "app.api.chat.chat_store.get_thread_for_user",
        AsyncMock(return_value=None),
    ):
        response = client.post(
            "/chat/stream",
            json={
                "threadId": str(THREAD_ID),
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "parts": [{"type": "text", "text": "Hello"}],
                    }
                ],
            },
        )

    assert response.status_code == 404


def test_stream_emits_ai_sdk_ui_message_events(client: TestClient) -> None:
    thread = type(
        "Thread",
        (),
        {"id": THREAD_ID, "user_id": USER_ID, "title": "New chat"},
    )()

    with (
        patch(
            "app.api.chat.chat_store.get_thread_for_user",
            AsyncMock(return_value=thread),
        ),
        patch(
            "app.api.chat.stub_ui_message_stream",
            stub_ui_message_stream_fast,
        ),
    ):
        response = client.post(
            "/chat/stream",
            json={
                "threadId": str(THREAD_ID),
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "parts": [{"type": "text", "text": "Hello"}],
                    }
                ],
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"

    events = _parse_sse_events(response.text)
    assert events[-1] == "[DONE]"

    typed = [e for e in events if isinstance(e, dict)]
    types = [e["type"] for e in typed]
    assert "start" in types
    assert "text-start" in types
    assert "text-delta" in types
    assert "text-end" in types
    assert "finish" in types

    deltas = "".join(e["delta"] for e in typed if e["type"] == "text-delta")
    assert len(deltas) > 0


async def stub_ui_message_stream_fast(text: str, **_: object):
    from app.chat.streaming import stub_ui_message_stream

    async for chunk in stub_ui_message_stream(text, chunk_delay_s=0):
        yield chunk
