import asyncio

class ConversationEventBus:
    def __init__(self):
        self.queues_by_user = {}

    async def subscribe(self, user_id: str):
        queue = asyncio.Queue()
        self.queues_by_user.setdefault(user_id, set()).add(queue)

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    yield None
                    continue
                yield event
        finally: 
            self.queues_by_user[user_id].discard(queue)
    
    async def publish(self, user_id: str, event: dict):
        for queue in self.queues_by_user.get(user_id, set()).copy():
            await queue.put(event)
        
conversation_event_bus = ConversationEventBus()