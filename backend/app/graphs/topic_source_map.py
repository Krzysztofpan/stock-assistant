from app.config import Topics, get_settings
from app.core.tools.mcp_tools import SourceName

TOPIC_SOURCE_MAP: dict[Topics, tuple[SourceName, ...]] = {
    "price": ("yfinance",),
    "news": ("finnhub",),
    "fundamentals": ("eodhd", "yfinance"),
    "history": ("eodhd",),
    "analysis": ("yfinance", "finnhub", "eodhd"),
    "not related": (),
}

SOURCE_PRIORITY: tuple[SourceName, ...] = ("yfinance", "finnhub", "eodhd")


def _enabled_sources() -> set[SourceName]:
    settings = get_settings()
    enabled: set[SourceName] = set()

    if settings.enable_yfinance:
        enabled.add("yfinance")
    if settings.enable_finnhub:
        enabled.add("finnhub")
    if settings.enable_eodhd:
        enabled.add("eodhd")

    return enabled


def resolve_sources_for_topics(topics: list[Topics]) -> list[SourceName]:
    enabled = _enabled_sources()
    selected: set[SourceName] = set()

    for topic in topics:
        for source in TOPIC_SOURCE_MAP.get(topic, ()):
            if source in enabled:
                selected.add(source)

    return [source for source in SOURCE_PRIORITY if source in selected]
