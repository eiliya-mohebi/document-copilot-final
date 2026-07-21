"""Citation-context route: auth and chunk lookup for the passage UI."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.assistant.outputs import SourcePassage
from app.auth.dependencies import CurrentUser, get_current_user
from app.database.session import get_session
from app.main import app
from app.retrieval.citation_context import CitationContext

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_EMAIL = "analyst@driftwood.com"
CHUNK_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
DOC_ID = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
NEIGHBOR_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002")


def _passage(
    chunk_id: uuid.UUID,
    *,
    index: int = 5,
    text: str = "Focus passage",
) -> SourcePassage:
    return SourcePassage(
        chunk_id=chunk_id,
        document_id=DOC_ID,
        chunk_index=index,
        text=text,
        section="Item 1A",
        company="Apple Inc.",
        ticker="AAPL",
        form="10-K",
        fiscal_year="2021",
        filing_date="2021-10-29",
        source_url="https://example.test/aapl-10k",
    )


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


def test_citation_context_rejects_missing_bearer() -> None:
    with TestClient(app) as bare_client:
        response = bare_client.get(f"/citations/{CHUNK_ID}/context")

    assert response.status_code == 401


def test_citation_context_returns_404_when_chunk_missing(client: TestClient) -> None:
    with patch(
        "app.api.citations.get_citation_context",
        AsyncMock(return_value=None),
    ):
        response = client.get(f"/citations/{CHUNK_ID}/context")

    assert response.status_code == 404
    assert response.json()["detail"] == "Chunk not found"


def test_citation_context_returns_passage_and_neighbors(client: TestClient) -> None:
    context = CitationContext(
        passage=_passage(CHUNK_ID),
        neighbors=[_passage(NEIGHBOR_ID, index=6, text="Next passage")],
    )

    with patch(
        "app.api.citations.get_citation_context",
        AsyncMock(return_value=context),
    ):
        response = client.get(f"/citations/{CHUNK_ID}/context")

    assert response.status_code == 200
    body = response.json()
    assert body["passage"]["chunkId"] == str(CHUNK_ID)
    assert body["passage"]["company"] == "Apple Inc."
    assert body["passage"]["form"] == "10-K"
    assert body["passage"]["fiscalYear"] == "2021"
    assert body["passage"]["section"] == "Item 1A"
    assert body["passage"]["text"] == "Focus passage"
    assert body["neighbors"][0]["chunkId"] == str(NEIGHBOR_ID)
    assert body["neighbors"][0]["text"] == "Next passage"
