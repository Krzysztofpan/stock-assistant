from typing import Annotated

from fastapi import Depends

from app.services.chat_service import ChatService

_chat_service: ChatService | None = None


def init_chat_service(service: ChatService) -> None:
    global _chat_service
    _chat_service = service


def reset_chat_service() -> None:
    global _chat_service
    _chat_service = None


def get_chat_service() -> ChatService:
    if _chat_service is None:
        raise RuntimeError("ChatService has not been initialized")
    return _chat_service


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
