import re 
from app.core.security.PII_detector import PIIDetector

class OutputValidator:
    """
    Validate LLM output before returning to the client.
    Catches PII leakage harmful content in responses.
    """

    HARMFUL_PATTERNS = [
        re.compile(r"here('s| is) (how|the way) to (hack|steal|attack)", re.I),
        re.compile(r"password\s+is\s+", re.I),
        re.compile(r"api[_\s]?key\s*[:=]", re.I)
    ]

    def __init__(self):
        self.pii_detector = PIIDetector()
    
    def validate(self, output: str) -> tuple[str, list[str]]:
        """
        Validate and clean output.
        Returns: (cleaned_output, list_of_warnings)
        """
        warnings = []

        pii_found = self.pii_detector.detect(output)
        if pii_found:
            output = self.pii_detector.mask(output)
            warnings.append(f"PII masked in output: {list(pii_found.keys())}")
        
        for pattern in self.HARMFUL_PATTERNS:
            if pattern.search(output):
                output = "[Response blocked: potentially harmful content]"
                warnings.append("Harmful content blocked")

        return output, warnings