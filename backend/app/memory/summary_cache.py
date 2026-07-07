import json
from dataclasses import dataclass

from redis.asyncio import Redis

from app.memory.keys import conversation_key
from app.tortoise.models.conversation_summary import ConversationSummary


@dataclass(frozen=True)
class SummaryEntry:
    text: str
    last_message_id: int


class SummaryCache:
    TTL_SECONDS = 60 * 60 * 24 * 7

    def __init__(self, redis: Redis):
        self.redis = redis

    def _summary_key(self, conversation_id: str) -> str:
        return conversation_key(conversation_id, "summary")

    async def get_entry(self, conversation_id: str) -> SummaryEntry | None:
        key = self._summary_key(conversation_id)
        cached = await self.redis.get(key)

        if cached is not None:
            entry = self._parse_cached(cached)
            if entry is not None:
                return entry

        return await self._rebuild_entry_from_db(conversation_id)

    async def get(self, conversation_id: str) -> str | None:
        entry = await self.get_entry(conversation_id)
        return entry.text if entry else None

    async def set(
        self,
        conversation_id: str,
        summary: str,
        last_message_id: int,
    ) -> None:
        key = self._summary_key(conversation_id)
        payload = json.dumps(
            {
                "summary": summary,
                "last_message_id": last_message_id,
            }
        )
        await self.redis.set(key, payload, ex=self.TTL_SECONDS)

    async def delete(self, conversation_id: str) -> None:
        await self.redis.delete(self._summary_key(conversation_id))

    def _parse_cached(self, cached: str) -> SummaryEntry | None:
        try:
            data = json.loads(cached)
            if isinstance(data, dict):
                return SummaryEntry(
                    text=data["summary"],
                    last_message_id=data["last_message_id"],
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        return None

    async def _rebuild_entry_from_db(self, conversation_id: str) -> SummaryEntry | None:
        record = await ConversationSummary.get_or_none(
            conversation_id=conversation_id
        )
        if not record:
            return None

        entry = SummaryEntry(
            text=record.summary,
            last_message_id=record.last_message_id,
        )
        await self.set(conversation_id, entry.text, entry.last_message_id)
        return entry
