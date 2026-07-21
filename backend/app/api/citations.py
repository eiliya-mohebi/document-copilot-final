"""Authenticated citation-context routes for the source passage UI."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.assistant.outputs import SourcePassage
from app.database.session import get_session
from app.retrieval.citation_context import get_citation_context
from app.retrieval.schemas import CitationContextResponse, PassageResponse

router = APIRouter(tags=["citations"])


@router.get(
    "/citations/{chunk_id}/context",
    response_model=CitationContextResponse,
)
async def citation_context(
    chunk_id: uuid.UUID,
    _user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CitationContextResponse:
    context = await get_citation_context(session, chunk_id)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found",
        )
    return CitationContextResponse(
        passage=_to_response(context.passage),
        neighbors=[_to_response(neighbor) for neighbor in context.neighbors],
    )


def _to_response(passage: SourcePassage) -> PassageResponse:
    return PassageResponse(
        chunk_id=passage.chunk_id,
        document_id=passage.document_id,
        chunk_index=passage.chunk_index,
        text=passage.text,
        section=passage.section,
        company=passage.company,
        ticker=passage.ticker,
        form=passage.form,
        fiscal_year=passage.fiscal_year,
        filing_date=passage.filing_date,
        source_url=passage.source_url,
    )
