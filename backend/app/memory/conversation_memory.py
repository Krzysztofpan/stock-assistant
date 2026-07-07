from redis.asyncio import Redis

from app.memory.conversation_context import ConversationContext
from app.memory.message_buffer import MessageBuffer
from app.memory.summary_cache import SummaryCache
from app.models.chat_message import ChatMessage


class ConversationMemory:
    def __init__(self, redis: Redis):
        self.messages = MessageBuffer(redis)
        self.summary = SummaryCache(redis)

    async def append_message(
        self,
        conversation_id: str,
        role: str,
        text: str,
    ) -> None:
        await self.messages.append_message(conversation_id, role, text)

    async def get_recent_messages(self, conversation_id: str) -> list[ChatMessage]:
        return await self.messages.get_recent_messages(conversation_id)

    async def get_context(self, conversation_id: str) -> ConversationContext:
        summary_entry = await self.summary.get_entry(conversation_id)

        if summary_entry:
            messages = await self.messages.get_messages_after(
                conversation_id,
                summary_entry.last_message_id,
            )
            return ConversationContext(
                summary=summary_entry.text,
                messages=messages,
            )

        messages = await self.messages.get_recent_messages(conversation_id)
        return ConversationContext(summary=None, messages=messages)
