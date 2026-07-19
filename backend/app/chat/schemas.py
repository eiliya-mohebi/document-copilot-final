"""Request/response models for chat HTTP boundaries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UIMessagePart(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    text: str | None = None


class UIMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    role: Literal["user", "assistant", "system"]
    parts: list[UIMessagePart] = Field(default_factory=list)


class ChatStreamRequest(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    thread_id: uuid.UUID = Field(alias="threadId")
    messages: list[UIMessage]


class ThreadCreateResponse(BaseModel):
    id: uuid.UUID
    title: str


class ThreadCreateRequest(BaseModel):
    title: str | None = None


class ThreadListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    title: str
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ThreadListResponse(BaseModel):
    threads: list[ThreadListItem]


class ThreadHistoryResponse(BaseModel):
    id: uuid.UUID
    title: str
    messages: list[UIMessage]
