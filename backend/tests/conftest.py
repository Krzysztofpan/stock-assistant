import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from app.config import get_settings
import app.memory.redis_client as redis_module
from app.memory.conversation_memory import ConversationMemory
from app.memory.message_buffer import MessageBuffer
from app.core.security.security_pipeline import SecurityPipeline
from app.dependencies import get_chat_service
from app.models.routing import SafetyVerdict
from app.services.chat_service import ChatService
from app.services.injection_gate_service import InjectionGateService
from app.tortoise.config import close_db, init_db
from app.tortoise.models.users import User
from app.utils.tokenizer import Tokenizer

settings = get_settings()

DEFAULT_PASSWORD = "Password1"


async def _mock_ask_stream(_messages) -> AsyncIterator[dict]:
    yield {"type": "token", "delta": "Test response"}


def _recreate_redis() -> None:
    client = Redis(
        host=settings.redis_host,
        port=int(settings.redis_port),
        decode_responses=True,
    )
    redis_module.redis = client

    # Modules import `redis` by value; refresh after lifespan closes the client.
    import app.routes.healthy_check as health_module

    health_module.redis = client


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
    _recreate_redis()
    await init_db()

    mock_stock_assistant = AsyncMock()
    mock_stock_assistant.ask_stream = _mock_ask_stream

    mock_injection_gate = AsyncMock(spec=InjectionGateService)
    mock_injection_gate.check_safety = AsyncMock(
        return_value=SafetyVerdict(is_safe=True, confidence=0.0),
    )

    from app.container import mark_heavy_services_warmed
    from app.app import app

    security = SecurityPipeline()
    chat_service = ChatService(
        security=security,
        memory=ConversationMemory(
            redis_module.redis,
            MessageBuffer(redis_module.redis, security.mask_for_llm),
        ),
        stock_assistant=mock_stock_assistant,
        tokenizer=Tokenizer(settings.llm_model),
        injection_gate=mock_injection_gate,
    )
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        mark_heavy_services_warmed()
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
