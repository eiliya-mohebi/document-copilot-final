"""Docling conversion + hybrid chunking against a small local HTML fixture.

Marked integration: docling and tiktoken fetch tokenizer assets on first run.
"""

from __future__ import annotations

import pytest

pytest.importorskip("docling")

from ingest.conversion import convert_filing  # noqa: E402

FIXTURE_HTML = """
<html><body>
<h1>Item 1. Business</h1>
<p>The company designs consumer electronics and sells them worldwide.</p>
<h1>Item 7. Management's Discussion and Analysis</h1>
<p>Total net sales increased 8 percent year over year driven by services.</p>
<table>
  <tr><th>Segment</th><th>Revenue</th></tr>
  <tr><td>Products</td><td>100</td></tr>
  <tr><td>Services</td><td>50</td></tr>
</table>
</body></html>
"""


@pytest.mark.integration
def test_converts_html_to_markdown_and_hybrid_chunks(tmp_path):
    path = tmp_path / "sample_10-k.htm"
    path.write_text(FIXTURE_HTML)

    converted = convert_filing(path)

    assert "Item 1. Business" in converted.markdown
    assert converted.chunks, "expected at least one chunk"
    all_text = " ".join(chunk.text for chunk in converted.chunks)
    assert "net sales increased 8 percent" in all_text
    mdna = next(c for c in converted.chunks if "net sales" in c.text)
    assert mdna.section and "Item 7" in mdna.section
    assert mdna.embed_text.startswith(mdna.section.split(" > ")[0][:10])
    assert mdna.token_count > 0
