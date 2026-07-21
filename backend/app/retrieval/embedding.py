"""Async query embedding for the request path (ingest uses the sync client)."""

from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings


def build_async_openai_client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for retrieval and chat.")
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


async def embed_query(client: AsyncOpenAI, query: str) -> list[float]:
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=[query],
        dimensions=settings.openai_embedding_dimensions,
    )
    return response.data[0].embedding
