import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.summarization_service import SummarizationService


@pytest.mark.asyncio
async def test_upsert_summary_skips_when_threshold_not_reached(db, redis_client):
    from app.memory.summary_cache import SummaryCache
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.conversation_summary import ConversationSummary
    from app.tortoise.models.users import User

    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"
    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
        window_size=10,
    )
    cache = SummaryCache(redis_client)
    service = SummarizationService(str(conversation_id), summary_cache=cache)

    try:
        await service.upsert_summary()

        assert await ConversationSummary.filter(conversation_id=conversation.id).count() == 0
        assert await cache.get(str(conversation_id)) is None
    finally:
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_upsert_summary_writes_db_and_cache(db, redis_client):
    from app.memory.summary_cache import SummaryCache
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.conversation_summary import ConversationSummary
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"
    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
        window_size=600,
    )
    message = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="długa wiadomość testowa",
    )
    cache = SummaryCache(redis_client)
    service = SummarizationService(str(conversation_id), summary_cache=cache)

    try:
        with patch.object(
            SummarizationService,
            "create_summary",
            new=AsyncMock(return_value="nowe podsumowanie"),
        ):
            await service.upsert_summary()

        summary = await ConversationSummary.get_or_none(conversation_id=conversation.id)
        cached = await cache.get_entry(str(conversation_id))

        assert summary is not None
        assert summary.summary == "nowe podsumowanie"
        assert summary.last_message_id == message.id
        assert cached is not None
        assert cached.text == "nowe podsumowanie"
        assert cached.last_message_id == message.id
    finally:
        await cache.delete(str(conversation_id))
        await ConversationSummary.filter(conversation_id=conversation.id).delete()
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()
