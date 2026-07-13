from typing import Annotated

from fastapi import Depends

from app.container import get_chat_service
from app.services.chat_service import ChatService

ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]

__all__ = ["ChatServiceDep", "get_chat_service"]
