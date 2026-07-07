import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors.exceptions import AppError
from app.errors.mapping import classify_exception, user_facing_message
from app.models.error import ErrorResponse

logger = logging.getLogger(__name__)


def _error_response(message: str, status_code: int) -> JSONResponse:
    body = ErrorResponse(message=message, status_code=status_code)
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return _error_response(user_facing_message(exc), exc.status_code)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(message=message, status_code=exc.status_code).model_dump(),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        messages = [
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        ]
        message = "; ".join(messages) if messages else "Validation error"
        return _error_response(message, 422)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        classified = classify_exception(exc, context="api")
        return _error_response(
            classified.user_message,
            classified.detail.status_code,
        )
