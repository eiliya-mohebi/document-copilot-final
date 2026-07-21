"""Load a cited chunk plus neighboring passages for the source passage UI."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.outputs import SourcePassage
from app.retrieval import queries
from app.retrieval.queries import ChunkRow

DEFAULT_NEIGHBOR_WINDOW = 1


@dataclass(frozen=True)
class CitationContext:
    passage: SourcePassage
    neighbors: list[SourcePassage]


async def get_citation_context(
    session: AsyncSession,
    chunk_id: uuid.UUID,
    *,
    window: int = DEFAULT_NEIGHBOR_WINDOW,
) -> CitationContext | None:
    rows = await queries.fetch_chunk_rows(session, [chunk_id])
    if not rows:
        return None

    focus = rows[0]
    neighbor_rows = await queries.fetch_neighbor_rows(
        session, focus.document_id, focus.chunk_index, window
    )
    return CitationContext(
        passage=_to_passage(focus),
        neighbors=[
            _to_passage(row)
            for row in neighbor_rows
            if row.chunk_id != focus.chunk_id
        ],
    )


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
