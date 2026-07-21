"""Chat stream route: auth/ownership checks and orchestrator wiring."""

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

STREAM_BODY = {
    "threadId": str(THREAD_ID),
    "messages": [
        {
            "id": "msg-1",
            "role": "user",
            "parts": [{"type": "text", "text": "Hello"}],
        }
    ],
}


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
        events.append("[DONE]" if payload == "[DONE]" else json.loads(payload))
    return events


def test_stream_rejects_missing_bearer() -> None:
    with TestClient(app) as bare_client:
        response = bare_client.post("/chat/stream", json=STREAM_BODY)

    assert response.status_code == 401


def test_stream_rejects_unknown_thread(client: TestClient) -> None:
    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=None),
    ):
        response = client.post("/chat/stream", json=STREAM_BODY)

    assert response.status_code == 404


def test_stream_rejects_other_users_thread(client: TestClient) -> None:
    other_user = uuid.UUID("22222222-2222-2222-2222-222222222222")
    thread = type(
        "Thread",
        (),
        {"id": THREAD_ID, "user_id": other_user, "title": "Private"},
    )()

    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=thread),
    ):
        response = client.post("/chat/stream", json=STREAM_BODY)

    assert response.status_code == 403


def test_stream_rejects_payload_without_user_message(client: TestClient) -> None:
    thread = type(
        "Thread",
        (),
        {"id": THREAD_ID, "user_id": USER_ID, "title": "New chat"},
    )()

    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=thread),
    ):
        response = client.post(
            "/chat/stream",
            json={"threadId": str(THREAD_ID), "messages": []},
        )

    assert response.status_code == 422


def test_stream_delegates_to_orchestrator_and_relays_events(
    client: TestClient,
) -> None:
    thread = type(
        "Thread",
        (),
        {"id": THREAD_ID, "user_id": USER_ID, "title": "New chat"},
    )()

    async def fake_stream(session, thread_arg, user_message, **_: object):
        assert thread_arg is thread
        assert user_message.role == "user"
        yield 'data: {"type":"start","messageId":"msg_1"}\n\n'
        yield 'data: {"type":"text-delta","id":"t1","delta":"grounded"}\n\n'
        yield "data: [DONE]\n\n"

    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=thread),
    ), patch("app.api.chat.stream_chat_turn", fake_stream):
        response = client.post("/chat/stream", json=STREAM_BODY)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"

    events = _parse_sse_events(response.text)
    assert events[-1] == "[DONE]"
    assert {"type": "text-delta", "id": "t1", "delta": "grounded"} in events
