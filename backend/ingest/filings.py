"""Discover downloaded SEC filings from data/downloads + manifest.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
}


@dataclass(frozen=True)
class Filing:
    ticker: str
    company: str
    cik: str
    form: str
    filing_date: str
    report_date: str
    fiscal_year: str
    accession_number: str
    source_url: str
    path: Path


def discover_filings(
    downloads_dir: Path, years: list[str] | None = None
) -> list[Filing]:
    """Read manifest.json and return filings whose local file exists on disk."""
    manifest_path = downloads_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    filings = []
    for entry in manifest["filings"]:
        path = downloads_dir / entry["local_path"]
        fiscal_year = (entry["report_date"] or entry["filing_date"])[:4]
        if years is not None and fiscal_year not in years:
            continue
        if path.suffix.lower() != ".htm" or not path.is_file():
            continue
        filings.append(
            Filing(
                ticker=entry["ticker"],
                company=COMPANY_NAMES.get(entry["ticker"], entry["ticker"]),
                cik=entry["cik"],
                form=entry["form"],
                filing_date=entry["filing_date"],
                report_date=entry["report_date"],
                fiscal_year=fiscal_year,
                accession_number=entry["accession_number"],
                source_url=entry["source_url"],
                path=path,
            )
        )
    return filings
