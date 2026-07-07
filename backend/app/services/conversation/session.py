from app.memory.conversation_context import ConversationContext
from app.memory.conversation_memory import ConversationMemory
from app.services.conversation.service import ConversationService
from app.tortoise.models.messages import Message
from app.utils.tokenizer import Tokenizer
from app.models.api import MessageItem, MessageRole

class ConversationSession:
    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        *,
        memory: ConversationMemory,
        tokenizer: Tokenizer,
    ):
        self.conversation_id = conversation_id
        self._conversation = ConversationService(conversation_id, user_id)
        self._memory = memory
        self._tokenizer = tokenizer

    async def ensure_exists(self) -> None:
        conversation = await self._conversation.ensure_owned_by_user()
        if conversation is None:
            await self._conversation.create_conversation()

    async def add_message(self, role: str, text: str) -> MessageItem:
        message = await Message.create(text=text, role=MessageRole(role), conversation_id=self.conversation_id)
        await self._memory.append_message(self.conversation_id, role, text=text)
        await self._conversation.update_conversation_window_size(
            self._tokenizer.get_tokens_sum(text)
        )
    
        return MessageItem(
            id=message.id,
            role=MessageRole(message.role),
            text=message.text,
            created_at=message.created_at,
        )

    async def get_context(self) -> ConversationContext:
        return await self._memory.get_context(self.conversation_id)
