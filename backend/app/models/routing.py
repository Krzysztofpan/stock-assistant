from pydantic import BaseModel


class SafetyVerdict(BaseModel):
    is_safe: bool
    confidence: float
