import uuid

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from app.memory.conversation_memory import ConversationMemory
from app.memory.summary_cache import SummaryCache


@pytest.mark.asyncio
async def test_get_context_without_summary_uses_recent_messages(db, redis_client):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    memory = ConversationMemory(redis_client)
    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"

    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
    )
    await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="pierwsze",
    )
    await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.AI,
        text="odpowiedź",
    )

    try:
        context = await memory.get_context(str(conversation_id))

        assert context.summary is None
        assert len(context.messages) == 2
        assert context.messages[0].content == "pierwsze"
        assert context.messages[1].content == "odpowiedź"
    finally:
        await redis_client.delete(f"conversation:{conversation_id}:buffer")
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_context_with_summary_excludes_summarized_messages(db, redis_client):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.conversation_summary import ConversationSummary
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    memory = ConversationMemory(redis_client)
    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"

    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
    )
    old_user = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="stare pytanie",
    )
    old_ai = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.AI,
        text="stara odpowiedź",
    )
    new_user = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="nowe pytanie",
    )

    summary_cache = SummaryCache(redis_client)
    await summary_cache.set(str(conversation_id), "podsumowanie starej części", old_ai.id)
    await ConversationSummary.create(
        conversation_id=conversation.id,
        summary="podsumowanie starej części",
        summary_level=1,
        last_message_id=old_ai.id,
    )

    try:
        context = await memory.get_context(str(conversation_id))
        chat_messages = context.to_chat_messages()

        assert context.summary == "podsumowanie starej części"
        assert len(context.messages) == 1
        assert context.messages[0].content == "nowe pytanie"
        assert isinstance(chat_messages[0], SystemMessage)
        assert "podsumowanie starej części" in chat_messages[0].content
        assert isinstance(chat_messages[1], HumanMessage)
        assert chat_messages[1].content == "nowe pytanie"
    finally:
        await summary_cache.delete(str(conversation_id))
        await redis_client.delete(f"conversation:{conversation_id}:buffer")
        await ConversationSummary.filter(conversation_id=conversation.id).delete()
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()
