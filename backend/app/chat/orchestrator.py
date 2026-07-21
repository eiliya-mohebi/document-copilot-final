"""One chat turn end-to-end: generate, validate grounding, stream, persist."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from functools import partial
from typing import AsyncIterator, Awaitable, Callable

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.agent import build_model, document_agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer, SourcePassage
from app.chat.messages import ui_message_parts, ui_message_text
from app.chat.schemas import UIMessage
from app.chat.streaming import sse_event, split_deltas
from app.database import chats as chat_store
from app.database.models import ChatThread
from app.grounding.validator import GroundingError, validate_grounding
from app.retrieval.embedding import build_async_openai_client, embed_query
from app.retrieval.retriever import DocumentRetriever

logger = structlog.get_logger(__name__)

GROUNDING_FAILURE_TEXT = (
    "The assistant could not verify its citations against the retrieved "
    "filings, so the answer was withheld. Please try rephrasing the question."
)
UPSTREAM_FAILURE_TEXT = (
    "The assistant failed to produce an answer due to an upstream error. "
    "Please try again."
)


@dataclass
class TurnResult:
    """What the agent produced plus everything it retrieved along the way."""

    answer: GroundedAnswer
    retrieved: dict[uuid.UUID, SourcePassage]


GenerateFn = Callable[[str], Awaitable[TurnResult]]


async def generate_grounded_answer(
    session: AsyncSession,
    thread: ChatThread,
    question: str,
) -> TurnResult:
    """Run the real document agent over the corpus for one question."""
    client = build_async_openai_client()
    retriever = DocumentRetriever(session, partial(embed_query, client))
    deps = DocumentAgentDeps(
        user_id=thread.user_id,
        thread_id=thread.id,
        retriever=retriever,
    )
    result = await document_agent.run(question, model=build_model(), deps=deps)
    return TurnResult(answer=result.output, retrieved=retriever.retrieved)


def _build_citations(
    answer: GroundedAnswer,
    retrieved: dict[uuid.UUID, SourcePassage],
) -> tuple[list[dict], list[dict]]:
    """Return (wire payload, DB records) for the answer's validated citations.

    A refusal (insufficient_evidence) carries no citations even if the model
    emitted stray ones; grounding validation already vouched for the rest.
    """
    if answer.insufficient_evidence:
        return [], []

    payload: list[dict] = []
    records: list[dict] = []
    for citation in sorted(answer.citations, key=lambda c: c.marker):
        passage = retrieved[citation.chunk_id]
        item = {
            "marker": citation.marker,
            "chunkId": str(citation.chunk_id),
            "documentId": str(passage.document_id),
            "quote": citation.quote,
            "company": passage.company,
            "ticker": passage.ticker,
            "form": passage.form,
            "fiscalYear": passage.fiscal_year,
            "filingDate": passage.filing_date,
            "section": passage.section,
            "sourceUrl": passage.source_url,
            "excerpt": passage.text,
        }
        payload.append(item)
        records.append(
            {
                "chunk_id": citation.chunk_id,
                "document_id": passage.document_id,
                "marker": citation.marker,
                "quote": citation.quote,
                "source": item,
            }
        )
    return payload, records


def _build_refusal(answer: GroundedAnswer) -> dict | None:
    reasons: list[str] = []
    if answer.insufficient_evidence:
        reasons.append("insufficient_evidence")
    if answer.declined_advice:
        reasons.append("no_advice")
    if not reasons:
        return None
    return {"reasons": reasons}


async def stream_chat_turn(
    session: AsyncSession,
    thread: ChatThread,
    user_message: UIMessage,
    *,
    generate: GenerateFn | None = None,
) -> AsyncIterator[str]:
    """Yield AI SDK UI message stream SSE chunks for one grounded turn.

    Grounding is validated before any answer text is streamed, so an
    unsupported answer never reaches the client (fail closed). Persistence
    happens only after a successful grounded run.
    """
    if generate is None:
        generate = partial(generate_grounded_answer, session, thread)

    question = ui_message_text(user_message)
    yield sse_event({"type": "start", "messageId": f"msg_{uuid.uuid4().hex}"})

    try:
        result = await generate(question)
        validate_grounding(result.answer, result.retrieved)
    except GroundingError as exc:
        logger.warning("chat.grounding_failed", thread_id=str(thread.id), error=str(exc))
        yield sse_event({"type": "error", "errorText": GROUNDING_FAILURE_TEXT})
        yield sse_event({"type": "finish"})
        yield sse_event("[DONE]")
        return
    # Blanket catch is deliberate: the SSE response has already started, so
    # the only way to surface any failure (LLM, retrieval, bugs) to the
    # client is an error event on the stream — a raised exception would just
    # sever the connection with no explanation.
    except Exception:
        logger.exception("chat.turn_failed", thread_id=str(thread.id))
        yield sse_event({"type": "error", "errorText": UPSTREAM_FAILURE_TEXT})
        yield sse_event({"type": "finish"})
        yield sse_event("[DONE]")
        return

    answer = result.answer
    text_id = f"text_{uuid.uuid4().hex}"
    yield sse_event({"type": "text-start", "id": text_id})
    for delta in split_deltas(answer.answer):
        yield sse_event({"type": "text-delta", "id": text_id, "delta": delta})
    yield sse_event({"type": "text-end", "id": text_id})

    citation_payload, citation_records = _build_citations(answer, result.retrieved)
    refusal_payload = _build_refusal(answer)
    assistant_parts: list[dict] = [{"type": "text", "text": answer.answer}]
    if refusal_payload:
        yield sse_event({"type": "data-refusal", "data": refusal_payload})
        assistant_parts.append({"type": "data-refusal", "data": refusal_payload})
    if citation_payload:
        yield sse_event({"type": "data-citations", "data": citation_payload})
        assistant_parts.append({"type": "data-citations", "data": citation_payload})

    try:
        await chat_store.append_turn(
            session,
            thread.id,
            user_text=question,
            user_parts=ui_message_parts(user_message),
            assistant_text=answer.answer,
            assistant_parts=assistant_parts,
            citations=citation_records,
        )
    except Exception:
        logger.exception("chat.persist_failed", thread_id=str(thread.id))
        yield sse_event(
            {
                "type": "error",
                "errorText": "The answer could not be saved to this thread.",
            }
        )

    yield sse_event({"type": "finish"})
    yield sse_event("[DONE]")
