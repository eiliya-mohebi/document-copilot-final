"""Typed outputs shared by retrieval, the agent, and grounding validation."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class SourcePassage(BaseModel):
    """A retrieved chunk plus the filing metadata needed to cite it."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    section: str | None = None
    company: str = ""
    ticker: str = ""
    form: str = ""
    fiscal_year: str = ""
    filing_date: str = ""
    source_url: str = ""


class Citation(BaseModel):
    """A claim-level reference to one retrieved passage."""

    marker: int = Field(description="1-based citation number as used in the answer text, e.g. [1]")
    chunk_id: uuid.UUID = Field(description="chunk_id of the retrieved passage that supports the claim")
    quote: str | None = Field(
        default=None,
        description="Short verbatim excerpt from the passage that supports the claim",
    )


class GroundedAnswer(BaseModel):
    """The agent's typed answer; grounding is enforced after generation."""

    answer: str = Field(description="Answer text with [n] citation markers, or an explanation that the corpus lacks evidence")
    citations: list[Citation] = Field(default_factory=list)
    insufficient_evidence: bool = Field(
        default=False,
        description="True when the retrieved passages cannot support an answer",
    )
    declined_advice: bool = Field(
        default=False,
        description="True when the question asked for stock picks or investment advice and that request was declined",
    )
