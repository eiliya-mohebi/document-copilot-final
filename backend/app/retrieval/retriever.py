"""Hybrid query-to-source-passage retrieval with an audit of what was seen."""

from __future__ import annotations

import uuid
from typing import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.outputs import SourcePassage
from app.retrieval import queries
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import ChunkRow

EmbedQuery = Callable[[str], Awaitable[list[float]]]

DEFAULT_CANDIDATES_PER_QUERY = 20
DEFAULT_TOP_K = 8


class DocumentRetriever:
    """Runs hybrid search and records every passage handed to the agent.

    `retrieved` is the grounding audit trail: the validator only accepts
    citations to chunk ids present in this mapping.
    """

    def __init__(
        self,
        session: AsyncSession,
        embed_query: EmbedQuery,
        *,
        candidates_per_query: int = DEFAULT_CANDIDATES_PER_QUERY,
        top_k: int = DEFAULT_TOP_K,
    ) -> None:
        self._session = session
        self._embed_query = embed_query
        self._candidates_per_query = candidates_per_query
        self._top_k = top_k
        self.retrieved: dict[uuid.UUID, SourcePassage] = {}

    async def search(self, query: str) -> list[SourcePassage]:
        embedding = await self._embed_query(query)
        semantic_ids = await queries.semantic_search_ids(
            self._session, embedding, self._candidates_per_query
        )
        lexical_ids = await queries.lexical_search_ids(
            self._session, query, self._candidates_per_query
        )

        fused_ids = reciprocal_rank_fusion([semantic_ids, lexical_ids])
        selected = fused_ids[: self._top_k]
        rows = await queries.fetch_chunk_rows(self._session, selected)

        by_id = {row.chunk_id: row for row in rows}
        passages = [
            self._record(by_id[chunk_id]) for chunk_id in selected if chunk_id in by_id
        ]
        return passages

    async def neighbors(
        self,
        document_id: uuid.UUID,
        chunk_index: int,
        window: int = 1,
    ) -> list[SourcePassage]:
        rows = await queries.fetch_neighbor_rows(
            self._session, document_id, chunk_index, window
        )
        return [self._record(row) for row in rows]

    async def read_chunks(self, chunk_ids: list[uuid.UUID]) -> list[SourcePassage]:
        rows = await queries.fetch_chunk_rows(self._session, chunk_ids)
        return [self._record(row) for row in rows]

    def _record(self, row: ChunkRow) -> SourcePassage:
        passage = _to_passage(row)
        self.retrieved[passage.chunk_id] = passage
        return passage


def _to_passage(row: ChunkRow) -> SourcePassage:
    meta = row.metadata
    return SourcePassage(
        chunk_id=row.chunk_id,
        document_id=row.document_id,
        chunk_index=row.chunk_index,
        text=row.text,
        section=row.section,
        company=meta.get("company", ""),
        ticker=meta.get("ticker", ""),
        form=meta.get("form", ""),
        fiscal_year=meta.get("fiscal_year", ""),
        filing_date=meta.get("filing_date", ""),
        source_url=meta.get("source_url", ""),
    )
