from typing import Annotated

from fastapi import Depends
from app.errors.exceptions import AppError

from app.auth import oauth2_scheme
from app.models.auth import TokenPayload
from app.tortoise.models.users import User
from app.utils.jwt_verifier import decode_access_token
from app.utils.password_hasher import password_hasher
from tortoise.exceptions import DoesNotExist
from app.models.api import UserPublic

class AuthService:
    def __init__(self):
        pass

    async def authenticate_user(self, email: str, password: str) -> User | None:
        user = await User.get_or_none(email=email)
        
        if not user:
            return None

        if not password_hasher.verify_password(password, user.password):
            return None
        
        return user
    
    def verify_access_token(
        self, token: Annotated[str, Depends(oauth2_scheme)]
    ) -> TokenPayload:
        return decode_access_token(token)
    
    async def get_current_user(self, user_id: str) -> UserPublic:
        try:
            user = await User.get(id=user_id).only("name", "email", "id")
            return UserPublic.model_validate(user)
        except DoesNotExist:
            raise AppError(
                message="User not found",
                status_code=404,
                user_message="User not found",
            )
     

auth_service = AuthService()

class RegisterService:
    def __init__(self, name: str, email: str, password: str, password_repeat: str):
        self.name = name
        self.email = email
        self.password = password
        self.password_repeat = password_repeat


    async def create_user(self):
        hashed_password = password_hasher.get_password_hash(self.password)
        await User.create(name=self.name, email=self.email, password=hashed_password)

    async def user_already_exists(self) -> bool:
        user = await User.get_or_none(email=self.email)
        if(user):
            return True
        return False
    
