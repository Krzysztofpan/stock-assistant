import re 
from app.core.security.PII_detector import PIIDetector

from langsmith import traceable
from app.core.security.input_sanitizer import InputSanitizer
from app.core.security.output_validator import OutputValidator

class SecurityPipeline:
    """
    Full security pipeline that processes input and output.
    This is the signle class you wire into your API.
    """

    def __init__(self):
        self.sanitizer  = InputSanitizer()
        self.pii_detector = PIIDetector()
        self.output_validator = OutputValidator()

    @traceable(name="security_check_input")
    def check_input(self, text: str) -> tuple[bool, str, list[str]]:
        """
        Process input through security checks.
        Returns: (is_allowed, cleaned_text, security_notes)
        """

        notes = []

        is_safe, reason = self.sanitizer.check(text)
        if not is_safe:
            return False, "", [reason]

        cleaned = self.sanitizer.clean(text)

        pii_found = self.pii_detector.detect(cleaned)

        if pii_found:
            cleaned = self.pii_detector.mask(cleaned)
            notes.append(f"Input PII masked: {list(pii_found.keys())}")

            return True, cleaned, notes
        return True, cleaned, notes

    @traceable(name="security_check_output")
    def check_output(self, text: str) -> tuple[str, list[str]]:
        """
        Validate output before returning to client.
        Returns (cleaned_output, warnings)
        """
        return self.output_validator.validate(text)