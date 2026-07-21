"""Filing discovery from the local downloads directory + manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ingest.filings import discover_filings

MANIFEST = {
    "source": "SEC EDGAR",
    "form": "10-K",
    "filings": [
        {
            "ticker": "AAPL",
            "cik": "0000320193",
            "form": "10-K",
            "filing_date": "2021-10-29",
            "report_date": "2021-09-25",
            "accession_number": "0000320193-21-000105",
            "primary_document": "aapl-20210925.htm",
            "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm",
            "local_path": "2021/aapl_10-k_2021-10-29_0000320193-21-000105.htm",
        },
        {
            "ticker": "MSFT",
            "cik": "0000789019",
            "form": "10-K",
            "filing_date": "2022-07-28",
            "report_date": "2022-06-30",
            "accession_number": "0001564590-22-026876",
            "primary_document": "msft-10k_20220630.htm",
            "source_url": "https://www.sec.gov/Archives/edgar/data/789019/000156459022026876/msft-10k_20220630.htm",
            "local_path": "2022/msft_10-k_2022-07-28_0001564590-22-026876.htm",
        },
    ],
}


@pytest.fixture
def downloads_dir(tmp_path: Path) -> Path:
    (tmp_path / "manifest.json").write_text(json.dumps(MANIFEST))
    for filing in MANIFEST["filings"]:
        path = tmp_path / filing["local_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<html><body>10-K</body></html>")
    return tmp_path


def test_discovers_all_filings_with_citation_metadata(downloads_dir: Path):
    filings = discover_filings(downloads_dir)

    assert len(filings) == 2
    aapl = filings[0]
    assert aapl.ticker == "AAPL"
    assert aapl.company == "Apple Inc."
    assert aapl.form == "10-K"
    assert aapl.filing_date == "2021-10-29"
    assert aapl.fiscal_year == "2021"
    assert aapl.accession_number == "0000320193-21-000105"
    assert aapl.source_url.startswith("https://www.sec.gov/")
    assert aapl.path == downloads_dir / "2021/aapl_10-k_2021-10-29_0000320193-21-000105.htm"


def test_filters_by_year(downloads_dir: Path):
    filings = discover_filings(downloads_dir, years=["2022"])

    assert [f.ticker for f in filings] == ["MSFT"]


def test_skips_manifest_entries_whose_file_is_missing(downloads_dir: Path):
    (downloads_dir / "2022/msft_10-k_2022-07-28_0001564590-22-026876.htm").unlink()

    filings = discover_filings(downloads_dir)

    assert [f.ticker for f in filings] == ["AAPL"]


def test_skips_non_htm_artifacts(downloads_dir: Path):
    manifest = json.loads((downloads_dir / "manifest.json").read_text())
    manifest["filings"].append(
        {**MANIFEST["filings"][0], "local_path": "2021/notes.txt"}
    )
    (downloads_dir / "manifest.json").write_text(json.dumps(manifest))
    (downloads_dir / "2021/notes.txt").write_text("not a filing")

    filings = discover_filings(downloads_dir)

    assert len(filings) == 2


def test_missing_manifest_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        discover_filings(tmp_path)
