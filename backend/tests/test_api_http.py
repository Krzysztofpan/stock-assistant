import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.tortoise.models.conversation import Conversation
from app.tortoise.models.users import User
from tests.conftest import DEFAULT_PASSWORD, login_user, register_user


@pytest.mark.asyncio
async def test_sign_up_creates_user(client: AsyncClient, unique_email: str):
    response = await client.post(
        "/auth/sign-up",
        json={
            "name": "New User",
            "email": unique_email,
            "password": DEFAULT_PASSWORD,
            "password_repeat": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == 201
    assert response.json() == "User successfully registered"

    user = await User.get_or_none(email=unique_email)
    assert user is not None
    assert user.name == "New User"

    await user.delete()


@pytest.mark.asyncio
async def test_sign_up_rejects_duplicate_email(client: AsyncClient, unique_email: str):
    payload = {
        "name": "New User",
        "email": unique_email,
        "password": DEFAULT_PASSWORD,
        "password_repeat": DEFAULT_PASSWORD,
    }

    first = await client.post("/auth/sign-up", json=payload)
    second = await client.post("/auth/sign-up", json=payload)

    assert first.status_code == 201
    assert second.status_code == 400
    body = second.json()
    assert body["message"] == "User with this email already exists"
    assert body["status_code"] == 400

    await User.filter(email=unique_email).delete()


@pytest.mark.asyncio
async def test_sign_up_rejects_invalid_payload(client: AsyncClient):
    response = await client.post(
        "/auth/sign-up",
        json={
            "name": "New User",
            "email": "not-an-email",
            "password": "short",
            "password_repeat": "short",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_sign_in_returns_token(client: AsyncClient, unique_email: str):
    await register_user(client, unique_email)

    response = await client.post(
        "/auth/sign-in",
        data={"username": unique_email, "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    await User.filter(email=unique_email).delete()


@pytest.mark.asyncio
async def test_sign_in_rejects_bad_credentials(client: AsyncClient, unique_email: str):
    await register_user(client, unique_email)

    response = await client.post(
        "/auth/sign-in",
        data={"username": unique_email, "password": "WrongPass1"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Bad credentials"
    assert body["status_code"] == 401

    await User.filter(email=unique_email).delete()


@pytest.mark.asyncio
async def test_api_requires_authentication(client: AsyncClient):
    response = await client.get("/api/conversations/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_rejects_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/conversations/",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Malformed token"
    assert body["status_code"] == 401


@pytest.mark.asyncio
async def test_api_rejects_expired_token(client: AsyncClient):
    from datetime import datetime, timedelta, timezone

    import jwt

    from app.config import get_settings

    settings = get_settings()
    expired = datetime.now(timezone.utc) - timedelta(seconds=60)
    token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001", "exp": expired},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Token expired"
    assert body["status_code"] == 401


@pytest.mark.asyncio
async def test_get_me_returns_current_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    unique_email: str,
):
    user = await User.get(email=unique_email)

    response = await client.get("/api/me", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "user": {
            "id": str(user.id),
            "name": "Test User",
            "email": unique_email,
        }
    }


@pytest.mark.asyncio
async def test_get_me_requires_authentication(client: AsyncClient):
    response = await client.get("/api/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_rejects_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["message"] == "Malformed token"
    assert body["status_code"] == 401


@pytest.mark.asyncio
async def test_get_me_returns_404_when_user_deleted(
    client: AsyncClient,
    unique_email: str,
):
    await register_user(client, unique_email)
    token = await login_user(client, unique_email)
    headers = {"Authorization": f"Bearer {token}"}

    user = await User.get(email=unique_email)
    await user.delete()

    response = await client.get("/api/me", headers=headers)

    assert response.status_code == 404
    body = response.json()
    assert body["status_code"] == 404
    assert body["message"] == "User not found"


@pytest.mark.asyncio
async def test_get_conversations_returns_empty_list(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await client.get("/api/conversations/", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["conversations"] == []
    assert body["has_more"] is False


@pytest.mark.asyncio
async def test_get_conversation_messages_returns_empty_for_missing_conversation(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    response = await client.get(
        f"/api/conversations/{uuid.uuid4()}/messages",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["messages"] == []
    assert body["has_more"] is False


@pytest.mark.asyncio
async def test_get_conversation_messages_returns_messages(
    client: AsyncClient,
    auth_headers: dict[str, str],
    unique_email: str,
):
    user = await User.get(email=unique_email)
    conversation_id = uuid.uuid4()
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="Test conversation",
    )

    try:
        response = await client.get(
            f"/api/conversations/{conversation_id}/messages",
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["messages"] == []
        assert body["has_more"] is False
    finally:
        await conversation.delete()


@pytest.mark.asyncio
async def test_chat_stream_returns_response(client: AsyncClient, auth_headers: dict[str, str]):
    conversation_id = str(uuid.uuid4())

    with patch(
        "app.services.conversation.service.ConversationService.create_conversation_title",
        new=AsyncMock(return_value="Test title"),
    ):
        response = await client.post(
            "/api/chat/stream",
            headers=auth_headers,
            json={
                "message": "Jaka jest cena AAPL?",
                "conversation_id": conversation_id,
            },
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = _parse_sse_events(response.text)
    event_types = [event_type for event_type, _ in events]

    assert "token" in event_types
    assert "done" in event_types

    done_data = next(data for event_type, data in events if event_type == "done")
    assert done_data["message"]["text"] == "Test response"
    assert done_data["error"] is None

    conversation = await Conversation.get_or_none(id=conversation_id)
    if conversation:
        await conversation.delete()


def _parse_sse_events(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []

    for block in text.strip().split("\n\n"):
        if not block.strip():
            continue

        event_type = "message"
        data = ""

        for line in block.split("\n"):
            if line.startswith("event:"):
                event_type = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data = line.removeprefix("data:").strip()

        if data:
            events.append((event_type, json.loads(data)))

    return events
