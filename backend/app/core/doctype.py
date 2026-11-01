import re


def detect(text: str) -> str:
    rental = len(re.findall(r"\b(?:tenant|landlord|rent|lease|licensee)\b", text, re.I))
    freelance = len(re.findall(r"\b(?:freelancer|client|deliverables|invoice|services)\b", text, re.I))
    return "other" if max(rental, freelance) < 2 else ("rental" if rental > freelance else "freelance")
