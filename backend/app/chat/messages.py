"""Convert between persisted chat rows and AI SDK UI messages."""

from __future__ import annotations

from app.chat.schemas import UIMessage, UIMessagePart
from app.database.models import ChatMessage


def ui_message_text(message: UIMessage) -> str:
    return "".join(
        part.text for part in message.parts if part.type == "text" and part.text
    )


def ui_message_parts(message: UIMessage) -> list[dict]:
    return [part.model_dump(exclude_none=True) for part in message.parts]


def message_to_ui(message: ChatMessage) -> UIMessage:
    raw_parts = message.parts if isinstance(message.parts, list) else []
    parts = [UIMessagePart.model_validate(part) for part in raw_parts]
    return UIMessage(id=str(message.id), role=message.role, parts=parts)
