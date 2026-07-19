"""Thread create seam: authenticated POST /threads creates an owned thread."""

from __future__ import annotations

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


def test_create_thread_rejects_missing_bearer() -> None:
    with TestClient(app) as bare_client:
        response = bare_client.post("/threads", json={})

    assert response.status_code == 401


def test_create_thread_returns_owned_thread(client: TestClient) -> None:
    created = type(
        "Thread",
        (),
        {
            "id": THREAD_ID,
            "user_id": USER_ID,
            "title": "New chat",
        },
    )()

    with patch(
        "app.api.chat.chat_store.create_thread",
        AsyncMock(return_value=created),
    ) as mock_create:
        response = client.post("/threads", json={})

    assert response.status_code == 201
    assert response.json() == {
        "id": str(THREAD_ID),
        "title": "New chat",
    }
    mock_create.assert_awaited_once()
    assert mock_create.await_args.args[1] == USER_ID
    assert mock_create.await_args.kwargs["email"] == USER_EMAIL
