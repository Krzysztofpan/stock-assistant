class AppError(Exception):
    """Base application error with HTTP status."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        user_message: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.user_message = user_message
        super().__init__(message)


class AuthenticationError(AppError):
    def __init__(self, message: str, *, user_message: str | None = None):
        super().__init__(
            message,
            status_code=403,
            user_message=user_message or "I don't have access to this data.",
        )


class ExternalServiceError(AppError):
    def __init__(self, message: str, *, status_code: int = 502, user_message: str | None = None):
        super().__init__(
            message,
            status_code=status_code,
            user_message=user_message or "The external service is temporarily unavailable. Please try again later.",
        )


class InputBlockedError(AppError):
    def __init__(self):
        super().__init__(
            "Input blocked by security filters",
            status_code=400,
            user_message="Your message was blocked by our security filters.",
        )
