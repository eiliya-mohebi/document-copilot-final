"""Thread list / history / delete seam: authenticated thread CRUD for history."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database.session import get_session
from app.main import app

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
THREAD_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OTHER_THREAD_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
USER_EMAIL = "analyst@driftwood.com"
UPDATED_AT = datetime(2026, 7, 19, 12, 0, tzinfo=timezone.utc)


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


def test_list_threads_rejects_missing_bearer() -> None:
    with TestClient(app) as bare_client:
        response = bare_client.get("/threads")

    assert response.status_code == 401


def test_list_threads_returns_own_threads(client: TestClient) -> None:
    threads = [
        type(
            "Thread",
            (),
            {
                "id": THREAD_ID,
                "user_id": USER_ID,
                "title": "Filing Q2",
                "updated_at": UPDATED_AT,
            },
        )(),
        type(
            "Thread",
            (),
            {
                "id": OTHER_THREAD_ID,
                "user_id": USER_ID,
                "title": "New chat",
                "updated_at": UPDATED_AT,
            },
        )(),
    ]

    with patch(
        "app.api.chat.chat_store.list_threads_for_user",
        AsyncMock(return_value=threads),
    ) as mock_list:
        response = client.get("/threads")

    assert response.status_code == 200
    assert response.json() == {
        "threads": [
            {
                "id": str(THREAD_ID),
                "title": "Filing Q2",
                "updatedAt": UPDATED_AT.isoformat().replace("+00:00", "Z"),
            },
            {
                "id": str(OTHER_THREAD_ID),
                "title": "New chat",
                "updatedAt": UPDATED_AT.isoformat().replace("+00:00", "Z"),
            },
        ]
    }
    mock_list.assert_awaited_once()
    assert mock_list.await_args.args[1] == USER_ID


def test_get_thread_rejects_missing_bearer() -> None:
    with TestClient(app) as bare_client:
        response = bare_client.get(f"/threads/{THREAD_ID}")

    assert response.status_code == 401


def test_get_thread_returns_404_when_missing(client: TestClient) -> None:
    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=None),
    ):
        response = client.get(f"/threads/{THREAD_ID}")

    assert response.status_code == 404


def test_get_thread_returns_403_for_other_users_thread(client: TestClient) -> None:
    thread = type(
        "Thread",
        (),
        {
            "id": THREAD_ID,
            "user_id": OTHER_USER_ID,
            "title": "Private",
            "updated_at": UPDATED_AT,
        },
    )()

    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=thread),
    ):
        response = client.get(f"/threads/{THREAD_ID}")

    assert response.status_code == 403


def test_get_thread_returns_persisted_history(client: TestClient) -> None:
    thread = type(
        "Thread",
        (),
        {
            "id": THREAD_ID,
            "user_id": USER_ID,
            "title": "Filing Q2",
            "updated_at": UPDATED_AT,
        },
    )()
    messages = [
        type(
            "Message",
            (),
            {
                "id": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                "role": "user",
                "parts": [{"type": "text", "text": "Hello"}],
                "content": "Hello",
                "sequence_number": 1,
            },
        )(),
        type(
            "Message",
            (),
            {
                "id": uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                "role": "assistant",
                "parts": [{"type": "text", "text": "Stub reply"}],
                "content": "Stub reply",
                "sequence_number": 2,
            },
        )(),
    ]

    with (
        patch(
            "app.api.chat.chat_store.get_thread_by_id",
            AsyncMock(return_value=thread),
        ),
        patch(
            "app.api.chat.chat_store.list_messages_for_thread",
            AsyncMock(return_value=messages),
        ) as mock_messages,
    ):
        response = client.get(f"/threads/{THREAD_ID}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(THREAD_ID),
        "title": "Filing Q2",
        "messages": [
            {
                "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "role": "user",
                "parts": [{"type": "text", "text": "Hello"}],
            },
            {
                "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                "role": "assistant",
                "parts": [{"type": "text", "text": "Stub reply"}],
            },
        ],
    }
    mock_messages.assert_awaited_once()
    assert mock_messages.await_args.args[1] == THREAD_ID


def test_delete_thread_rejects_missing_bearer() -> None:
    with TestClient(app) as bare_client:
        response = bare_client.delete(f"/threads/{THREAD_ID}")

    assert response.status_code == 401


def test_delete_thread_returns_404_when_missing(client: TestClient) -> None:
    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=None),
    ):
        response = client.delete(f"/threads/{THREAD_ID}")

    assert response.status_code == 404


def test_delete_thread_returns_403_for_other_users_thread(client: TestClient) -> None:
    thread = type(
        "Thread",
        (),
        {
            "id": THREAD_ID,
            "user_id": OTHER_USER_ID,
            "title": "Private",
            "updated_at": UPDATED_AT,
        },
    )()

    with patch(
        "app.api.chat.chat_store.get_thread_by_id",
        AsyncMock(return_value=thread),
    ):
        response = client.delete(f"/threads/{THREAD_ID}")

    assert response.status_code == 403


def test_delete_own_thread_returns_204(client: TestClient) -> None:
    thread = type(
        "Thread",
        (),
        {
            "id": THREAD_ID,
            "user_id": USER_ID,
            "title": "Filing Q2",
            "updated_at": UPDATED_AT,
        },
    )()

    with (
        patch(
            "app.api.chat.chat_store.get_thread_by_id",
            AsyncMock(return_value=thread),
        ),
        patch(
            "app.api.chat.chat_store.delete_thread",
            AsyncMock(),
        ) as mock_delete,
    ):
        response = client.delete(f"/threads/{THREAD_ID}")

    assert response.status_code == 204
    mock_delete.assert_awaited_once()
    assert mock_delete.await_args.args[1] is thread
