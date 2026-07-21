"""Opt-in live test: real agent + retrieval + grounding against Supabase/LLM.

Run with: uv run pytest -m integration tests/chat/test_orchestrator_integration.py
Requires live DATABASE_URL and OPENAI_API_KEY plus an ingested corpus.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.chat.orchestrator import generate_grounded_answer
from app.config import settings
from app.grounding.validator import validate_grounding

pytestmark = pytest.mark.integration


class _FakeThread:
    id = uuid.uuid4()
    user_id = uuid.uuid4()


async def test_live_turn_produces_grounded_cited_answer() -> None:
    engine = create_async_engine(settings.async_database_url)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with maker() as session:
            result = await generate_grounded_answer(
                session,
                _FakeThread(),
                "How did Apple's revenue grow in fiscal 2021?",
            )
    finally:
        await engine.dispose()

    assert not result.answer.insufficient_evidence
    assert result.answer.citations
    cited = validate_grounding(result.answer, result.retrieved)
    assert cited
    assert all(p.chunk_id in result.retrieved for p in cited)
