"""Chat thread persistence helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ChatMessage, ChatThread, User


async def ensure_user(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    email: str,
) -> User:
    user = await session.get(User, user_id)
    if user is not None:
        if user.email != email:
            user.email = email
        return user

    user = User(id=user_id, email=email)
    session.add(user)
    await session.flush()
    return user


async def create_thread(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    email: str,
    title: str = "New chat",
) -> ChatThread:
    await ensure_user(session, user_id=user_id, email=email)
    thread = ChatThread(user_id=user_id, title=title)
    session.add(thread)
    await session.commit()
    await session.refresh(thread)
    return thread


async def get_thread_for_user(
    session: AsyncSession,
    thread_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ChatThread | None:
    result = await session.execute(
        select(ChatThread).where(
            ChatThread.id == thread_id,
            ChatThread.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_threads_for_user(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[ChatThread]:
    result = await session.execute(
        select(ChatThread)
        .where(ChatThread.user_id == user_id)
        .order_by(ChatThread.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_thread_by_id(
    session: AsyncSession,
    thread_id: uuid.UUID,
) -> ChatThread | None:
    return await session.get(ChatThread, thread_id)


async def list_messages_for_thread(
    session: AsyncSession,
    thread_id: uuid.UUID,
) -> list[ChatMessage]:
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.sequence_number.asc())
    )
    return list(result.scalars().all())


async def delete_thread(session: AsyncSession, thread: ChatThread) -> None:
    await session.delete(thread)
    await session.commit()


async def append_turn(
    session: AsyncSession,
    thread_id: uuid.UUID,
    *,
    user_text: str,
    user_parts: list[dict[str, Any]],
    assistant_text: str,
) -> None:
    result = await session.execute(
        select(func.coalesce(func.max(ChatMessage.sequence_number), 0)).where(
            ChatMessage.thread_id == thread_id
        )
    )
    next_sequence = int(result.scalar_one()) + 1

    session.add(
        ChatMessage(
            thread_id=thread_id,
            role="user",
            content=user_text or None,
            parts=user_parts,
            sequence_number=next_sequence,
        )
    )
    session.add(
        ChatMessage(
            thread_id=thread_id,
            role="assistant",
            content=assistant_text,
            parts=[{"type": "text", "text": assistant_text}],
            sequence_number=next_sequence + 1,
        )
    )

    thread = await session.get(ChatThread, thread_id)
    if thread is not None:
        thread.updated_at = datetime.now(timezone.utc)

    await session.commit()
