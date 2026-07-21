"""PydanticAI document agent: bounded tools over the corpus, typed output."""

from __future__ import annotations

import uuid
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer, SourcePassage
from app.config import settings

INSTRUCTIONS = (Path(__file__).parent / "instructions.md").read_text(encoding="utf-8")

document_agent = Agent(
    deps_type=DocumentAgentDeps,
    output_type=GroundedAnswer,
    instructions=INSTRUCTIONS,
    retries=2,
)


def build_model() -> OpenAIChatModel:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to run the document agent.")
    return OpenAIChatModel(
        settings.openai_chat_model,
        provider=OpenAIProvider(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
        ),
    )


def _passage_for_model(passage: SourcePassage) -> dict:
    return {
        "chunk_id": str(passage.chunk_id),
        "document_id": str(passage.document_id),
        "chunk_index": passage.chunk_index,
        "company": passage.company,
        "ticker": passage.ticker,
        "form": passage.form,
        "fiscal_year": passage.fiscal_year,
        "filing_date": passage.filing_date,
        "section": passage.section,
        "text": passage.text,
    }


@document_agent.tool
async def search_filings(ctx: RunContext[DocumentAgentDeps], query: str) -> list[dict]:
    """Hybrid-search the SEC filing corpus and return the best-matching passages."""
    passages = await ctx.deps.retriever.search(query)
    return [_passage_for_model(p) for p in passages]


@document_agent.tool
async def read_chunk(ctx: RunContext[DocumentAgentDeps], chunk_id: str) -> list[dict]:
    """Re-read a specific passage by its chunk_id."""
    passages = await ctx.deps.retriever.read_chunks([uuid.UUID(chunk_id)])
    return [_passage_for_model(p) for p in passages]


@document_agent.tool
async def read_surrounding_chunks(
    ctx: RunContext[DocumentAgentDeps],
    document_id: str,
    chunk_index: int,
) -> list[dict]:
    """Read the passages immediately before and after a chunk in the same filing."""
    passages = await ctx.deps.retriever.neighbors(
        uuid.UUID(document_id), chunk_index=chunk_index, window=1
    )
    return [_passage_for_model(p) for p in passages]
