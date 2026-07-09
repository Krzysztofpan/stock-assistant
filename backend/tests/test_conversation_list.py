import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.errors.exceptions import AppError
from app.services.conversation import ConversationService, list_conversations


@pytest.mark.asyncio
async def test_get_conversations_returns_most_recently_updated_first(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"
    now = datetime.now(timezone.utc)

    user = await User.create(name="test", email=email, password="secret")
    oldest = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="oldest",
    )
    middle = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="middle",
    )
    newest = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="newest",
    )
    await Conversation.filter(id=oldest.id).update(updated_at=now - timedelta(hours=2))
    await Conversation.filter(id=middle.id).update(updated_at=now - timedelta(hours=1))
    await Conversation.filter(id=newest.id).update(updated_at=now)

    try:
        result = await list_conversations(str(user.id), limit=10)

        assert result.has_more is False
        assert [item.title for item in result.conversations] == [
            "newest",
            "middle",
            "oldest",
        ]
    finally:
        await Conversation.filter(user_id=user.id).delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_conversations_with_cursor_returns_older_conversations(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"
    now = datetime.now(timezone.utc)

    user = await User.create(name="test", email=email, password="secret")
    oldest = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="oldest",
    )
    middle = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="middle",
    )
    newest = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="newest",
    )
    await Conversation.filter(id=oldest.id).update(updated_at=now - timedelta(hours=2))
    await Conversation.filter(id=middle.id).update(updated_at=now - timedelta(hours=1))
    await Conversation.filter(id=newest.id).update(updated_at=now)
    middle = await Conversation.get(id=middle.id)

    try:
        result = await list_conversations(
            str(user.id),
            limit=10,
            before_updated_at=middle.updated_at,
            before_id=str(middle.id),
        )

        assert result.has_more is False
        assert len(result.conversations) == 1
        assert result.conversations[0].title == "oldest"
    finally:
        await Conversation.filter(user_id=user.id).delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_conversations_respects_limit_and_has_more(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"
    now = datetime.now(timezone.utc)

    user = await User.create(name="test", email=email, password="secret")
    for offset in range(3):
        conversation = await Conversation.create(
            id=uuid.uuid4(),
            user_id=user.id,
            title=f"conversation-{offset}",
        )
        await Conversation.filter(id=conversation.id).update(
            updated_at=now - timedelta(hours=offset),
        )

    try:
        result = await list_conversations(str(user.id), limit=2)

        assert result.has_more is True
        assert len(result.conversations) == 2
        assert result.conversations[0].title == "conversation-0"
        assert result.conversations[1].title == "conversation-1"
    finally:
        await Conversation.filter(user_id=user.id).delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_conversations_returns_empty_for_user_without_conversations(db):
    from app.tortoise.models.users import User

    user = await User.create(
        name="test",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )

    try:
        result = await list_conversations(str(user.id))

        assert result.conversations == []
        assert result.has_more is False
    finally:
        await user.delete()


@pytest.mark.asyncio
async def test_get_conversations_raises_for_incomplete_cursor(db):
    from app.tortoise.models.users import User

    user = await User.create(
        name="test",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )

    try:
        with pytest.raises(AppError) as exc_info:
            await list_conversations(
                str(user.id),
                before_updated_at=datetime.now(timezone.utc),
            )

        assert exc_info.value.status_code == 400
    finally:
        await user.delete()


@pytest.mark.asyncio
async def test_get_conversations_filters_by_is_bookmarked(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    user = await User.create(
        name="test",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )
    pinned = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="pinned",
        is_bookmarked=True,
    )
    recent = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="recent",
        is_bookmarked=False,
    )

    try:
        pinned_result = await list_conversations(str(user.id), limit=10, is_bookmarked=True)
        recent_result = await list_conversations(str(user.id), limit=10, is_bookmarked=False)

        assert [item.title for item in pinned_result.conversations] == ["pinned"]
        assert [item.title for item in recent_result.conversations] == ["recent"]
    finally:
        await Conversation.filter(user_id=user.id).delete()
        await user.delete()


@pytest.mark.asyncio
async def test_updating_conversation_bookmark_does_not_update_updated_at(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    user = await User.create(
        name="test",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )
    conversation = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="conversation",
        is_bookmarked=False,
    )
    await Conversation.filter(id=conversation.id).update(
        updated_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    conversation = await Conversation.get(id=conversation.id)

    try:
        previous_updated_at = conversation.updated_at

        service = await ConversationService.open(
            conversation_id=str(conversation.id),
            user_id=str(user.id),
        )
        await service.update_conversation_bookmark(True)

        updated_conversation = await Conversation.get(id=conversation.id)

        assert updated_conversation.is_bookmarked is True
        assert updated_conversation.updated_at == previous_updated_at
    finally:
        await Conversation.filter(user_id=user.id).delete()
        await user.delete()


@pytest.mark.asyncio
async def test_updating_conversation_title_updates_updated_at(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    user = await User.create(
        name="test",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )
    conversation = await Conversation.create(
        id=uuid.uuid4(),
        user_id=user.id,
        title="conversation",
    )
    await Conversation.filter(id=conversation.id).update(
        updated_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    conversation = await Conversation.get(id=conversation.id)

    try:
        previous_updated_at = conversation.updated_at

        service = await ConversationService.open(
            conversation_id=str(conversation.id),
            user_id=str(user.id),
        )
        await service.update_conversation_title("renamed conversation")

        updated_conversation = await Conversation.get(id=conversation.id)

        assert updated_conversation.title == "renamed conversation"
        assert updated_conversation.updated_at > previous_updated_at
    finally:
        await Conversation.filter(user_id=user.id).delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_conversations_does_not_return_other_users_conversations(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    now = datetime.now(timezone.utc)

    owner = await User.create(
        name="owner",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )
    other_user = await User.create(
        name="other",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )
    await Conversation.create(
        id=uuid.uuid4(),
        user_id=owner.id,
        title="owner conversation",
        updated_at=now,
    )

    try:
        result = await list_conversations(str(other_user.id))

        assert result.conversations == []
        assert result.has_more is False
    finally:
        await Conversation.filter(user_id=owner.id).delete()
        await owner.delete()
        await other_user.delete()
