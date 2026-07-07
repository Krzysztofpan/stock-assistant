from pydantic import BaseModel


class ErrorDetail(BaseModel):
    message: str
    status_code: int


class ErrorResponse(BaseModel):
    """Unified HTTP error body returned by all API error handlers."""

    message: str
    status_code: int
