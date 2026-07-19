"""Auth boundary: GET /me requires a valid Supabase bearer token."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError

from app.main import app

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_EMAIL = "analyst@driftwood.com"


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_rejects_missing_bearer(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_rejects_empty_bearer(client: TestClient) -> None:
    response = client.get("/me", headers={"Authorization": "Bearer "})
    assert response.status_code == 401


def test_me_rejects_invalid_token(client: TestClient) -> None:
    mock_client = MagicMock()
    mock_client.auth.get_user = AsyncMock(
        side_effect=AuthApiError("invalid JWT", 401, None),
    )

    with patch(
        "app.auth.dependencies.acreate_client",
        AsyncMock(return_value=mock_client),
    ):
        response = client.get(
            "/me",
            headers={"Authorization": "Bearer bad-token"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_me_returns_current_user(client: TestClient) -> None:
    mock_user = SimpleNamespace(id=str(USER_ID), email=USER_EMAIL)
    mock_client = MagicMock()
    mock_client.auth.get_user = AsyncMock(
        return_value=SimpleNamespace(user=mock_user),
    )

    with patch(
        "app.auth.dependencies.acreate_client",
        AsyncMock(return_value=mock_client),
    ):
        response = client.get(
            "/me",
            headers={"Authorization": "Bearer good-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"id": str(USER_ID), "email": USER_EMAIL}
    mock_client.auth.get_user.assert_awaited_once_with(jwt="good-token")
