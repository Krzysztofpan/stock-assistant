from transformers import pipeline
from app.config import get_settings, Settings
from app.models.routing import SafetyVerdict
import asyncio 

settings = get_settings()

class InjectionGateService:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._pipeline = None  # lazy

    @property
    def is_warmed(self) -> bool:
        return self._pipeline is not None

    def _get_pipeline(self):
        if self._pipeline is None:
            self._pipeline = pipeline(
                "text-classification",
                model=self._settings.injection_model,
            )
        return self._pipeline

    def warmup(self) -> None:
        self._get_pipeline()

    def _extract_scores(self, results: list) -> dict[str, float]:
        if not results:
            return {}

        first = results[0]
        if isinstance(first, list):
            return {r["label"]: r["score"] for r in first}

        if isinstance(first, dict) and "label" in first:
            if all(isinstance(r, dict) and "label" in r for r in results):
                return {r["label"]: r["score"] for r in results}

            label, score = first["label"], first["score"]
            if label == "unsafe":
                return {"unsafe": score, "safe": 1.0 - score}
            return {"safe": score, "unsafe": 1.0 - score}

        return {}

    def _classify_sync(self, text: str) -> SafetyVerdict:
        results = self._get_pipeline()(
            text,
            truncation=True,
            max_length=self._settings.injection_max_length,
            return_all_scores=True,
        )
        scores = self._extract_scores(results)
        unsafe_score = scores.get("unsafe", 0.0)
        is_safe = unsafe_score < self._settings.injection_threshold
        return SafetyVerdict(is_safe=is_safe, confidence=unsafe_score)

    async def check_safety(self, text: str) -> SafetyVerdict:
        return await asyncio.to_thread(self._classify_sync, text)
