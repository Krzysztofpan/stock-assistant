import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAlgorithmError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)
from pydantic import ValidationError

from app.config import get_settings
from app.errors.exceptions import AppError
from app.models.auth import TokenPayload

settings = get_settings()


def _token_auth_error(message: str, *, user_message: str | None = None) -> AppError:
    return AppError(
        message,
        status_code=401,
        user_message=user_message or message,
    )


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload.model_validate(payload)
    except ExpiredSignatureError:
        raise _token_auth_error("Token expired")
    except InvalidSignatureError:
        raise _token_auth_error("Invalid token signature")
    except InvalidAlgorithmError:
        raise _token_auth_error("Invalid token algorithm")
    except MissingRequiredClaimError:
        raise _token_auth_error(
            "Missing required token claim",
            user_message="Invalid token payload",
        )
    except DecodeError:
        raise _token_auth_error("Malformed token")
    except InvalidTokenError:
        raise _token_auth_error("Invalid token")
    except ValidationError:
        raise _token_auth_error(
            "Invalid token payload",
            user_message="Invalid token payload",
        )
