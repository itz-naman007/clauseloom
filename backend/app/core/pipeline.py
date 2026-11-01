import asyncio
import hashlib
import re
from .extract import extract
from .segment import segment
from .redact import redact
from .doctype import detect
from .scoring import score, WEIGHTS
from ..rules.engine import detect_flags, key_terms, missing_protections
from ..llm.client import model
from ..config import settings


def fallback(clause, flags, lang):
    risk = max((f.severity for f in flags), key=lambda k: WEIGHTS[k], default="low")
    return {
        "plain_summary": (
            "AI explanation unavailable for this clause. Review the original text alongside the rule findings."
            if lang == "en"
            else "इस शर्त के लिए AI व्याख्या उपलब्ध नहीं है। मूल पाठ और नियमों से मिली जानकारी पढ़ें।"
        ),
        "who_benefits": "unclear",
        "risk_level": risk,
        "why_it_matters": flags[0].explanation_template
        if flags
        else (
            "No configured rule matched. This does not establish that the clause is safe."
            if lang == "en"
            else "कोई निर्धारित नियम नहीं मिला। इसका मतलब यह नहीं कि शर्त सुरक्षित है।"
        ),
        "what_to_ask_or_negotiate": flags[0].suggestion_template
        if flags
        else (
            "Ask for clarification of any unclear obligation." if lang == "en" else "किसी अस्पष्ट ज़िम्मेदारी के बारे में स्पष्टीकरण माँगें।"
        ),
        "evidence_quote": flags[0].matched_text if flags else "",
    }


async def analyze(session, data, filename, requested_type, lang, redact_pii):
    workers = []
    try:
        session.emit("status", {"stage": "extracting"})
        text, pages, warnings = await asyncio.to_thread(extract, data, filename)
        del data
        if session.deleted:
            return
        if redact_pii:
            text = redact(text)
            warnings.append("Pattern redaction is best-effort; names in prose and other identifiers may remain.")
        kind = detect(text) if requested_type == "auto" else requested_type
        await model.available()
        if kind == "other" and requested_type == "auto":
            kind = await model.classify(text)
        if kind == "other":
            warnings.append("This does not clearly look like a rental or freelance contract. Specialized rules are not applied.")
        session.emit("status", {"stage": "segmenting"})
        clauses = segment(text)
        info = {
            "filename": filename,
            "doc_type": kind,
            "pages": pages,
            "clause_count": len(clauses),
            "warnings": warnings,
            "model": settings.model,
            "lang": lang,
            "redacted": redact_pii,
            "jurisdiction": settings.jurisdiction,
            "ttl_minutes": settings.ttl // 60,
        }
        session.result = {"doc_info": info, "clauses": [], "key_terms": {}, "summary": None}
        session.emit("doc_info", info)
        if not model.loaded:
            session.emit(
                "status",
                {
                    "stage": "analyzing",
                    "notice": "Local model unavailable. Deterministic screening will continue; AI explanations are marked unavailable.",
                },
            )
        completed = 0

        async def one(clause):
            nonlocal completed
            flags = detect_flags(clause.text, kind, text, settings.jurisdiction)
            if clause.index == 1:
                flags += missing_protections(text, kind)
            key = hashlib.sha256((clause.text + lang + kind).encode()).hexdigest()
            boilerplate = bool(re.match(r"(?i)^(?:\d+[.)]?\s*)?(?:signatures?|definitions?)\b", clause.text)) and not flags
            ai = session.cache.get(key)
            if not ai and not boilerplate:
                ai = await model.explain(clause, flags, kind, lang)
                if ai:
                    session.cache[key] = ai
            if session.deleted:
                return
            explanation = ai or fallback(clause, flags, lang)
            explanation["risk_level"] = max((f.severity for f in flags), key=lambda k: WEIGHTS[k], default="low")
            result = {
                "clause": clause.model_dump(),
                "flags": [f.model_dump() for f in flags],
                "explanation": explanation,
                "confidence": "grounded" if ai else "rule-only",
                "ai_available": bool(ai),
                "boilerplate": boilerplate,
            }
            session.result["clauses"].append(result)
            session.emit("clause_result", result)
            completed += 1
            session.emit("status", {"stage": "analyzing", "completed": completed, "total": len(clauses)})

        workers = [asyncio.create_task(one(c)) for c in clauses]
        await asyncio.gather(*workers)
        if session.deleted:
            return
        session.emit("status", {"stage": "summarizing"})
        session.result["clauses"].sort(key=lambda r: r["clause"]["index"])
        session.result["key_terms"] = key_terms(text)
        relevant = {
            "rental": {"rent", "deposit", "duration", "notice", "lock_in", "renewal", "jurisdiction"},
            "freelance": {"fee", "duration", "notice", "payment", "renewal", "jurisdiction"},
        }.get(kind, set())

        async def fill_term(field):
            if not session.result["key_terms"][field]:
                value = await model.extract_term(field, clauses)
                if not session.deleted:
                    session.result["key_terms"][field] = value

        await asyncio.gather(*(fill_term(field) for field in relevant))
        if session.deleted:
            return
        session.result["summary"] = score(session.result["clauses"], lang)
        session.emit("key_terms", session.result["key_terms"])
        session.emit("summary", session.result["summary"])
        session.done = True
        session.emit("done", {"session_id": session.id})
    except asyncio.CancelledError:
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        raise
    except Exception as error:
        session.done = True
        session.emit(
            "error",
            {"message": str(error) if isinstance(error, ValueError) else "Analysis could not finish. Please try another file."},
        )
