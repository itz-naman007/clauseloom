"""Source-preserving segmentation; offsets refer to the analyzed text."""

import re
from ..models import Clause

HEADING = re.compile(r"(?m)^(?=\d+(?:\.\d+)*[.)]?\s+|\([a-z]\)\s+|Clause\s+\d+|ARTICLE\s+[IVX]+|[A-Z][A-Z /&-]{4,}\s*$)")


def segment(text: str) -> list[Clause]:
    starts = sorted(set([0] + [m.start() for m in HEADING.finditer(text)] + [len(text)]))
    has_headings = len(starts) > 2
    if not has_headings:
        starts = sorted(set([0] + [m.end() for m in re.finditer(r"\n\s*\n", text)] + [len(text)]))
    spans = []
    for a, b in zip(starts, starts[1:]):
        words = list(re.finditer(r"\S+", text[a:b]))
        while len(words) > 350:
            limit = a + words[350].start()
            boundary = list(re.finditer(r"[.!?]\s+", text[a:limit]))
            end = a + boundary[-1].end() if boundary and boundary[-1].end() > 200 else limit
            spans.append((a, end))
            a = end
            words = list(re.finditer(r"\S+", text[a:b]))
        if text[a:b].strip():
            if not has_headings and spans and len(text[a:b].split()) < 8 and b - spans[-1][0] < 1800:
                spans[-1] = (spans[-1][0], b)
            else:
                spans.append((a, b))
    if len(spans) > 60:
        raise ValueError("This demo supports up to 60 clauses. Please upload a shorter section.")
    clauses = []
    for i, (a, b) in enumerate(spans):
        a += len(text[a:b]) - len(text[a:b].lstrip())
        b -= len(text[a:b]) - len(text[a:b].rstrip())
        clauses.append(
            Clause(
                id=f"clause-{i + 1}",
                index=i + 1,
                heading=text[a:b].splitlines()[0][:90],
                text=text[a:b],
                page=text[:a].count("\f") + 1,
                char_start=a,
                char_end=b,
            )
        )
    return clauses
