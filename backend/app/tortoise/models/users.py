from tortoise import fields, models


class User(models.Model):
    id = fields.UUIDField(primary_key=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255)

    class Meta:
        table = "Users"