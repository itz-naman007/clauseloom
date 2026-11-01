WEIGHTS = {"high": 15, "medium": 7, "low": 2}


def score(results: list[dict], lang="en") -> dict:
    flags = [f for r in results for f in r["flags"]]
    counts = {level: sum(f["severity"] == level for f in flags) for level in WEIGHTS}
    total = min(100, sum(counts[k] * WEIGHTS[k] for k in WEIGHTS))
    labels = (
        ["Looks fairly standard", "Needs attention", "Risky: negotiate before signing"]
        if lang == "en"
        else ["काफी सामान्य लगता है", "ध्यान देने की ज़रूरत है", "हस्ताक्षर से पहले शर्तों पर बात करें"]
    )
    return {
        "overall_score": total,
        "label": labels[0 if total <= 25 else 1 if total <= 55 else 2],
        "counts": counts,
        "weights": WEIGHTS,
        "formula": f"min(100, {counts['high']} × 15 + {counts['medium']} × 7 + {counts['low']} × 2)",
        "top_flags": sorted(flags, key=lambda f: WEIGHTS[f["severity"]], reverse=True)[:3],
        "verdict": "Review the flagged terms and verify anything important with a qualified lawyer."
        if lang == "en"
        else "चिह्नित शर्तें पढ़ें और ज़रूरी बातों की पुष्टि योग्य वकील से करें।",
    }
