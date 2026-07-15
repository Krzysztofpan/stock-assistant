import json
from collections.abc import Callable

from redis.asyncio import Redis

from app.memory.keys import conversation_key
from app.models.chat_message import ChatMessage, message_from_payload
from app.tortoise.models.messages import Message


class MessageBuffer:
    BUFFER_SIZE = 20
    TTL_SECONDS = 60 * 60 * 24 * 7

    def __init__(self, redis: Redis, mask_text: Callable[[str], str]):
        self.redis = redis
        self._mask_text = mask_text

    def _buffer_key(self, conversation_id: str) -> str:
        return conversation_key(conversation_id, "buffer")

    def _to_payload(self, message_id: int, role: str, text: str) -> dict:
        return {"id": message_id, "role": role, "text": text}

    def _role_value(self, role) -> str:
        return role.value if hasattr(role, "value") else role

    async def append_message(
        self,
        conversation_id: str,
        role: str,
        text: str,
        *,
        message_id: int,
    ) -> None:
        payload = self._to_payload(message_id, role, text)

        key = self._buffer_key(conversation_id)

        pipe = self.redis.pipeline()
        pipe.rpush(key, json.dumps(payload))
        pipe.ltrim(key, -self.BUFFER_SIZE, -1)
        pipe.expire(key, self.TTL_SECONDS)
        await pipe.execute()

    async def get_recent_messages(self, conversation_id: str) -> list[ChatMessage]:
        key = self._buffer_key(conversation_id)

        cached = await self.redis.lrange(key, 0, -1)

        if cached:
            messages = self._parse_cached_messages(cached)
            if messages is not None:
                return messages

        return await self._rebuild_buffer(conversation_id)

    async def get_messages_after(
        self,
        conversation_id: str,
        after_message_id: int,
    ) -> list[ChatMessage]:
        key = self._buffer_key(conversation_id)

        cached = await self.redis.lrange(key, 0, -1)

        if cached:
            messages = self._parse_cached_messages(
                cached,
                after_message_id=after_message_id,
            )
            if messages is not None:
                return messages

        return await self._rebuild_messages_after(conversation_id, after_message_id)

    async def trim_messages_up_to(self, conversation_id: str, last_message_id: int) -> None:
        key = self._buffer_key(conversation_id)
        cached = await self.redis.lrange(key, 0, -1)

        if not cached:
            return

        kept: list[str] = []
        for item in cached:
            try:
                payload = json.loads(item)
                if payload.get("id", 0) > last_message_id:
                    kept.append(item)
            except (json.JSONDecodeError, TypeError):
                continue

        pipe = self.redis.pipeline()
        pipe.delete(key)
        for item in kept:
            pipe.rpush(key, item)
        if kept:
            pipe.expire(key, self.TTL_SECONDS)
        await pipe.execute()

    def _parse_cached_messages(
        self,
        cached: list,
        *,
        after_message_id: int | None = None,
    ) -> list[ChatMessage] | None:
        try:
            messages: list[ChatMessage] = []
            for item in cached:
                payload = json.loads(item)
                if payload.get("id") is None:
                    return None
                if after_message_id is not None and payload["id"] <= after_message_id:
                    continue
                messages.append(message_from_payload(payload))
            return messages
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    async def _rebuild_buffer(self, conversation_id: str) -> list[ChatMessage]:
        messages = (
            await Message.filter(conversation_id=conversation_id)
            .order_by("-created_at")
            .limit(self.BUFFER_SIZE)
        )

        messages.reverse()

        result: list[ChatMessage] = []
        key = self._buffer_key(conversation_id)
        pipe = self.redis.pipeline()
        pipe.delete(key)

        for message in messages:
            masked_text = self._mask_text(message.text)
            payload = self._to_payload(
                message.id,
                self._role_value(message.role),
                masked_text,
            )

            result.append(message_from_payload(payload))
            pipe.rpush(key, json.dumps(payload))

        if result:
            pipe.expire(key, self.TTL_SECONDS)
        await pipe.execute()

        return result

    async def _rebuild_messages_after(
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

        result: list[ChatMessage] = []
        key = self._buffer_key(conversation_id)
        pipe = self.redis.pipeline()
        pipe.delete(key)

        for message in messages:
            masked_text = self._mask_text(message.text)
            payload = self._to_payload(
                message.id,
                self._role_value(message.role),
                masked_text,
            )

            result.append(message_from_payload(payload))
            pipe.rpush(key, json.dumps(payload))

        if result:
            pipe.expire(key, self.TTL_SECONDS)
        await pipe.execute()

        return result
