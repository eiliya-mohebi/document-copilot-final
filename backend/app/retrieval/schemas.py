"""Request/response models for citation-context HTTP boundaries."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class PassageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    chunk_id: uuid.UUID = Field(serialization_alias="chunkId")
    document_id: uuid.UUID = Field(serialization_alias="documentId")
    chunk_index: int = Field(serialization_alias="chunkIndex")
    text: str
    section: str | None = None
    company: str
    ticker: str
    form: str
    fiscal_year: str = Field(serialization_alias="fiscalYear")
    filing_date: str = Field(serialization_alias="filingDate")
    source_url: str = Field(serialization_alias="sourceUrl")


class CitationContextResponse(BaseModel):
    passage: PassageResponse
    neighbors: list[PassageResponse]
