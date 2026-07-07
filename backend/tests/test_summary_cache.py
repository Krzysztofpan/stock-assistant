import uuid

import pytest

from app.memory.summary_cache import SummaryCache, SummaryEntry


@pytest.mark.asyncio
async def test_summary_cache_roundtrip(redis_client):
    cache = SummaryCache(redis_client)
    conversation_id = str(uuid.uuid4())

    try:
        await cache.set(conversation_id, "test summary", 42)

        entry = await cache.get_entry(conversation_id)

        assert entry == SummaryEntry(text="test summary", last_message_id=42)
        assert await cache.get(conversation_id) == "test summary"
    finally:
        await cache.delete(conversation_id)


@pytest.mark.asyncio
async def test_summary_cache_rebuild_from_db(db, redis_client):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.conversation_summary import ConversationSummary
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    cache = SummaryCache(redis_client)
    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"

    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
    )
    message = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="hello",
    )
    await ConversationSummary.create(
        conversation_id=conversation.id,
        summary="db summary",
        summary_level=1,
        last_message_id=message.id,
    )

    try:
        await cache.delete(str(conversation_id))

        entry = await cache.get_entry(str(conversation_id))

        assert entry == SummaryEntry(text="db summary", last_message_id=message.id)
    finally:
        await cache.delete(str(conversation_id))
        await ConversationSummary.filter(conversation_id=conversation.id).delete()
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()
