"""Ingest downloaded SEC filings into Supabase.

Usage (from backend/):
    uv run python -m ingest.run                 # ingest everything new
    uv run python -m ingest.run --years 2021    # limit to fiscal years
    uv run python -m ingest.run --force         # re-ingest existing filings
    uv run python -m ingest.run --smoke "query" # ingest, then run a retrieval smoke
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from ingest.conversion import convert_filing
from ingest.embeddings import build_openai_client, embed_texts
from ingest.filings import discover_filings
from ingest.pipeline import ingest_filings
from ingest.repository import SqlRepository, build_sync_engine

DOWNLOADS_DIR = Path(__file__).resolve().parents[2] / "data" / "downloads"

SMOKE_QUERY_SQL = text(
    """
    SELECT c.text, c.section, c.metadata->>'company' AS company,
           c.metadata->>'fiscal_year' AS fiscal_year
    FROM document_chunks c
    ORDER BY c.embedding <=> CAST(:embedding AS vector)
    LIMIT 1
    """
)


def run_smoke(session: Session, client: OpenAI, query: str) -> None:
    embedding = embed_texts(client, [query])[0]
    row = session.execute(SMOKE_QUERY_SQL, {"embedding": str(embedding)}).first()
    if row is None:
        raise SystemExit("Smoke failed: no chunks found for query.")
    print(f"\nSmoke query: {query!r}")
    print(f"Top passage ({row.company}, FY{row.fiscal_year}, {row.section}):")
    print(row.text[:500])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="*", help="Fiscal years to ingest")
    parser.add_argument("--force", action="store_true", help="Re-ingest existing")
    parser.add_argument("--smoke", metavar="QUERY", help="Run a retrieval smoke test")
    args = parser.parse_args()

    filings = discover_filings(DOWNLOADS_DIR, years=args.years)
    print(f"Found {len(filings)} filing(s) in {DOWNLOADS_DIR}")

    client = build_openai_client()
    engine = build_sync_engine()

    with Session(engine) as session:
        report = ingest_filings(
            filings,
            convert=convert_filing,
            embed=lambda texts: embed_texts(client, texts),
            repository=SqlRepository(session),
            force=args.force,
        )
        print(f"Ingested {report.ingested}, skipped {report.skipped} (already stored)")

        if args.smoke:
            run_smoke(session, client, args.smoke)


if __name__ == "__main__":
    main()
