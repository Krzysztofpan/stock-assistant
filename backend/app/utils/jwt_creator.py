from datetime import datetime, timedelta, timezone
from app.config import get_settings
import jwt
from app.tortoise.models.users import User
from uuid import UUID

settings = get_settings()

class JWTCreator:
    def __init__(self, secret, expires_time, algorithm):
        self.jwt_secret = secret
        self.expires_time = expires_time
        self.jwt_algorithm = algorithm

    def create_access_token(self, user_id: UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            seconds=settings.access_token_expire_seconds
        )
        payload = {
            "sub": str(user_id),
            "exp": expire,
        }

        return jwt.encode(
            payload, self.jwt_secret, algorithm=self.jwt_algorithm
        )
    


jwt_creator = JWTCreator(settings.jwt_secret, settings.access_token_expire_seconds, settings.jwt_algorithm)