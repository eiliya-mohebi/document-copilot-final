"""Synchronous DB writes for the offline ingest script."""

from __future__ import annotations

import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import DocumentChunk, SourceDocument
from ingest.conversion import Chunk
from ingest.filings import Filing


def build_sync_engine():
    # Reuse the async URL normalization, then run psycopg synchronously.
    url = settings.async_database_url
    return create_engine(url, pool_pre_ping=True)


class SqlRepository:
    def __init__(self, session: Session):
        self._session = session

    def find_document_id(self, accession_number: str) -> uuid.UUID | None:
        return self._session.scalar(
            select(SourceDocument.id).where(
                SourceDocument.accession_number == accession_number
            )
        )

    def replace_document(
        self,
        existing_id: uuid.UUID | None,
        filing: Filing,
        markdown: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict,
    ) -> uuid.UUID:
        """Delete + reinsert in one transaction so a failure keeps the old doc."""
        if existing_id is not None:
            existing = self._session.get(SourceDocument, existing_id)
            if existing is not None:
                self._session.delete(existing)

        document = SourceDocument(
            ticker=filing.ticker,
            company=filing.company,
            form=filing.form,
            filing_date=filing.filing_date,
            fiscal_year=filing.fiscal_year,
            accession_number=filing.accession_number,
            source_url=filing.source_url,
            markdown=markdown,
        )
        self._session.add(document)
        self._session.flush()

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings, strict=True)
        ):
            self._session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    text=chunk.text,
                    section=chunk.section,
                    token_count=chunk.token_count,
                    embedding=embedding,
                    doc_metadata=metadata,
                )
            )
        self._session.commit()
        return document.id
