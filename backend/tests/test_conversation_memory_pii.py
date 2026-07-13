import json
import uuid

import pytest

from app.core.security.PII_detector import PIIDetector
from app.memory.conversation_memory import ConversationMemory
from app.memory.message_buffer import MessageBuffer


def _memory(redis_client) -> ConversationMemory:
    mask = PIIDetector().mask
    return ConversationMemory(redis_client, MessageBuffer(redis_client, mask))


@pytest.mark.asyncio
async def test_get_context_masks_user_email_on_db_rebuild(db, redis_client):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    memory = _memory(redis_client)
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
        text="kontakt jan@test.com",
    )

    try:
        context = await memory.get_context(str(conversation_id))

        assert context.summary is None
        assert len(context.messages) == 1
        assert context.messages[0].content == "kontakt <EMAIL_ADDRESS>"
        assert "jan@test.com" not in context.messages[0].content
    finally:
        await redis_client.delete(f"conversation:{conversation_id}:buffer")
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_context_uses_masked_redis_without_db_remask(db, redis_client):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    memory = _memory(redis_client)
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
        text="kontakt jan@test.com",
    )

    try:
        await memory.append_message(
            str(conversation_id),
            "user",
            "kontakt <EMAIL_ADDRESS>",
            message_id=message.id,
        )

        context = await memory.get_context(str(conversation_id))

        assert context.messages[0].content == "kontakt <EMAIL_ADDRESS>"
    finally:
        await redis_client.delete(f"conversation:{conversation_id}:buffer")
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_context_with_summary_uses_redis_summary_and_tail_messages(db, redis_client):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.conversation_summary import ConversationSummary
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    memory = _memory(redis_client)
    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"

    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
    )
    old_ai = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.AI,
        text="stara odpowiedź",
    )
    new_user = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="kontakt jan@test.com",
    )

    await memory.summary.set(str(conversation_id), "podsumowanie", old_ai.id)
    await ConversationSummary.create(
        conversation_id=conversation.id,
        summary="podsumowanie",
        summary_level=1,
        last_message_id=old_ai.id,
    )
    await memory.append_message(
        str(conversation_id),
        "user",
        "kontakt <EMAIL_ADDRESS>",
        message_id=new_user.id,
    )

    try:
        context = await memory.get_context(str(conversation_id))

        assert context.summary == "podsumowanie"
        assert len(context.messages) == 1
        assert context.messages[0].content == "kontakt <EMAIL_ADDRESS>"
    finally:
        await memory.summary.delete(str(conversation_id))
        await redis_client.delete(f"conversation:{conversation_id}:buffer")
        await ConversationSummary.filter(conversation_id=conversation.id).delete()
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()
