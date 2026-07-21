"""Orchestrate ingest: convert -> chunk -> embed -> store, idempotently."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

import structlog

from ingest.conversion import Chunk, ConvertedFiling
from ingest.filings import Filing

logger = structlog.get_logger(__name__)


class Repository(Protocol):
    def find_document_id(self, accession_number: str) -> uuid.UUID | None: ...

    def replace_document(
        self,
        existing_id: uuid.UUID | None,
        filing: Filing,
        markdown: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        metadata: dict,
    ) -> uuid.UUID:
        """Atomically delete existing_id (if given) and store doc + chunks."""
        ...


@dataclass
class IngestReport:
    ingested: int = 0
    skipped: int = 0
    filings: list[str] = field(default_factory=list)


def ingest_filings(
    filings: list[Filing],
    convert: Callable[[Path], ConvertedFiling],
    embed: Callable[[list[str]], list[list[float]]],
    repository: Repository,
    force: bool = False,
) -> IngestReport:
    """Ingest filings; re-runs skip already-stored filings unless force=True."""
    report = IngestReport()

    for filing in filings:
        existing_id = repository.find_document_id(filing.accession_number)
        if existing_id is not None and not force:
            logger.info("ingest.skip_existing", accession=filing.accession_number)
            report.skipped += 1
            continue

        # Convert and embed before touching the DB so a failure here leaves
        # any previously ingested version of the filing intact.
        logger.info("ingest.convert", path=str(filing.path))
        converted = convert(filing.path)
        embeddings = embed([chunk.embed_text for chunk in converted.chunks])

        metadata = {
            "ticker": filing.ticker,
            "company": filing.company,
            "cik": filing.cik,
            "form": filing.form,
            "filing_date": filing.filing_date,
            "report_date": filing.report_date,
            "fiscal_year": filing.fiscal_year,
            "accession_number": filing.accession_number,
            "source_url": filing.source_url,
        }
        repository.replace_document(
            existing_id, filing, converted.markdown,
            converted.chunks, embeddings, metadata,
        )

        logger.info(
            "ingest.stored",
            accession=filing.accession_number,
            chunks=len(converted.chunks),
        )
        report.ingested += 1
        report.filings.append(filing.accession_number)

    return report
