import pytest

from app.errors.exceptions import AppError
from app.utils.pagination import (
    Page,
    clamp_limit,
    validate_composite_cursor,
)


def test_clamp_limit_enforces_bounds():
    assert clamp_limit(0, 30) == 1
    assert clamp_limit(15, 30) == 15
    assert clamp_limit(100, 30) == 30


def test_validate_composite_cursor_accepts_both_or_neither():
    validate_composite_cursor(None, None)
    validate_composite_cursor("2026-01-01", "uuid")


def test_validate_composite_cursor_rejects_partial_cursor():
    with pytest.raises(AppError) as exc_info:
        validate_composite_cursor("2026-01-01", None)

    assert exc_info.value.status_code == 400

    with pytest.raises(AppError):
        validate_composite_cursor(None, "uuid")


@pytest.mark.asyncio
async def test_fetch_page_detects_has_more_and_reverses(db):
    import uuid

    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User
    from app.utils.pagination import fetch_page

    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"

    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
    )
    first = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="pierwsze",
    )
    second = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.AI,
        text="drugie",
    )

    try:
        page = await fetch_page(
            Message.filter(conversation_id=conversation.id).order_by("-id"),
            1,
            reverse=True,
        )

        assert page == Page(items=[second], has_more=True)
    finally:
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()
