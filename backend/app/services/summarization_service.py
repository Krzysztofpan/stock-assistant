from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.memory.summary_cache import SummaryCache
from app.errors.exceptions import AppError
from app.errors.mapping import classify_exception
from app.tortoise.models.conversation import Conversation
from app.tortoise.models.conversation_summary import ConversationSummary
from app.tortoise.models.messages import Message

settings = get_settings()


class SummarizationService:
    def __init__(self, conversation_id, summary_cache: SummaryCache | None = None):
        self.conversation_id = conversation_id
        self.summary_cache = summary_cache

    async def upsert_summary(self) -> None:
        conversation = await Conversation.get(id=self.conversation_id)
        existing_summary = await ConversationSummary.get_or_none(
            conversation_id=self.conversation_id
        )
        if not self._is_summarization_needed(conversation, existing_summary):
            return

        message_filters = {"conversation_id": self.conversation_id}
        if existing_summary:
            message_filters["id__gt"] = existing_summary.last_message_id

        last_messages = await Message.filter(**message_filters).order_by("id")
        if not last_messages:
            return

        new_summary = await self.create_summary(
            existing_summary.summary if existing_summary else None,
            last_messages,
        )

        await ConversationSummary.update_or_create(
            conversation_id=self.conversation_id,
            defaults={
                "summary": new_summary,
                "last_message_id": last_messages[-1].id,
                "summary_level": existing_summary.summary_level + 1 if existing_summary else 1,
            },
        )

        if self.summary_cache:
            await self.summary_cache.set(
                self.conversation_id,
                new_summary,
                last_messages[-1].id,
            )

    def _is_summarization_needed(
        self,
        conversation: Conversation,
        summary: ConversationSummary | None,
    ) -> bool:
        threshold = settings.tokens_between_summary
        if not summary:
            return conversation.window_size >= threshold
        return conversation.window_size >= (summary.summary_level + 1) * threshold

    async def create_summary(self, existing_summary: str | None, last_messages: List[Message]) -> str:
        template = """
        Based on existing summary and last messages between user and chatbot create new conversation summary:

        existing summary (maybe doesn't exist): {summary}

        last messages: {last_messages}

        based on this create new summary with all context existing in summary and new messages combine this and return new summary.
        """
        converted_last_messages = "\n\n".join(
            f"{message.role.value}: {message.text}" for message in last_messages
        )
         
        prompt = ChatPromptTemplate.from_template(template)

        llm_for_create_summary = ChatOpenAI(model=settings.llm_model, temperature=0.5)

        chain = prompt | llm_for_create_summary

        try:
            new_summary = await chain.ainvoke({"summary": existing_summary, "last_messages": converted_last_messages}) 
        except Exception as e:
            classified = classify_exception(e, context="create_summary")
            raise AppError(
                classified.detail.message,
                status_code=classified.detail.status_code,
                user_message=classified.user_message,
            ) from e
        
        return new_summary.content


