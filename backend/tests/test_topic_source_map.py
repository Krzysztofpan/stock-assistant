import pytest

from app.graphs.topic_source_map import resolve_sources_for_topics


@pytest.fixture(autouse=True)
def enable_all_sources(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("ENABLE_EODHD", "true")
    monkeypatch.setenv("ENABLE_FINNHUB", "true")
    monkeypatch.setenv("ENABLE_YFINANCE", "true")
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("topics", "expected"),
    [
        (["price"], ["yfinance"]),
        (["news"], ["finnhub"]),
        (["fundamentals"], ["yfinance", "eodhd"]),
        (["history"], ["eodhd"]),
        (["analysis"], ["yfinance", "finnhub", "eodhd"]),
        (["not related"], []),
        (["price", "history"], ["yfinance", "eodhd"]),
        (["news", "fundamentals"], ["yfinance", "finnhub", "eodhd"]),
    ],
)
def test_resolve_sources_for_topics(topics, expected):
    assert resolve_sources_for_topics(topics) == expected


def test_resolve_sources_for_topics_respects_disabled_sources(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("ENABLE_EODHD", "false")
    monkeypatch.setenv("ENABLE_FINNHUB", "false")
    monkeypatch.setenv("ENABLE_YFINANCE", "true")

    assert resolve_sources_for_topics(["analysis"]) == ["yfinance"]
    assert resolve_sources_for_topics(["history"]) == []

    get_settings.cache_clear()
