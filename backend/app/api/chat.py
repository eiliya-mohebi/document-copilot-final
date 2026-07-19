"""Chat thread and streaming routes."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat.schemas import ChatStreamRequest, ThreadCreateRequest, ThreadCreateResponse
from app.chat.streaming import STUB_REPLY, stub_ui_message_stream
from app.database import chats as chat_store
from app.database.session import get_session

router = APIRouter(tags=["chat"])

_UI_STREAM_HEADERS = {
    "x-vercel-ai-ui-message-stream": "v1",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


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


@router.post("/chat/stream")
async def chat_stream(
    body: ChatStreamRequest,
    user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    thread = await chat_store.get_thread_for_user(session, body.thread_id, user.id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    return StreamingResponse(
        stub_ui_message_stream(STUB_REPLY),
        media_type="text/event-stream",
        headers=_UI_STREAM_HEADERS,
    )
