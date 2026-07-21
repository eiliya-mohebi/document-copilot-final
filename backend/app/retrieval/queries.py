"""Bounded SQL for hybrid retrieval over document_chunks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ChunkRow:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    section: str | None
    metadata: dict


_SEMANTIC_SQL = text(
    """
    SELECT id
    FROM document_chunks
    ORDER BY embedding <=> CAST(:embedding AS vector)
    LIMIT :limit
    """
)

_LEXICAL_SQL = text(
    """
    SELECT id
    FROM document_chunks
    WHERE search_vector @@ websearch_to_tsquery('english', :query)
    ORDER BY ts_rank(search_vector, websearch_to_tsquery('english', :query)) DESC
    LIMIT :limit
    """
)

_FETCH_SQL = text(
    """
    SELECT id, document_id, chunk_index, text, section, metadata
    FROM document_chunks
    WHERE id = ANY(:ids)
    """
)

_NEIGHBORS_SQL = text(
    """
    SELECT id, document_id, chunk_index, text, section, metadata
    FROM document_chunks
    WHERE document_id = :document_id
      AND chunk_index BETWEEN :low AND :high
    ORDER BY chunk_index
    """
)


async def semantic_search_ids(
    session: AsyncSession,
    embedding: list[float],
    limit: int,
) -> list[uuid.UUID]:
    embedding_literal = "[" + ",".join(str(v) for v in embedding) + "]"
    result = await session.execute(
        _SEMANTIC_SQL, {"embedding": embedding_literal, "limit": limit}
    )
    return [row.id for row in result]


async def lexical_search_ids(
    session: AsyncSession,
    query: str,
    limit: int,
) -> list[uuid.UUID]:
    result = await session.execute(_LEXICAL_SQL, {"query": query, "limit": limit})
    return [row.id for row in result]


async def fetch_chunk_rows(
    session: AsyncSession,
    chunk_ids: list[uuid.UUID],
) -> list[ChunkRow]:
    if not chunk_ids:
        return []
    result = await session.execute(_FETCH_SQL, {"ids": chunk_ids})
    return [_to_row(row) for row in result]


async def fetch_neighbor_rows(
    session: AsyncSession,
    document_id: uuid.UUID,
    chunk_index: int,
    window: int,
) -> list[ChunkRow]:
    result = await session.execute(
        _NEIGHBORS_SQL,
        {
            "document_id": document_id,
            "low": chunk_index - window,
            "high": chunk_index + window,
        },
    )
    return [_to_row(row) for row in result]


def _to_row(row) -> ChunkRow:
    return ChunkRow(
        chunk_id=row.id,
        document_id=row.document_id,
        chunk_index=row.chunk_index,
        text=row.text,
        section=row.section,
        metadata=row.metadata or {},
    )
