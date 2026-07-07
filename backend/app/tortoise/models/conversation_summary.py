from tortoise import fields, models


class ConversationSummary(models.Model):
    id = fields.UUIDField(primary_key=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    summary = fields.TextField()
    summary_level = fields.SmallIntField(default=0)
    
    conversation = fields.ForeignKeyField(
        "models.Conversation",
        db_column="conversation_id",
        related_name="summaries",
    )

    last_message = fields.ForeignKeyField(
        "models.Message",
        db_column="last_message_id",
        related_name="summaries",
    )

    class Meta:
        table = "ConversationsSummary"