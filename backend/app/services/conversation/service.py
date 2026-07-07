from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from tortoise.expressions import F

from app.config import get_settings
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

    async def create_conversation(self) -> None:
        await Conversation.create(
            id=self._conversation_id,
            user_id=self._user_id,
            title="New Conversation",
        )

    async def create_conversation_title(self, first_message: str):
        try:
            llm = ChatOpenAI(model=settings.cheap_llm_model, temperature=0.5)
            prompt = f"""
            Based on first user question, create conversation title based on first user question, use only few words, remember that you are in the
            finance context, so don't change english business name to other country word for example Apple. 
            Rember to generate title in the same language as user input
            
            question: {first_message}
            """
            res = await llm.ainvoke(prompt)
            conversation = await Conversation.get(id=self._conversation_id)
            conversation.title = res.content
            await conversation.save()
            
            await conversation_event_bus.publish(self._user_id, {
                "type": "conversation.title_updated",
                "conversation_id": self._conversation_id,
                "title": res.content
            })
        except Exception as e:
            classified = classify_exception(e, context="create_conversation_title")
            raise AppError(
                classified.detail.message,
                status_code=classified.detail.status_code,
                user_message=classified.user_message,
            ) from e

    async def update_conversation_window_size(self, size_to_add: int) -> None:
        try:
            await Conversation.filter(id=self._conversation_id).update(
                window_size=F("window_size") + size_to_add,
                updated_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            classified = classify_exception(e, context="update_conversation_window_size")
            raise AppError(
                classified.detail.message,
                status_code=classified.detail.status_code,
                user_message=classified.user_message,
            ) from e
        
    async def update_conversation_bookmark(self, bookmark_value):
        await Conversation.filter(id=self._conversation_id).update(
            is_bookmarked=bookmark_value,
        )

        return bookmark_value
    


    async def ensure_owned_by_user(self) -> Conversation | None:
        conversation = await Conversation.get_or_none(
            id=self._conversation_id,
            user_id=self._user_id,
        )

        if conversation is None:
            exists = await Conversation.exists(id=self._conversation_id)
            if exists:
                raise AppError(f"Conversation {self._conversation_id} not found for user {self._user_id}", status_code=404, user_message="Conversation not found.")
            return None
        return conversation
