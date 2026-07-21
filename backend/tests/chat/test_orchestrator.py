"""Primary seam: one chat turn from user question to streamed grounded answer.

The agent/LLM boundary is faked via the `generate` callable; grounding
validation, streaming events, and persistence run for real.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.assistant.outputs import Citation, GroundedAnswer, SourcePassage
from app.chat.orchestrator import TurnResult, stream_chat_turn
from app.chat.schemas import UIMessage, UIMessagePart

THREAD_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
CHUNK_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000001")
DOC_ID = uuid.UUID("dddddddd-0000-0000-0000-000000000001")


def make_thread():
    return type("Thread", (), {"id": THREAD_ID, "title": "New chat"})()


def user_message(text: str = "How did Apple revenue grow in 2021?") -> UIMessage:
    return UIMessage(
        id="msg-1",
        role="user",
        parts=[UIMessagePart(type="text", text=text)],
    )


def passage() -> SourcePassage:
    return SourcePassage(
        chunk_id=CHUNK_ID,
        document_id=DOC_ID,
        chunk_index=3,
        text="Total net sales increased 33% or $91.3 billion during 2021.",
        section="Item 7",
        company="Apple Inc.",
        ticker="AAPL",
        form="10-K",
        fiscal_year="2021",
        filing_date="2021-10-29",
    )


def grounded_result() -> TurnResult:
    answer = GroundedAnswer(
        answer="Apple's net sales increased 33% in fiscal 2021 [1].",
        citations=[
            Citation(marker=1, chunk_id=CHUNK_ID, quote="increased 33%"),
        ],
    )
    return TurnResult(answer=answer, retrieved={CHUNK_ID: passage()})


async def collect_events(stream) -> list[dict | str]:
    events: list[dict | str] = []
    async for chunk in stream:
        for block in chunk.split("\n\n"):
            line = block.strip()
            if not line.startswith("data: "):
                continue
            payload = line.removeprefix("data: ").strip()
            events.append("[DONE]" if payload == "[DONE]" else json.loads(payload))
    return events


async def test_grounded_turn_streams_text_citations_and_persists() -> None:
    generate = AsyncMock(return_value=grounded_result())

    with patch(
        "app.chat.orchestrator.chat_store.append_turn", AsyncMock()
    ) as mock_append:
        events = await collect_events(
            stream_chat_turn(
                MagicMock(), make_thread(), user_message(), generate=generate
            )
        )

    assert events[-1] == "[DONE]"
    typed = [e for e in events if isinstance(e, dict)]
    types = [e["type"] for e in typed]
    assert types[0] == "start"
    assert "finish" in types

    deltas = "".join(e["delta"] for e in typed if e["type"] == "text-delta")
    assert deltas == "Apple's net sales increased 33% in fiscal 2021 [1]."

    citation_parts = [e for e in typed if e["type"] == "data-citations"]
    assert len(citation_parts) == 1
    citation = citation_parts[0]["data"][0]
    assert citation["marker"] == 1
    assert citation["chunkId"] == str(CHUNK_ID)
    assert citation["company"] == "Apple Inc."
    assert citation["fiscalYear"] == "2021"
    assert citation["excerpt"].startswith("Total net sales")

    mock_append.assert_awaited_once()
    kwargs = mock_append.await_args.kwargs
    assert kwargs["user_text"] == "How did Apple revenue grow in 2021?"
    assert kwargs["assistant_text"].startswith("Apple's net sales")
    part_types = [p["type"] for p in kwargs["assistant_parts"]]
    assert part_types == ["text", "data-citations"]
    assert kwargs["citations"][0]["chunk_id"] == CHUNK_ID
    assert kwargs["citations"][0]["marker"] == 1


async def test_ungrounded_citations_fail_closed_without_persisting() -> None:
    bogus = GroundedAnswer(
        answer="Confident but unsupported [1].",
        citations=[Citation(marker=1, chunk_id=uuid.uuid4())],
    )
    generate = AsyncMock(return_value=TurnResult(answer=bogus, retrieved={}))

    with patch(
        "app.chat.orchestrator.chat_store.append_turn", AsyncMock()
    ) as mock_append:
        events = await collect_events(
            stream_chat_turn(
                MagicMock(), make_thread(), user_message(), generate=generate
            )
        )

    typed = [e for e in events if isinstance(e, dict)]
    error_events = [e for e in typed if e["type"] == "error"]
    assert len(error_events) == 1
    assert "verify" in error_events[0]["errorText"].lower()
    assert events[-1] == "[DONE]"
    mock_append.assert_not_awaited()


async def test_insufficient_evidence_streams_refusal_and_persists() -> None:
    refusal = GroundedAnswer(
        answer="The corpus does not contain enough evidence to answer this.",
        citations=[],
        insufficient_evidence=True,
    )
    generate = AsyncMock(return_value=TurnResult(answer=refusal, retrieved={}))

    with patch(
        "app.chat.orchestrator.chat_store.append_turn", AsyncMock()
    ) as mock_append:
        events = await collect_events(
            stream_chat_turn(
                MagicMock(), make_thread(), user_message(), generate=generate
            )
        )

    typed = [e for e in events if isinstance(e, dict)]
    deltas = "".join(e["delta"] for e in typed if e["type"] == "text-delta")
    assert "does not contain enough evidence" in deltas
    assert not [e for e in typed if e["type"] == "data-citations"]

    kwargs = mock_append.await_args.kwargs
    assert kwargs["citations"] == []


async def test_refusal_with_stray_citations_streams_refusal_without_citations() -> None:
    # The model may set insufficient_evidence but still emit bogus citations;
    # they must be dropped rather than crash the stream or reach the client.
    refusal = GroundedAnswer(
        answer="The corpus does not contain enough evidence to answer this.",
        citations=[Citation(marker=1, chunk_id=uuid.uuid4())],
        insufficient_evidence=True,
    )
    generate = AsyncMock(return_value=TurnResult(answer=refusal, retrieved={}))

    with patch(
        "app.chat.orchestrator.chat_store.append_turn", AsyncMock()
    ) as mock_append:
        events = await collect_events(
            stream_chat_turn(
                MagicMock(), make_thread(), user_message(), generate=generate
            )
        )

    typed = [e for e in events if isinstance(e, dict)]
    assert not [e for e in typed if e["type"] == "data-citations"]
    assert not [e for e in typed if e["type"] == "error"]
    assert events[-1] == "[DONE]"
    assert mock_append.await_args.kwargs["citations"] == []


async def test_agent_failure_emits_error_event_without_persisting() -> None:
    generate = AsyncMock(side_effect=RuntimeError("upstream LLM exploded"))

    with patch(
        "app.chat.orchestrator.chat_store.append_turn", AsyncMock()
    ) as mock_append:
        events = await collect_events(
            stream_chat_turn(
                MagicMock(), make_thread(), user_message(), generate=generate
            )
        )

    typed = [e for e in events if isinstance(e, dict)]
    assert [e for e in typed if e["type"] == "error"]
    assert events[-1] == "[DONE]"
    mock_append.assert_not_awaited()
