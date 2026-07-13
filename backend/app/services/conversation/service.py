from datetime import datetime, timezone

from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.core.security.PII_detector import get_pii_detector
from app.events.conversation_event_bus import conversation_event_bus
from app.errors.exceptions import AppError
from app.errors.mapping import classify_exception
from app.tortoise.models.conversation import Conversation
settings = get_settings()


class ConversationService:
    """Operacje na jednej konwersacji w flow czatu."""

    def __init__(self, conversation_id: str, user_id: str):
        self._conversation_id = conversation_id
        self._user_id = user_id
        self._conversation: Conversation | None = None

    @property
    def conversation(self) -> Conversation:
        if self._conversation is None:
            raise AppError(
                "Conversation service is not bound to an owned conversation.",
                status_code=500,
                user_message="Internal server error.",
            )
        return self._conversation

    @classmethod
    async def open(cls, conversation_id: str, user_id: str) -> "ConversationService":
        service = cls(conversation_id, user_id)
        await service._bind()
        return service

    async def _bind(self, *, allow_missing: bool = False) -> None:
        conversation = await Conversation.get_or_none(
            id=self._conversation_id,
            user_id=self._user_id,
        )
        if conversation is not None:
            self._conversation = conversation
            return

        if await Conversation.exists(id=self._conversation_id):
            raise AppError(
                f"Conversation {self._conversation_id} not found for user {self._user_id}",
                status_code=404,
                user_message="Conversation not found.",
            )

        if not allow_missing:
            raise AppError(
                f"Conversation {self._conversation_id} not found for user {self._user_id}",
                status_code=404,
                user_message="Conversation not found.",
            )

    async def ensure_exists(self) -> None:
        await self._bind(allow_missing=True)
        if self._conversation is not None:
            return

        self._conversation = await Conversation.create(
            id=self._conversation_id,
            user_id=self._user_id,
            title="New Conversation",
        )

    async def create_conversation_title(self, first_message: str):
        try:
            safe_message = get_pii_detector().mask(first_message)
            llm = ChatOpenAI(model=settings.cheap_llm_model, temperature=0.5)
            prompt = f"""
            Based on first user question, create conversation title based on first user question, use only few words, remember that you are in the
            finance context, so don't change english business name to other country word for example Apple. 
            Rember to generate title in the same language as user input
            
            question: {safe_message}
            """
            res = await llm.ainvoke(prompt)
            self.conversation.title = res.content
            await self.conversation.save()

            await conversation_event_bus.publish(self._user_id, {
                "type": "conversation.title_updated",
                "conversation_id": self._conversation_id,
                "title": res.content
            })
        except AppError:
            raise
        except Exception as e:
            classified = classify_exception(e, context="create_conversation_title")
            raise AppError(
                classified.detail.message,
                status_code=classified.detail.status_code,
                user_message=classified.user_message,
            ) from e

    async def update_conversation_window_size(self, size_to_add: int) -> None:
        try:
            self.conversation.window_size += size_to_add
            self.conversation.updated_at = datetime.now(timezone.utc)
            await self.conversation.save(update_fields=["window_size", "updated_at"])
        except AppError:
            raise
        except Exception as e:
            classified = classify_exception(e, context="update_conversation_window_size")
            raise AppError(
                classified.detail.message,
                status_code=classified.detail.status_code,
                user_message=classified.user_message,
            ) from e

    async def update_conversation_bookmark(self, bookmark_value: bool) -> bool:
        self.conversation.is_bookmarked = bookmark_value
        await Conversation.filter(id=self._conversation_id).update(
            is_bookmarked=bookmark_value,
        )
        return bookmark_value

    async def update_conversation_title(self, title: str) -> str:
        self.conversation.title = title
        await self.conversation.save()
        return title

    async def delete_conversation(self):
        try:
            await self.conversation.delete()
        except AppError:
            raise
        except Exception as e:
            classified = classify_exception(e, context="delete_conversation")
            raise AppError(
                classified.detail.message,
                status_code=classified.detail.status_code,
                user_message=classified.user_message,
            ) from e
