from pydantic import BaseModel
from typing import Literal

class SafetyVerdict(BaseModel):
    is_safe: bool
    confidence: float