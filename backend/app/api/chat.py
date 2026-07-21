"""Chat thread and streaming routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat.messages import message_to_ui
from app.chat.schemas import (
    ChatStreamRequest,
    ThreadCreateRequest,
    ThreadCreateResponse,
    ThreadHistoryResponse,
    ThreadListItem,
    ThreadListResponse,
)
from app.chat.orchestrator import stream_chat_turn
from app.database import chats as chat_store
from app.database.session import get_session

router = APIRouter(tags=["chat"])

_UI_STREAM_HEADERS = {
    "x-vercel-ai-ui-message-stream": "v1",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadListResponse:
    threads = await chat_store.list_threads_for_user(session, user.id)
    return ThreadListResponse(
        threads=[
            ThreadListItem(id=thread.id, title=thread.title, updated_at=thread.updated_at)
            for thread in threads
        ]
    )


@router.post(
    "/threads",
    response_model=ThreadCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(
    body: ThreadCreateRequest = Body(default_factory=ThreadCreateRequest),
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadCreateResponse:
    title = body.title or "New chat"
    thread = await chat_store.create_thread(
        session,
        user.id,
        email=user.email,
        title=title,
    )
    return ThreadCreateResponse(id=thread.id, title=thread.title)


@router.get("/threads/{thread_id}", response_model=ThreadHistoryResponse)
async def get_thread(
    thread_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadHistoryResponse:
    thread = await chat_store.get_thread_by_id(session, thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    messages = await chat_store.list_messages_for_thread(session, thread_id)
    return ThreadHistoryResponse(
        id=thread.id,
        title=thread.title,
        messages=[message_to_ui(message) for message in messages],
    )


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    thread = await chat_store.get_thread_by_id(session, thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    await chat_store.delete_thread(session, thread)


@router.post("/chat/stream")
async def chat_stream(
    body: ChatStreamRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    thread = await chat_store.get_thread_by_id(session, body.thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    if thread.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    user_message = next(
        (message for message in reversed(body.messages) if message.role == "user"),
        None,
    )
    if user_message is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Expected a user message",
        )

    return StreamingResponse(
        stream_chat_turn(session, thread, user_message),
        media_type="text/event-stream",
        headers=_UI_STREAM_HEADERS,
    )
