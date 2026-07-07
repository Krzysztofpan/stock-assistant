from redis.asyncio import Redis
from app.config import get_settings

settings = get_settings()

redis = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True
)