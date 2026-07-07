import json
import logging
import re
from dataclasses import dataclass

import httpx
from openai import AuthenticationError as OpenAIAuthenticationError
from openai import PermissionDeniedError

from app.errors.exceptions import AppError
from app.models.error import ErrorDetail

logger = logging.getLogger(__name__)

_AUTH_STATUS_CODES = {401, 403}
_HTTP_STATUS_PATTERN = re.compile(r"\b(401|403|404|408|429|500|502|503|504)\b")


@dataclass(frozen=True)
class ClassifiedError:
    user_message: str
    detail: ErrorDetail


@dataclass(frozen=True)
class ExtractedError:
    message: str
    status_code: int


def _raw_message(exc: Exception) -> str:
    if isinstance(exc, AppError):
        return exc.message
    return str(exc) or exc.__class__.__name__


def _parse_embedded_payload(raw: str) -> dict | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _message_from_payload(data: dict, *, fallback: str) -> str:
    parts: list[str] = []
    for key in ("error", "message", "text"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    if parts:
        return " ".join(dict.fromkeys(parts))
    return fallback


def _status_code_from_payload(data: dict) -> int | None:
    status = data.get("status_code")
    if isinstance(status, int):
        return status
    if isinstance(status, str) and status.isdigit():
        return int(status)
    return None


def _status_code_from_text(raw: str) -> int | None:
    match = _HTTP_STATUS_PATTERN.search(raw)
    if match:
        return int(match.group(1))
    return None


def extract_error(exc: Exception) -> ExtractedError:
    if isinstance(exc, AppError):
        return ExtractedError(message=exc.message, status_code=exc.status_code)

    raw = _raw_message(exc)

    if isinstance(exc, httpx.HTTPStatusError):
        return ExtractedError(message=raw, status_code=exc.response.status_code)

    payload = _parse_embedded_payload(raw)
    if payload is not None:
        status_code = _status_code_from_payload(payload) or _status_code_from_text(raw) or 500
        return ExtractedError(
            message=_message_from_payload(payload, fallback=raw),
            status_code=status_code,
        )

    status_code = _status_code_from_text(raw) or 500
    return ExtractedError(message=raw, status_code=status_code)


def is_auth_error(exc: BaseException) -> bool:
    if isinstance(exc, (OpenAIAuthenticationError, PermissionDeniedError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in _AUTH_STATUS_CODES:
        return True
    if isinstance(exc, Exception):
        if extract_error(exc).status_code in _AUTH_STATUS_CODES:
            return True
    cause = exc.__cause__ or exc.__context__
    if cause is not None and cause is not exc:
        return is_auth_error(cause)
    return False


def is_retryable_error(exc: BaseException) -> bool:
    """Client errors (4xx except 429) should not be retried."""
    if is_auth_error(exc):
        return False
    if isinstance(exc, Exception):
        status = extract_error(exc).status_code
        if 400 <= status < 500 and status != 429:
            return False
    return True


def user_facing_message(exc: Exception, *, context: str = "") -> str:
    if isinstance(exc, AppError) and exc.user_message:
        return exc.user_message
    if is_auth_error(exc):
        return "I don't have access to this data."
    extracted = extract_error(exc)
    if extracted.status_code >= 500 or isinstance(exc, httpx.HTTPStatusError):
        return "The external service is temporarily unavailable. Please try again later."
    if context == "generate_output":
        return "Something went wrong while generating the response. Please try again later."
    return "Something went wrong. Please try again later."


def classify_exception(exc: Exception, *, context: str = "") -> ClassifiedError:
    extracted = extract_error(exc)
    if isinstance(exc, AppError):
        logger.warning("Error in %s: %s", context or "app", extracted.message)
    else:
        logger.error("Error in %s: %s", context or "app", extracted.message, exc_info=exc)

    return ClassifiedError(
        user_message=user_facing_message(exc, context=context),
        detail=ErrorDetail(message=extracted.message, status_code=extracted.status_code),
    )
