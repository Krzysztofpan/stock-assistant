from datetime import datetime

from pydantic import BaseModel
from typing import Literal, Optional
from app.models.error import ErrorDetail
from app.tortoise.models.messages import MessageRole
from uuid import UUID
from pydantic import ConfigDict

class MessageItem(BaseModel):
    id: int
    role: MessageRole
    text: str
    created_at: datetime

class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    new_conversation: bool = False


class MessagesResponse(BaseModel):
    messages: list[MessageItem]
    has_more: bool

class ConversationItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_bookmarked: bool


class ConversationsResponse(BaseModel):
    conversations: list[ConversationItem]
    has_more: bool

class ConversationDetail(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_bookmarked: Optional[bool] = None


class ConversationResponse(BaseModel):
    conversation: ConversationDetail

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)    
    id: UUID
    name: str
    email: str

class CurrentUserDataResponse(BaseModel):
    user: UserPublic

class CheckResult(BaseModel):
    status: Literal["ok", "error"]
    latency_ms: Optional[int] = None
    detail: Optional[str] = None


class LiveResponse(BaseModel):
    status: Literal["ok"] = "ok"


class HealthyResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    checks: dict[str, CheckResult]

class ConversationBookmarkRequest(BaseModel):
    is_bookmarked: bool

class ConversationBookmarkResponse(BaseModel):
    is_bookmarked: bool