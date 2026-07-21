"""Chunk embeddings via the OpenAI SDK pointed at AvalAI."""

from __future__ import annotations

from openai import OpenAI

from app.config import settings
from app.database.models import EMBEDDING_DIMENSIONS

DEFAULT_BATCH_SIZE = 128


def build_openai_client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for ingest (AvalAI API key)."
        )
    if settings.openai_embedding_dimensions != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"OPENAI_EMBEDDING_DIMENSIONS={settings.openai_embedding_dimensions} "
            f"does not match the vector({EMBEDDING_DIMENSIONS}) column; "
            "a schema migration is required to change dimensions."
        )
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def embed_texts(
    client: OpenAI,
    texts: list[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[list[float]]:
    """Embed texts in order, batching requests to stay under API limits."""
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts[start : start + batch_size],
            dimensions=settings.openai_embedding_dimensions,
        )
        vectors.extend(item.embedding for item in response.data)
    return vectors
