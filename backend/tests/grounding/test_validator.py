"""Grounding seam: citations must map to retrieved passages; fail closed."""

from __future__ import annotations

import uuid

import pytest

from app.assistant.outputs import Citation, GroundedAnswer, SourcePassage
from app.grounding.validator import GroundingError, validate_grounding

CHUNK_A = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
CHUNK_B = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002")
DOC_ID = uuid.UUID("dddddddd-0000-0000-0000-000000000001")


def passage(chunk_id: uuid.UUID) -> SourcePassage:
    return SourcePassage(
        chunk_id=chunk_id,
        document_id=DOC_ID,
        chunk_index=0,
        text="Net sales increased 33% in fiscal 2021.",
        company="Apple Inc.",
        ticker="AAPL",
        form="10-K",
        fiscal_year="2021",
        filing_date="2021-10-29",
    )


def test_valid_citations_return_cited_passages_in_marker_order() -> None:
    retrieved = {CHUNK_A: passage(CHUNK_A), CHUNK_B: passage(CHUNK_B)}
    answer = GroundedAnswer(
        answer="Revenue grew [1] and margins expanded [2].",
        citations=[
            Citation(marker=2, chunk_id=CHUNK_B),
            Citation(marker=1, chunk_id=CHUNK_A),
        ],
    )

    cited = validate_grounding(answer, retrieved)

    assert [p.chunk_id for p in cited] == [CHUNK_A, CHUNK_B]


def test_citation_to_non_retrieved_chunk_fails_closed() -> None:
    retrieved = {CHUNK_A: passage(CHUNK_A)}
    answer = GroundedAnswer(
        answer="Something confident [1].",
        citations=[Citation(marker=1, chunk_id=CHUNK_B)],
    )

    with pytest.raises(GroundingError):
        validate_grounding(answer, retrieved)


def test_answer_without_citations_fails_unless_insufficient_evidence() -> None:
    retrieved = {CHUNK_A: passage(CHUNK_A)}
    polished_but_unsupported = GroundedAnswer(answer="Trust me.", citations=[])

    with pytest.raises(GroundingError):
        validate_grounding(polished_but_unsupported, retrieved)


def test_insufficient_evidence_answer_needs_no_citations() -> None:
    answer = GroundedAnswer(
        answer="The corpus does not contain enough evidence to answer this.",
        citations=[],
        insufficient_evidence=True,
    )

    assert validate_grounding(answer, {}) == []


def test_duplicate_chunk_citations_return_passage_once() -> None:
    retrieved = {CHUNK_A: passage(CHUNK_A)}
    answer = GroundedAnswer(
        answer="Claim one [1]. Claim two [2].",
        citations=[
            Citation(marker=1, chunk_id=CHUNK_A),
            Citation(marker=2, chunk_id=CHUNK_A),
        ],
    )

    cited = validate_grounding(answer, retrieved)

    assert [p.chunk_id for p in cited] == [CHUNK_A]
