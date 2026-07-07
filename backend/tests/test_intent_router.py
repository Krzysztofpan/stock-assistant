import pytest

from app.graphs.intent_router import match_topics_from_rules


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Jaka cena AAPL?", ["price"]),
        ("What is the current price of Tesla?", ["price"]),
        ("Newsy o TSLA", ["news"]),
        ("Latest news and sentiment for Apple", ["news"]),
        ("Bilans Microsoft", ["fundamentals"]),
        ("Show me P/E ratio for NVDA", ["fundamentals"]),
        ("Historia CDPROJEKT.WA", ["price", "history"]),
        ("OHLCV chart for AAPL", ["history"]),
        ("Pełna analiza CDPROJEKT", ["analysis"]),
        ("Analiza spółki na GPW", ["price", "analysis"]),
        ("Co to jest fotosynteza?", None),
        ("Tell me about World War 2", None),
    ],
)
def test_match_topics_from_rules(question, expected):
    assert match_topics_from_rules(question) == expected
