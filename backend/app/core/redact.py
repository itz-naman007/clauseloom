import re


def redact(text: str) -> str:
    """Best-effort pattern redaction; not a guarantee of anonymity."""
    patterns = [
        (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[EMAIL]"),
        (r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b", "[AADHAAR]"),
        (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN]"),
        (r"(?<!\w)(?:\+91[ -]?)?[6-9]\d{9}\b", "[PHONE]"),
        (r"(?im)((?:name|landlord|tenant|client|freelancer)\s*:\s*)[A-Za-z][A-Za-z .]{2,60}(?=\n|$)", r"\1[NAME]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text
