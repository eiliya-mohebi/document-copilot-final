"""Idempotent ingest orchestration: convert -> chunk -> embed -> store."""

from __future__ import annotations

import uuid
from pathlib import Path

from ingest.conversion import Chunk, ConvertedFiling
from ingest.filings import Filing
from ingest.pipeline import ingest_filings

FILING = Filing(
    ticker="AAPL",
    company="Apple Inc.",
    cik="0000320193",
    form="10-K",
    filing_date="2021-10-29",
    report_date="2021-09-25",
    fiscal_year="2021",
    accession_number="0000320193-21-000105",
    source_url="https://www.sec.gov/example.htm",
    path=Path("/tmp/aapl.htm"),
)

CONVERTED = ConvertedFiling(
    markdown="# Apple 10-K\n\nRevenue grew.",
    chunks=[
        Chunk(
            text="Revenue grew.",
            embed_text="Item 7. MD&A\nRevenue grew.",
            section="Item 7. MD&A",
            token_count=7,
        ),
        Chunk(
            text="Risk factors exist.",
            embed_text="Item 1A. Risk Factors\nRisk factors exist.",
            section="Item 1A. Risk Factors",
            token_count=8,
        ),
    ],
)


class FakeRepository:
    def __init__(self):
        self.documents: dict[str, dict] = {}
        self.chunks: dict[uuid.UUID, list[dict]] = {}

    def find_document_id(self, accession_number: str) -> uuid.UUID | None:
        doc = self.documents.get(accession_number)
        return doc["id"] if doc else None

    def replace_document(
        self, existing_id, filing: Filing, markdown, chunks, embeddings, metadata
    ) -> uuid.UUID:
        if existing_id is not None:
            for accession, doc in list(self.documents.items()):
                if doc["id"] == existing_id:
                    del self.documents[accession]
            self.chunks.pop(existing_id, None)

        document_id = uuid.uuid4()
        self.documents[filing.accession_number] = {
            "id": document_id,
            "filing": filing,
            "markdown": markdown,
        }
        self.chunks[document_id] = [
            {
                "index": i,
                "chunk": chunk,
                "embedding": embedding,
                "metadata": metadata,
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]
        return document_id


def fake_convert(path: Path) -> ConvertedFiling:
    return CONVERTED


def fake_embed(texts: list[str]) -> list[list[float]]:
    return [[float(len(t))] * 3 for t in texts]


def test_ingest_stores_document_and_chunks_with_metadata():
    repo = FakeRepository()

    report = ingest_filings([FILING], fake_convert, fake_embed, repo)

    assert report.ingested == 1
    assert report.skipped == 0
    doc = repo.documents["0000320193-21-000105"]
    assert doc["markdown"] == CONVERTED.markdown
    stored = repo.chunks[doc["id"]]
    assert len(stored) == 2
    assert stored[0]["chunk"].text == "Revenue grew."
    # Embeddings are computed from the contextualized text, not the raw text.
    assert stored[0]["embedding"] == [float(len("Item 7. MD&A\nRevenue grew."))] * 3
    assert stored[0]["metadata"]["ticker"] == "AAPL"
    assert stored[0]["metadata"]["company"] == "Apple Inc."
    assert stored[0]["metadata"]["form"] == "10-K"
    assert stored[0]["metadata"]["fiscal_year"] == "2021"
    assert stored[0]["metadata"]["accession_number"] == "0000320193-21-000105"


def test_rerun_skips_already_ingested_filing():
    repo = FakeRepository()
    ingest_filings([FILING], fake_convert, fake_embed, repo)
    first_id = repo.documents["0000320193-21-000105"]["id"]

    report = ingest_filings([FILING], fake_convert, fake_embed, repo)

    assert report.ingested == 0
    assert report.skipped == 1
    assert repo.documents["0000320193-21-000105"]["id"] == first_id


def test_force_replaces_existing_document():
    repo = FakeRepository()
    ingest_filings([FILING], fake_convert, fake_embed, repo)
    first_id = repo.documents["0000320193-21-000105"]["id"]

    report = ingest_filings([FILING], fake_convert, fake_embed, repo, force=True)

    assert report.ingested == 1
    new_id = repo.documents["0000320193-21-000105"]["id"]
    assert new_id != first_id
    assert first_id not in repo.chunks
    assert len(repo.chunks[new_id]) == 2


def test_failed_conversion_leaves_existing_document_intact():
    repo = FakeRepository()
    ingest_filings([FILING], fake_convert, fake_embed, repo)
    first_id = repo.documents["0000320193-21-000105"]["id"]

    def broken_convert(path: Path) -> ConvertedFiling:
        raise RuntimeError("docling exploded")

    import pytest

    with pytest.raises(RuntimeError, match="docling exploded"):
        ingest_filings([FILING], broken_convert, fake_embed, repo, force=True)

    assert repo.documents["0000320193-21-000105"]["id"] == first_id
    assert len(repo.chunks[first_id]) == 2
