"""Runtime dependencies handed to the document agent per request."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.retrieval.retriever import DocumentRetriever


@dataclass
class DocumentAgentDeps:
    user_id: uuid.UUID
    thread_id: uuid.UUID
    retriever: DocumentRetriever
