"""Chat thread persistence helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ChatThread, User


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
