import json
import uuid

import pytest

from app.core.security.PII_detector import PIIDetector
from app.memory.message_buffer import MessageBuffer


@pytest.mark.asyncio
async def test_append_message_stores_masked_payload_in_redis(redis_client):
    buffer = MessageBuffer(redis_client, PIIDetector().mask)
    conversation_id = str(uuid.uuid4())

    try:
        await buffer.append_message(
            conversation_id,
            "user",
            "kontakt <EMAIL_ADDRESS>",
            message_id=1,
        )

        cached = await redis_client.lrange(f"conversation:{conversation_id}:buffer", 0, -1)

        assert len(cached) == 1
        payload = json.loads(cached[0])
        assert payload == {
            "id": 1,
            "role": "user",
            "text": "kontakt <EMAIL_ADDRESS>",
        }
    finally:
        await redis_client.delete(f"conversation:{conversation_id}:buffer")


@pytest.mark.asyncio
async def test_rebuild_buffer_masks_pii_from_db(db, redis_client):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

    buffer = MessageBuffer(redis_client, PIIDetector().mask)
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
        messages = await buffer.get_recent_messages(str(conversation_id))

        assert len(messages) == 1
        assert messages[0].content == "kontakt <EMAIL_ADDRESS>"
        assert "jan@test.com" not in messages[0].content
    finally:
        await redis_client.delete(f"conversation:{conversation_id}:buffer")
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_trim_messages_up_to_removes_summarized_messages(redis_client):
    buffer = MessageBuffer(redis_client, lambda text: text)
    conversation_id = str(uuid.uuid4())
    key = f"conversation:{conversation_id}:buffer"

    try:
        await redis_client.rpush(
            key,
            json.dumps({"id": 1, "role": "user", "text": "stare"}),
            json.dumps({"id": 2, "role": "ai", "text": "stara odpowiedź"}),
            json.dumps({"id": 3, "role": "user", "text": "nowe"}),
        )

        await buffer.trim_messages_up_to(conversation_id, 2)

        cached = await redis_client.lrange(key, 0, -1)

        assert len(cached) == 1
        assert json.loads(cached[0])["id"] == 3
    finally:
        await redis_client.delete(key)


@pytest.mark.asyncio
async def test_get_messages_after_prefers_redis_cache(redis_client):
    buffer = MessageBuffer(redis_client, lambda text: text)
    conversation_id = str(uuid.uuid4())
    key = f"conversation:{conversation_id}:buffer"

    try:
        await redis_client.rpush(
            key,
            json.dumps({"id": 5, "role": "user", "text": "z cache"}),
        )

        messages = await buffer.get_messages_after(conversation_id, after_message_id=4)

        assert len(messages) == 1
        assert messages[0].content == "z cache"
    finally:
        await redis_client.delete(key)
