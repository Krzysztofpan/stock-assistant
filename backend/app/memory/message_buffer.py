import json

from redis.asyncio import Redis

from app.memory.keys import conversation_key
from app.models.chat_message import ChatMessage, message_from_model, message_from_payload
from app.tortoise.models.messages import Message


class MessageBuffer:
    BUFFER_SIZE = 20
    TTL_SECONDS = 60 * 60 * 24 * 7

    def __init__(self, redis: Redis):
        self.redis = redis

    def _buffer_key(self, conversation_id: str) -> str:
        return conversation_key(conversation_id, "buffer")

    async def append_message(
        self,
        conversation_id: str,
        role: str,
        text: str,
    ) -> None:
        payload = {
            "role": role,
            "text": text,
        }

        key = self._buffer_key(conversation_id)

        await self.redis.rpush(key, json.dumps(payload))
        await self.redis.ltrim(key, -self.BUFFER_SIZE, -1)
        await self.redis.expire(key, self.TTL_SECONDS)

    async def get_recent_messages(self, conversation_id: str) -> list[ChatMessage]:
        key = self._buffer_key(conversation_id)

        cached = await self.redis.lrange(key, 0, -1)

        if cached:
            try:
                return [
                    message_from_payload(json.loads(item))
                    for item in cached
                ]
            except (json.JSONDecodeError, KeyError, TypeError):
                return await self._rebuild_buffer(conversation_id)

        return await self._rebuild_buffer(conversation_id)

    async def get_messages_after(
        self,
        conversation_id: str,
        after_message_id: int,
    ) -> list[ChatMessage]:
        messages = (
            await Message.filter(
                conversation_id=conversation_id,
                id__gt=after_message_id,
            )
            .order_by("id")
        )
        return [message_from_model(message) for message in messages]

    async def _rebuild_buffer(self, conversation_id: str) -> list[ChatMessage]:
        messages = (
            await Message.filter(conversation_id=conversation_id)
            .order_by("-created_at")
            .limit(self.BUFFER_SIZE)
        )

        messages.reverse()

        result = []
        key = self._buffer_key(conversation_id)
        pipe = self.redis.pipeline()

        for message in messages:
            payload = {
                "role": message.role,
                "text": message.text,
            }

            result.append(message_from_payload(payload))
            pipe.rpush(key, json.dumps(payload))

        pipe.expire(key, self.TTL_SECONDS)
        await pipe.execute()

        return result
