from dataclasses import dataclass
from typing import Generic, TypeVar

from tortoise.queryset import QuerySet

from app.errors.exceptions import AppError

T = TypeVar("T")

DEFAULT_LIMIT = 20


def clamp_limit(limit: int, max_limit: int) -> int:
    return min(max(limit, 1), max_limit)


def validate_composite_cursor(
    primary: object | None,
    secondary: object | None,
    *,
    user_message: str = "Invalid pagination parameters.",
) -> None:
    if (primary is None) != (secondary is None):
        raise AppError(
            "Incomplete pagination cursor",
            status_code=400,
            user_message=user_message,
        )


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    has_more: bool


async def fetch_page(
    queryset: QuerySet,
    limit: int,
    *,
    reverse: bool = False,
) -> Page[T]:
    items = await queryset.limit(limit + 1)
    has_more = len(items) > limit
    items = items[:limit]
    if reverse:
        items.reverse()
    return Page(items=items, has_more=has_more)
