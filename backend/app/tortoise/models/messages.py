from enum import Enum

from tortoise import fields, models


class MessageRole(str, Enum):
    USER = "user"
    SYSTEM = "system"
    AI = "ai"


class Message(models.Model):
    id = fields.IntField(primary_key=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    text = fields.TextField()

    role = fields.CharEnumField(enum_type=MessageRole)

    conversation = fields.ForeignKeyField(
        "models.Conversation",
        related_name="messages",
        db_column="conversation_id",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "Messages"