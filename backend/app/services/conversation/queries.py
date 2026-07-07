from app.models.api import (
    ConversationItem,
    ConversationsResponse,
    MessageItem,
    MessagesResponse,
)

from app.utils.pagination import (
    DEFAULT_LIMIT,
    clamp_limit,
    fetch_page,
    validate_composite_cursor,
)
from app.config import get_settings
from app.errors.exceptions import AppError
from app.tortoise.models.conversation import Conversation
from app.tortoise.models.messages import Message
from datetime import datetime
from tortoise.expressions import Q
from typing import Optional
settings = get_settings()

CONVERSATION_RESPONSE_FIELDS = {
    "id",
    "title",
    "created_at",
    "updated_at",
    "is_bookmarked",
}

def normalize_fields(fields):
    allowed = CONVERSATION_RESPONSE_FIELDS

    if not fields:
        return list(allowed)

    invalid = set(fields) - allowed
    if invalid:
        raise AppError(
            f"Unexpected fields who's doesn't exist in conversation: {invalid}",
            status_code=400,
            user_message="Unexpected fields param",
        )

    return fields

async def get_conversation(
    conversation_id: str,
    user_id: str,
    fields: Optional[list[str]] = None,
) -> dict:
    normalized_fields = normalize_fields(fields)
    conversation = await Conversation.get_or_none(
        id=conversation_id,
        user_id=user_id,
    ).values(*normalized_fields)

    if not conversation:
        raise AppError(
            f"Unexpected conversation_id. Conversation not found: {conversation_id}",
            status_code=404,
            user_message="Conversation not found",
        )

    if "id" in conversation:
        conversation["id"] = str(conversation["id"])

    return conversation



async def list_conversations(
    user_id: str,
    *,
    limit: int = DEFAULT_LIMIT,
    before_updated_at: datetime | None = None,
    before_id: str | None = None,
    query: str | None = None,
    is_bookmarked: bool | None = None
) -> ConversationsResponse:
    limit = clamp_limit(limit, settings.conversations_max_limit)
    validate_composite_cursor(before_updated_at, before_id)

    filters = Q(user_id=user_id)
    if before_updated_at is not None and before_id is not None:
        filters &= Q(updated_at__lt=before_updated_at) | Q(
            updated_at=before_updated_at,
            id__lt=before_id,
        )
    
    if query is not None and len(query) > 0:
        filters &= Q(title__icontains=query)
    
    if is_bookmarked is not None:
        filters &= Q(is_bookmarked=is_bookmarked)

    page = await fetch_page(
        Conversation.filter(filters).order_by("-updated_at", "-id"),
        limit,
    )

    return ConversationsResponse(
        conversations=[
            ConversationItem(
                id=str(conversation.id),
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                is_bookmarked=conversation.is_bookmarked
            )
            for conversation in page.items
        ],
        has_more=page.has_more,
    )


async def list_messages(
    conversation_id: str,
    user_id: str,
    *,
    limit: int = DEFAULT_LIMIT,
    before_id: int | None = None,
) -> MessagesResponse:
    limit = clamp_limit(limit, settings.messages_max_limit)

    conversation = await Conversation.get_or_none(
        id=conversation_id,
        user_id=user_id,
    )
    if not conversation:
        """ raise AppError(
            f"Conversation {conversation_id} not found for user {user_id}",
            status_code=404,
            user_message="Conversation not found.",
        ) """
        return MessagesResponse(messages=[], has_more=False)

    filters: dict = {"conversation_id": conversation_id}
    if before_id:
        filters["id__lt"] = before_id

    page = await fetch_page(
        Message.filter(**filters).order_by("-id"),
        limit,
        reverse=True,
    )

    return MessagesResponse(
        messages=[
            MessageItem(
                id=message.id,
                role=message.role,
                text=message.text,
                created_at=message.created_at,
            )
            for message in page.items
        ],
        has_more=page.has_more,
    )

