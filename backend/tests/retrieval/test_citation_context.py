"""Citation-context seam: load a chunk plus neighboring filing passages."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.retrieval.citation_context import get_citation_context
from app.retrieval.queries import ChunkRow

DOC_ID = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
CHUNK_IDS = [
    uuid.UUID(f"aaaaaaaa-0000-0000-0000-00000000000{n}") for n in range(1, 4)
]


def chunk_row(chunk_id: uuid.UUID, index: int) -> ChunkRow:
    return ChunkRow(
        chunk_id=chunk_id,
        document_id=DOC_ID,
        chunk_index=index,
        text=f"Passage {index}",
        section="Item 1A",
        metadata={
            "company": "Apple Inc.",
            "ticker": "AAPL",
            "form": "10-K",
            "fiscal_year": "2021",
            "filing_date": "2021-10-29",
            "source_url": "https://example.test/aapl-10k",
        },
    )


@pytest.mark.asyncio
async def test_returns_passage_and_neighbors_excluding_focus() -> None:
    focus = chunk_row(CHUNK_IDS[1], 5)
    before = chunk_row(CHUNK_IDS[0], 4)
    after = chunk_row(CHUNK_IDS[2], 6)

    with (
        patch(
            "app.retrieval.citation_context.queries.fetch_chunk_rows",
            AsyncMock(return_value=[focus]),
        ),
        patch(
            "app.retrieval.citation_context.queries.fetch_neighbor_rows",
            AsyncMock(return_value=[before, focus, after]),
        ) as neighbors,
    ):
        result = await get_citation_context(MagicMock(), CHUNK_IDS[1], window=1)

    assert result is not None
    assert result.passage.chunk_id == CHUNK_IDS[1]
    assert result.passage.company == "Apple Inc."
    assert result.passage.section == "Item 1A"
    assert result.passage.text == "Passage 5"
    assert [n.chunk_id for n in result.neighbors] == [CHUNK_IDS[0], CHUNK_IDS[2]]
    neighbors.assert_awaited_once()
    assert neighbors.await_args.args[1:] == (DOC_ID, 5, 1)


@pytest.mark.asyncio
async def test_returns_none_when_chunk_missing() -> None:
    with patch(
        "app.retrieval.citation_context.queries.fetch_chunk_rows",
        AsyncMock(return_value=[]),
    ):
        result = await get_citation_context(MagicMock(), CHUNK_IDS[0])

    assert result is None
