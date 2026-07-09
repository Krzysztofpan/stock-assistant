import json
from datetime import datetime
from app.services.conversation import ConversationService
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Query, Depends
from app.services.auth_service import auth_service
from app.events.conversation_event_bus import conversation_event_bus
from app.models.api import (
    ConversationsResponse,
    MessagesResponse,
    ConversationResponse,
    ConversationUpdateRequest,
)
from app.config import get_settings

from app.services.conversation.queries import (
    list_conversations, 
    list_messages, 
    get_conversation as get_conversation_query
)
from app.utils.pagination import DEFAULT_LIMIT
from app.models.auth import TokenPayload

from fastapi.responses import StreamingResponse

conversation_router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
    dependencies=[Depends(auth_service.verify_access_token)]
)

access_token_payload = Annotated[TokenPayload, Depends(auth_service.verify_access_token)]
settings = get_settings()

@conversation_router.get("/", response_model=ConversationsResponse)
async def get_conversations(
    access_token_payload: access_token_payload,
    before_updated_at: Optional[datetime] = None,
    before_id: Optional[UUID] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=settings.conversations_max_limit),
    ] = DEFAULT_LIMIT,
    query: Optional[str] = None,
    is_bookmarked: Optional[bool] = None,
) -> ConversationsResponse:
    return await list_conversations(
        user_id=access_token_payload.sub,
        limit=limit,
        before_updated_at=before_updated_at,
        before_id=str(before_id) if before_id else None,
        query=query,
        is_bookmarked=is_bookmarked
    )

@conversation_router.get("/events")
async def conversation_events(
    access_token_payload: access_token_payload,
):
    async def stream_events():
        async for event in conversation_event_bus.subscribe(access_token_payload.sub):
            event_type = event.get("type", "message")
            yield f"event: {event_type}\ndata: {json.dumps(event)}\n\n"

    return StreamingResponse(stream_events(), media_type="text/event-stream")
        

@conversation_router.get(
    "/{conversation_id}", 
    response_model=ConversationResponse
)
async def get_conversation(
    conversation_id: str,
    access_token_payload: access_token_payload,
    fields: Optional[str] = Query(None),
) -> ConversationResponse:
    parsed_fields = (
        [field.strip() for field in fields.split(",") if field.strip()]
        if fields
        else None
    )
    conversation = await get_conversation_query(
        conversation_id=conversation_id,
        user_id=access_token_payload.sub,
        fields=parsed_fields,
    )

    return ConversationResponse(conversation=conversation)

@conversation_router.get(
    "/{conversation_id}/messages",
    response_model=MessagesResponse,
)
async def get_conversation_messages(
    conversation_id: str,
    access_token_payload: access_token_payload,
    before_id: Optional[int] = None,
    limit: Annotated[int, Query(ge=1, le=settings.messages_max_limit)] = DEFAULT_LIMIT,
) -> MessagesResponse:
    return await list_messages(
        conversation_id,
        user_id=access_token_payload.sub,
        limit=limit,
        before_id=before_id,
    )

@conversation_router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: str,
    access_token_payload: access_token_payload,
    body: ConversationUpdateRequest,
) -> ConversationResponse:
    conversationService = await ConversationService.open(
        conversation_id=conversation_id,
        user_id=access_token_payload.sub,
    )

    updated_conversation: dict = {"id": conversation_id}

    if body.is_bookmarked is not None:
        updated_conversation["is_bookmarked"] = (
            await conversationService.update_conversation_bookmark(body.is_bookmarked)
        )

    if body.title is not None:
        updated_conversation["title"] = await conversationService.update_conversation_title(
            body.title,
        )

    return ConversationResponse(conversation=updated_conversation)

@conversation_router.delete(
    "/{conversation_id}"
)
async def delete_conversation(
    conversation_id: str,
    access_token_payload: access_token_payload,
):
    conversationService = await ConversationService.open(
        conversation_id=conversation_id,
        user_id=access_token_payload.sub,
    )

    await conversationService.delete_conversation()

    return {"conversation_id": conversation_id}