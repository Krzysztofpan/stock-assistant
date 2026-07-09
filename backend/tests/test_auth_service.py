import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from app.errors.exceptions import AppError

from app.config import get_settings
from app.models.api import UserPublic
from app.services.auth_service import AuthService, RegisterService
from app.tortoise.models.users import User
from app.utils.jwt_creator import jwt_creator
from tests.conftest import DEFAULT_PASSWORD

settings = get_settings()


@pytest.mark.asyncio
async def test_authenticate_user_returns_user_for_valid_credentials(db):
    email = f"{uuid.uuid4()}@example.com"
    hashed = RegisterService(
        name="Test",
        email=email,
        password=DEFAULT_PASSWORD,
        password_repeat=DEFAULT_PASSWORD,
    )
    await hashed.create_user()

    user = await AuthService().authenticate_user(email, DEFAULT_PASSWORD)

    assert user is not None
    assert user.email == email

    await User.filter(email=email).delete()


@pytest.mark.asyncio
async def test_authenticate_user_returns_none_for_wrong_password(db):
    email = f"{uuid.uuid4()}@example.com"
    service = RegisterService(
        name="Test",
        email=email,
        password=DEFAULT_PASSWORD,
        password_repeat=DEFAULT_PASSWORD,
    )
    await service.create_user()

    user = await AuthService().authenticate_user(email, "WrongPass1")

    assert user is None

    await User.filter(email=email).delete()


@pytest.mark.asyncio
async def test_authenticate_user_returns_none_for_unknown_email(db):
    user = await AuthService().authenticate_user(
        f"{uuid.uuid4()}@test.local",
        DEFAULT_PASSWORD,
    )

    assert user is None


@pytest.mark.asyncio
async def test_register_service_detects_existing_user(db):
    email = f"{uuid.uuid4()}@example.com"
    service = RegisterService(
        name="Test",
        email=email,
        password=DEFAULT_PASSWORD,
        password_repeat=DEFAULT_PASSWORD,
    )
    await service.create_user()

    assert await service.user_already_exists() is True

    await User.filter(email=email).delete()


@pytest.mark.asyncio
async def test_jwt_creator_includes_user_id_as_sub(db):
    email = f"{uuid.uuid4()}@example.com"
    user = await User.create(
        name="JWT Test",
        email=email,
        password="hashed",
    )

    token = jwt_creator.create_access_token(user.id)
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(user.id)
    assert "exp" in payload

    await user.delete()


def test_verify_access_token_rejects_malformed_token():
    with pytest.raises(AppError) as exc_info:
        AuthService().verify_access_token("not-a-valid-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.user_message == "Malformed token"


def test_verify_access_token_rejects_expired_token():
    expired = datetime.now(timezone.utc) - timedelta(seconds=60)
    payload = {"sub": str(uuid.uuid4()), "exp": expired}
    token = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(AppError) as exc_info:
        AuthService().verify_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.user_message == "Token expired"


def test_verify_access_token_rejects_invalid_signature():
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(AppError) as exc_info:
        AuthService().verify_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.user_message == "Invalid token signature"


def test_verify_access_token_rejects_invalid_payload():
    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(AppError) as exc_info:
        AuthService().verify_access_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.user_message == "Invalid token payload"


@pytest.mark.asyncio
async def test_get_current_user_returns_user_public(db):
    email = f"{uuid.uuid4()}@example.com"
    user = await User.create(
        name="Current User",
        email=email,
        password="hashed",
    )

    result = await AuthService().get_current_user(str(user.id))

    assert isinstance(result, UserPublic)
    assert result.id == user.id
    assert result.name == "Current User"
    assert result.email == email

    await user.delete()


@pytest.mark.asyncio
async def test_get_current_user_raises_404_for_unknown_id(db):
    with pytest.raises(AppError) as exc_info:
        await AuthService().get_current_user(str(uuid.uuid4()))

    assert exc_info.value.status_code == 404
