from app.services.conversation import ConversationService
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks,  Depends, Request
from app.services.auth_service import auth_service
from app.models.api import (
    ChatRequest,
    ChatResponse,
    CurrentUserDataResponse,
)
from app.config import get_settings
from app.dependencies import ChatServiceDep
from app.models.auth import TokenPayload
from app.core.security.rate_limit import limiter
from app.routes.conversation_routes import conversation_router

api_router = APIRouter(
    prefix="/api",
    tags=["api"],
    dependencies=[Depends(auth_service.verify_access_token)]
)
settings = get_settings()

access_token_payload = Annotated[TokenPayload, Depends(auth_service.verify_access_token)]

api_router.include_router(conversation_router)

@api_router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.rate_limit_for_question)
async def chat(
    request: Request,
    access_token_payload: access_token_payload,
    body: ChatRequest,
    background_tasks: BackgroundTasks,
    chat_service: ChatServiceDep,
) -> ChatResponse:
    response = await chat_service.handle(body, user_id=access_token_payload.sub)

    background_tasks.add_task(
        chat_service.summarize_conversation,
        body.conversation_id,
    )

    if body.new_conversation:
        conversation_service = ConversationService(body.conversation_id, access_token_payload.sub)

        background_tasks.add_task(
            conversation_service.create_conversation_title,
            body.message
        )
    return response
 
@api_router.get(
    "/me",
    response_model=CurrentUserDataResponse
) 
async def get_current_user_data(
    access_token_payload: access_token_payload
) -> CurrentUserDataResponse:
    user = await auth_service.get_current_user(access_token_payload.sub)
    return CurrentUserDataResponse(user=user)
