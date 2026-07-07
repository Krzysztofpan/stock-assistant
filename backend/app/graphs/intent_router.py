import re

from app.config import TOPIC_PRIORITY, Topics

Rule = tuple[re.Pattern[str], tuple[Topics, ...]]

RULES: list[Rule] = [
    (re.compile(r"\b(cena|kurs|price|quote)\b", re.I), ("price",)),
    (re.compile(r"\b(news|newsy|sentiment)\b", re.I), ("news",)),
    (re.compile(r"\b(bilans|fundamenty|earnings|p/e|pe ratio)\b", re.I), ("fundamentals",)),
    (re.compile(r"\b(wykres|historia|history|ohlcv)\b", re.I), ("history",)),
    (re.compile(r"\b(analiza|pełna analiza|full analysis)\b", re.I), ("analysis",)),
    (re.compile(r"\.WA\b|\bGPW\b|polsk(?:a|ie|ich)\s+spół", re.I), ("price",)),
]


def match_topics_from_rules(text: str) -> list[Topics] | None:
    matched: set[Topics] = set()

    for pattern, topics in RULES:
        if pattern.search(text):
            matched.update(topics)

    if not matched:
        return None

    return [topic for topic in TOPIC_PRIORITY if topic in matched]
