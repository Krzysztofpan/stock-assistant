
from app.models.auth import Token,RegisterBody
from app.services.auth_service import auth_service, RegisterService
from fastapi.responses import JSONResponse
from app.utils.jwt_creator import jwt_creator

from app.config import get_settings
from app.errors.exceptions import AppError
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

settings = get_settings()

@auth_router.post('/sign-up')
async def register(body: RegisterBody):

    register_service = RegisterService(**body.model_dump())
    user_exists = await register_service.user_already_exists()

    if user_exists:
        raise AppError(
            "User with this email already exists",
            status_code=400,
            user_message="User with this email already exists",
        )

    try:
        await register_service.create_user()
    except Exception:
        raise AppError(
            "User registration failed",
            status_code=500,
            user_message="Something went wrong during register user",
        )

    return JSONResponse(status_code=201, content="User successfully registered")


@auth_router.post('/sign-in', response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    authenticated_user = await auth_service.authenticate_user(
        form_data.username.strip().lower(),
        form_data.password,
    )

    if not authenticated_user:
        raise HTTPException(
            401,
            detail="Bad credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = jwt_creator.create_access_token(authenticated_user.id)
 
    return Token(access_token=access_token, token_type="bearer")
    