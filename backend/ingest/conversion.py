"""HTML filing -> DoclingDocument -> hybrid chunks.

Docling imports live inside functions: they pull heavy ML dependencies, and the
pipeline/unit tests only need the Chunk/ConvertedFiling data types.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    text: str
    # Contextualized text (headings prepended) — what gets embedded.
    embed_text: str
    section: str | None
    token_count: int


@dataclass(frozen=True)
class ConvertedFiling:
    markdown: str
    chunks: list[Chunk]


@lru_cache(maxsize=1)
def _converter():
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, HTMLFormatOption

    return DocumentConverter(
        allowed_formats=[InputFormat.HTML],
        format_options={InputFormat.HTML: HTMLFormatOption()},
    )


@lru_cache(maxsize=1)
def _chunker():
    from docling.chunking import HybridChunker
    from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
    import tiktoken

    from app.config import settings

    # Align the chunker's token budget with the embedding model's tokenizer so
    # chunk sizes are measured in the same units the embedding API bills/limits.
    tokenizer = OpenAITokenizer(
        tokenizer=tiktoken.encoding_for_model(settings.openai_embedding_model),
        max_tokens=1024,
    )
    return HybridChunker(tokenizer=tokenizer)


def convert_filing(path: Path) -> ConvertedFiling:
    """Convert one HTML filing into normalized Markdown + hybrid chunks."""
    document = _converter().convert(path).document
    chunker = _chunker()

    chunks = []
    for chunk in chunker.chunk(document):
        embed_text = chunker.contextualize(chunk)
        headings = chunk.meta.headings or []
        chunks.append(
            Chunk(
                text=chunk.text,
                embed_text=embed_text,
                section=" > ".join(headings) if headings else None,
                token_count=chunker.tokenizer.count_tokens(embed_text),
            )
        )

    return ConvertedFiling(markdown=document.export_to_markdown(), chunks=chunks)
