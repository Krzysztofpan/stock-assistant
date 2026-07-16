from app.services.conversation import ConversationService
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks,  Depends, Request
from fastapi.responses import StreamingResponse
from app.services.auth_service import auth_service
from app.models.api import (
    ChatRequest,
    CurrentUserDataResponse,
)
from app.config import get_settings
from app.dependencies import ChatServiceDep
from app.models.auth import TokenPayload
from app.core.security.rate_limit import limiter
from app.routes.conversation_routes import conversation_router
import json

api_router = APIRouter(
    prefix="/api",
    tags=["api"],
    dependencies=[Depends(auth_service.verify_access_token)]
)
settings = get_settings()

access_token_payload = Annotated[TokenPayload, Depends(auth_service.verify_access_token)]

async def _create_conversation_title(
    conversation_id: str,
    user_id: str,
    first_message: str,
) -> None:
    service = await ConversationService.open(conversation_id, user_id)
    await service.create_conversation_title(first_message)

api_router.include_router(conversation_router)

@api_router.post("/chat/stream")
@limiter.limit(settings.rate_limit_for_question)
async def chat_stream(
    request: Request,
    access_token_payload: access_token_payload,
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    chat_service: ChatServiceDep,
):
    async def event_generator():
        async for event in chat_service.handle_stream(body, user_id=access_token_payload.sub):
            yield (
                f"event: {event['type']}\n"
                f"data: {json.dumps(event['data'])}\n\n"
            )

        background_tasks.add_task(
            chat_service.summarize_conversation,
            body.conversation_id,
        )

        if body.new_conversation:
            background_tasks.add_task(
                _create_conversation_title,
                body.conversation_id,
                access_token_payload.sub,
                body.message,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@api_router.get(
    "/me",
    response_model=CurrentUserDataResponse
) 
async def get_current_user_data(
    access_token_payload: access_token_payload
) -> CurrentUserDataResponse:
    user = await auth_service.get_current_user(access_token_payload.sub)
    return CurrentUserDataResponse(user=user)
