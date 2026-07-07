from tortoise import Tortoise
from app.config import get_settings

settings = get_settings()


def normalize_db_url(url: str) -> str:
    if url.startswith("postgresql://"):
        url = "postgres://" + url.removeprefix("postgresql://")
    # PgBouncer (e.g. Supabase pooler) does not support asyncpg prepared statements.
    if "statement_cache_size" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}statement_cache_size=0"
    return url


async def init_db():
    await Tortoise.init(
        db_url=normalize_db_url(settings.database_url),
        modules={"models": ["app.tortoise.models"]},
    )


async def close_db():
    await Tortoise.close_connections()

