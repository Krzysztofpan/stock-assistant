from functools import lru_cache

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}


@lru_cache
def _get_nlp_engine():
    provider = NlpEngineProvider(nlp_configuration=configuration)
    return provider.create_engine()

_ENTITY_MAP = {
    "EMAIL_ADDRESS": "email",
    "PHONE_NUMBER": "phone",
    "CREDIT_CARD": "credit_card",
    "US_SSN": "ssn",
}

_PII_ENTITIES = list(_ENTITY_MAP.keys())


class PIIDetector:
    """
    Detect and mask personally identifiable information.
    Works on BOTH input (before LLM) and output (before client).
    """

    def __init__(self):
        self.analyzer = AnalyzerEngine(
            nlp_engine=_get_nlp_engine(),
            supported_languages=["en"],
        )
        self.anonymizer = AnonymizerEngine()

    def _analyze(self, text: str):
        # Presidio requires a language; pattern-based entities below work on mixed PL/EN text.
        return self.analyzer.analyze(
            text=text,
            language="en",
            entities=_PII_ENTITIES,
        )

    def detect(self, text: str) -> dict[str, list[str]]:
        """Detect PII types present in text."""
        detected: dict[str, list[str]] = {}
        for result in self._analyze(text):
            key = _ENTITY_MAP.get(result.entity_type)
            if key is None:
                continue
            detected.setdefault(key, []).append(text[result.start : result.end])
        return detected

    def mask(self, text: str) -> str:
        """Replace all PII with Presidio redaction markers."""
        results = self._analyze(text)
        if not results:
            return text
        return self.anonymizer.anonymize(text=text, analyzer_results=results).text


@lru_cache
def get_pii_detector() -> PIIDetector:
    return PIIDetector()


def reset_pii_caches() -> None:
    get_pii_detector.cache_clear()
    _get_nlp_engine.cache_clear()
