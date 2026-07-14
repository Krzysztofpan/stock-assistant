import uuid

import pytest

from app.services.conversation import list_messages


@pytest.mark.asyncio
async def test_get_messages_returns_latest_in_chronological_order(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

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
    third = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="trzecie",
    )

    try:
        result = await list_messages(
            str(conversation_id),
            str(user.id),
            limit=2,
        )

        assert result.has_more is True
        assert len(result.messages) == 2
        assert result.messages[0].id == second.id
        assert result.messages[0].text == "drugie"
        assert result.messages[1].id == third.id
        assert result.messages[1].text == "trzecie"
    finally:
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_messages_with_before_id_returns_older_messages(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.messages import Message, MessageRole
    from app.tortoise.models.users import User

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
    third = await Message.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        text="trzecie",
    )

    try:
        result = await list_messages(
            str(conversation_id),
            str(user.id),
            limit=10,
            before_id=second.id,
        )

        assert result.has_more is False
        assert len(result.messages) == 1
        assert result.messages[0].id == first.id
        assert result.messages[0].text == "pierwsze"
    finally:
        await Message.filter(conversation_id=conversation.id).delete()
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_messages_returns_empty_for_new_conversation(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    conversation_id = uuid.uuid4()
    email = f"{conversation_id}@test.local"

    user = await User.create(name="test", email=email, password="secret")
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=user.id,
        title="test",
    )

    try:
        result = await list_messages(
            str(conversation_id),
            str(user.id),
        )

        assert result.messages == []
        assert result.has_more is False
    finally:
        await conversation.delete()
        await user.delete()


@pytest.mark.asyncio
async def test_get_messages_returns_empty_when_conversation_not_found(db):
    from app.tortoise.models.users import User

    user = await User.create(
        name="test",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )

    try:
        result = await list_messages(str(uuid.uuid4()), str(user.id))

        assert result.messages == []
        assert result.has_more is False
    finally:
        await user.delete()


@pytest.mark.asyncio
async def test_get_messages_returns_empty_for_wrong_user(db):
    from app.tortoise.models.conversation import Conversation
    from app.tortoise.models.users import User

    conversation_id = uuid.uuid4()

    owner = await User.create(
        name="owner",
        email=f"{conversation_id}@test.local",
        password="secret",
    )
    other_user = await User.create(
        name="other",
        email=f"{uuid.uuid4()}@test.local",
        password="secret",
    )
    conversation = await Conversation.create(
        id=conversation_id,
        user_id=owner.id,
        title="test",
    )

    try:
        result = await list_messages(
            str(conversation_id),
            str(other_user.id),
        )

        assert result.messages == []
        assert result.has_more is False
    finally:
        await conversation.delete()
        await owner.delete()
        await other_user.delete()
