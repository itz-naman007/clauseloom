import re


def normalize(text: str) -> str:
    return " ".join(text.split())


def neutralize(text: str) -> str:
    text = re.sub(r"</?(?:clause|system|assistant|user)[^>]*>", "[delimiter removed]", text, flags=re.I)
    return re.sub(
        r"(?im)[^\n.!?]*(?:ignore (?:all |previous |prior )*instructions|reveal (?:the |your )?(?:system|prompt)|you are now|system prompt)[^\n.!?]*",
        "[instruction-like text removed]",
        text,
    )


def grounded(output: dict, source: str) -> bool:
    quote = output.get("evidence_quote", "")
    if not quote or normalize(quote) not in normalize(source):
        return False
    # Reject invented numeric tokens across explanatory fields.
    allowed = set(re.findall(r"\d+(?:[.,]\d+)*", source))
    claims = " ".join(output.get(k, "") for k in ["plain_summary", "why_it_matters", "what_to_ask_or_negotiate"])
    return set(re.findall(r"\d+(?:[.,]\d+)*", claims)) <= allowed
