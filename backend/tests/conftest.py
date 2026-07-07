import uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from app.config import get_settings
from app.memory.redis_client import redis as app_redis
from app.memory.conversation_memory import ConversationMemory
from app.core.security.security_pipeline import SecurityPipeline
from app.dependencies import get_chat_service
from app.services.chat_service import ChatService
from app.tortoise.config import close_db, init_db
from app.tortoise.models.users import User
from app.utils.tokenizer import Tokenizer

settings = get_settings()

DEFAULT_PASSWORD = "Password1"


def _recreate_redis() -> None:
    import app.memory.redis_client as redis_module

    redis_module.redis = Redis(
        host=settings.redis_host,
        port=int(settings.redis_port),
        decode_responses=True,
    )


@pytest_asyncio.fixture
async def db():
    await init_db()
    yield
    await close_db()


@pytest_asyncio.fixture
async def redis_client():
    client = Redis(
        host=settings.redis_host,
        port=int(settings.redis_port),
        decode_responses=True,
    )
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def client():
    await init_db()

    mock_stock_assistant = AsyncMock()
    mock_stock_assistant.ask.return_value = {
        "response": "Test response",
        "error": None,
    }

    from app.app import app

    chat_service = ChatService(
        security=SecurityPipeline(),
        memory=ConversationMemory(app_redis),
        stock_assistant=mock_stock_assistant,
        tokenizer=Tokenizer(settings.llm_model),
    )
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await close_db()
    _recreate_redis()


@pytest.fixture
def unique_email() -> str:
    return f"{uuid.uuid4()}@example.com"


async def register_user(
    client: AsyncClient,
    email: str,
    *,
    name: str = "Test User",
    password: str = DEFAULT_PASSWORD,
) -> None:
    response = await client.post(
        "/auth/sign-up",
        json={
            "name": name,
            "email": email,
            "password": password,
            "password_repeat": password,
        },
    )
    assert response.status_code == 201, response.text


async def login_user(
    client: AsyncClient,
    email: str,
    *,
    password: str = DEFAULT_PASSWORD,
) -> str:
    response = await client.post(
        "/auth/sign-in",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, unique_email: str):
    await register_user(client, unique_email)
    token = await login_user(client, unique_email)
    yield {"Authorization": f"Bearer {token}"}
    user = await User.get_or_none(email=unique_email)
    if user:
        await user.delete()
