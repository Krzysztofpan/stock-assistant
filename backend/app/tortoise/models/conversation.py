from tortoise import fields, models

class Conversation(models.Model):
    id = fields.UUIDField(primary_key=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    window_size = fields.IntField(default=0)
    title = fields.TextField()

    is_bookmarked = fields.BooleanField(default=False)

    user = fields.ForeignKeyField(
        "models.User",
        related_name="conversations",
        db_column="user_id",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "Conversations"

    