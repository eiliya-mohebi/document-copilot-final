"""Retriever seam: hybrid search fuses vector + FTS rankings into passages."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.retrieval.retriever import ChunkRow, DocumentRetriever

DOC_ID = uuid.UUID("dddddddd-0000-0000-0000-000000000001")
CHUNK_IDS = [
    uuid.UUID(f"aaaaaaaa-0000-0000-0000-00000000000{n}") for n in range(1, 6)
]


def chunk_row(chunk_id: uuid.UUID, index: int) -> ChunkRow:
    return ChunkRow(
        chunk_id=chunk_id,
        document_id=DOC_ID,
        chunk_index=index,
        text=f"Passage {index}",
        section="Item 7",
        metadata={
            "company": "Apple Inc.",
            "ticker": "AAPL",
            "form": "10-K",
            "fiscal_year": "2021",
            "filing_date": "2021-10-29",
            "source_url": "https://example.test/aapl-10k",
        },
    )


async def embed_query(_: str) -> list[float]:
    return [0.0] * 4


async def test_search_fuses_semantic_and_lexical_and_records_passages() -> None:
    semantic_ids = [CHUNK_IDS[0], CHUNK_IDS[1], CHUNK_IDS[2]]
    lexical_ids = [CHUNK_IDS[1], CHUNK_IDS[3]]
    rows = {cid: chunk_row(cid, i) for i, cid in enumerate(CHUNK_IDS)}

    retriever = DocumentRetriever(MagicMock(), embed_query, top_k=3)
    with (
        patch(
            "app.retrieval.retriever.queries.semantic_search_ids",
            AsyncMock(return_value=semantic_ids),
        ),
        patch(
            "app.retrieval.retriever.queries.lexical_search_ids",
            AsyncMock(return_value=lexical_ids),
        ),
        patch(
            "app.retrieval.retriever.queries.fetch_chunk_rows",
            AsyncMock(side_effect=lambda _s, ids: [rows[i] for i in ids]),
        ),
    ):
        passages = await retriever.search("revenue growth")

    # CHUNK_IDS[1] appears in both rankings, so RRF puts it first.
    assert passages[0].chunk_id == CHUNK_IDS[1]
    assert len(passages) == 3
    assert passages[0].company == "Apple Inc."
    assert passages[0].fiscal_year == "2021"

    # Every returned passage is recorded for grounding validation.
    for p in passages:
        assert retriever.retrieved[p.chunk_id] == p


async def test_neighbors_are_recorded_as_retrieved() -> None:
    row = chunk_row(CHUNK_IDS[0], 4)
    retriever = DocumentRetriever(MagicMock(), embed_query)

    with patch(
        "app.retrieval.retriever.queries.fetch_neighbor_rows",
        AsyncMock(return_value=[row]),
    ):
        passages = await retriever.neighbors(DOC_ID, chunk_index=4, window=1)

    assert passages[0].chunk_id == CHUNK_IDS[0]
    assert CHUNK_IDS[0] in retriever.retrieved
