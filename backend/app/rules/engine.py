"""Conservative, explainable screening rules; not determinations of legality."""

import re
from pathlib import Path
import yaml
from ..models import Flag

# id, severity, category, positive pattern, exclusion, explanation, question
RULES = {
    "rental": [
        (
            "nonrefundable_deposit",
            "high",
            "Deposit",
            r"(?:deposit.{0,70}non[- ]refundable|non[- ]refundable.{0,70}deposit)",
            r"",
            "You may not recover your deposit even if there is no damage.",
            "Can the deposit be refundable, with documented deductions only?",
        ),
        (
            "unitemized_deductions",
            "medium",
            "Deposit",
            r"(?:deduct.{0,80}(?:without itemi|sole discretion)|no itemi[sz]ed)",
            r"",
            "Deductions may be difficult to check.",
            "Can all deductions require an itemized statement and receipts?",
        ),
        (
            "tenant_only_lock",
            "high",
            "Lock-in",
            r"(?:tenant only|only the tenant).{0,60}(?:lock|bound)|lock.{0,80}(?:tenant only|only the tenant)",
            r"",
            "Only the tenant appears bound by this lock-in.",
            "Can both parties have equal exit rights?",
        ),
        (
            "auto_renewal",
            "medium",
            "Renewal",
            r"automatic(?:ally)? renew|auto[- ]renew|evergreen",
            r"(?:not|no) automatic|does not automatically",
            "The agreement may continue unless you act before a deadline.",
            "Can renewal require written agreement from both parties?",
        ),
        (
            "entry_without_notice",
            "high",
            "Privacy",
            r"(?:enter|entry|access).{0,80}(?:without (?:prior )?notice|at any time)",
            r"except.{0,20}emergenc",
            "Unannounced access can affect your privacy.",
            "Can entry require prior notice except in emergencies?",
        ),
        (
            "early_exit_penalty",
            "high",
            "Termination",
            r"(?:early (?:exit|termination).{0,100}(?:penalt|forfeit|liquidated)|forfeit.{0,70}deposit)",
            r"no (?:penalt|forfeit)",
            "Leaving early could cost more than expected.",
            "Can the exit charge be limited to documented losses?",
        ),
        (
            "major_repairs",
            "high",
            "Maintenance",
            r"tenant.{0,100}(?:all repairs|structural repairs|major repairs)",
            r"not responsible|landlord (?:pays|bears)",
            "Major building costs may be shifted to you.",
            "Can the landlord cover structural and major repairs?",
        ),
        (
            "eviction",
            "high",
            "Termination",
            r"(?:evict|vacate|terminate).{0,90}(?:without (?:any )?cause|immediately|24 hours|three days|3 days)",
            r"cannot|may not|shall not",
            "You could have little time to find another home.",
            "Can termination require a stated reason and reasonable written notice?",
        ),
        (
            "restrictions",
            "low",
            "Restrictions",
            r"(?:no|prohibited|not permitted).{0,30}(?:pets|guests|subletting)|(?:pets|guests|subletting).{0,30}(?:prohibited|not permitted)",
            r"",
            "Check whether these restrictions fit your needs.",
            "Can permitted guests, pets and subletting be clarified?",
        ),
        (
            "compound_interest",
            "high",
            "Late fees",
            r"compound(?:ed|ing)? (?:monthly|interest)|interest.{0,30}compound",
            r"not compound|no compound",
            "Interest could accumulate on earlier interest.",
            "Can late charges be simple, capped and proportionate?",
        ),
    ],
    "freelance": [
        (
            "auto_renewal",
            "medium",
            "Renewal",
            r"automatic(?:ally)? renew|auto[- ]renew|evergreen",
            r"not automatic|no automatic|does not automatically",
            "The engagement may continue without a fresh agreement.",
            "Can renewal require both parties to opt in?",
        ),
        (
            "payment_satisfaction",
            "high",
            "Payment",
            r"payment.{0,90}(?:client.{0,15}satisfaction|sole discretion)",
            r"within \d+ days",
            "Payment may depend on a subjective decision without a clear deadline.",
            "Can we agree objective acceptance criteria and a payment deadline?",
        ),
        (
            "unlimited_scope",
            "high",
            "Scope",
            r"unlimited (?:revisions|changes|scope)|revisions.{0,30}without limit",
            r"no unlimited",
            "The work may grow without additional pay.",
            "Can we cap revision rounds and price additional work separately?",
        ),
        (
            "ip_preexisting",
            "high",
            "Intellectual property",
            r"(?:assign|transfer|own).{0,120}(?:pre[- ]existing|all prior|background)",
            r"exclud|retain",
            "Tools or work created before this project may be transferred.",
            "Can pre-existing tools and materials remain mine?",
        ),
        (
            "ip_before_payment",
            "high",
            "Intellectual property",
            r"(?:IP|intellectual property|rights).{0,100}(?:before payment|upon creation|on creation)",
            r"only after|not until",
            "Rights may transfer before you have been paid.",
            "Can ownership transfer only after full payment?",
        ),
        (
            "non_compete",
            "high",
            "Restrictions",
            r"non[- ]compet|non[- ]solicit",
            r"no non[- ]|not subject",
            "This restriction could limit future work; scope and duration matter.",
            "Can we remove or narrowly limit the duration, geography and clients covered?",
        ),
        (
            "one_sided_termination",
            "high",
            "Termination",
            r"client.{0,90}terminat.{0,60}(?:immediately|without notice|at any time)",
            r"cannot|may not",
            "The client may end the engagement before you recover your costs.",
            "Can notice and a fee for completed and reserved work apply?",
        ),
        (
            "unlimited_liability",
            "high",
            "Liability",
            r"unlimited liability|liability.{0,30}uncapped|indemnif.{0,50}(?:all|any).{0,30}(?:claims|losses)",
            r"no unlimited|shall not indemnify",
            "Your financial exposure may exceed the project fee.",
            "Can liability be capped and indemnity limited to losses you cause?",
        ),
        (
            "damages",
            "high",
            "Liability",
            r"liquidated damages|penalty.{0,40}(?:delay|breach)",
            r"no (?:liquidated|penalty)",
            "A preset charge may apply if something goes wrong.",
            "Can charges be proportionate, capped and tied to your responsibility?",
        ),
        (
            "perpetual_confidentiality",
            "medium",
            "Confidentiality",
            r"confidential.{0,100}(?:forever|perpetual|indefinite|no end date)",
            r"except trade secrets",
            "The confidentiality obligation has no clear end date.",
            "Can ordinary information have a defined confidentiality period?",
        ),
        (
            "dispute_costs",
            "high",
            "Disputes",
            r"(?:arbitration|dispute).{0,100}(?:solely|all costs).{0,40}freelancer|freelancer.{0,70}(?:all|sole).{0,20}(?:arbitration|legal) costs",
            r"",
            "You may bear dispute costs regardless of outcome.",
            "Can dispute costs be shared fairly?",
        ),
        (
            "foreign_forum",
            "medium",
            "Disputes",
            r"(?:arbitration|courts|jurisdiction).{0,50}(?:London|New York|Singapore|foreign|overseas)",
            r"",
            "Resolving a dispute in this location could be expensive.",
            "Can we use a mutually accessible location or online mediation?",
        ),
        (
            "exclusivity",
            "medium",
            "Restrictions",
            r"exclusiv(?:e|ity)|may not work for (?:other|any other)",
            r"non[- ]exclusive|no exclusivity|not exclusive",
            "The contract may restrict other paid work.",
            "Can exclusivity be removed or limited and compensated?",
        ),
    ],
}


def thresholds(jurisdiction="india"):
    if jurisdiction not in {"india", "default"}:
        raise ValueError("Unsupported jurisdiction")
    return yaml.safe_load((Path(__file__).parent / f"{jurisdiction}.yaml").read_text())


def key_terms(text: str) -> dict:
    patterns = {
        "rent": r"(?:monthly rent|rent per month|rent)\s*(?:is|of|:|shall be)?\s*(?:INR|Rs\.?|₹)\s*[\d,]+",
        "fee": r"(?:project fee|fee|total fee)\s*(?:is|of|:)?\s*(?:INR|Rs\.?|₹)\s*[\d,]+",
        "deposit": r"(?:security )?deposit\s*(?:is|of|:|shall be)?\s*(?:INR|Rs\.?|₹)\s*[\d,]+",
        "duration": r"(?:term|duration|period)\s*(?:is|of|:)?\s*\d+\s*(?:months?|years?|weeks?)",
        "notice": r"[^.\n]{0,60}\b\d+[- ]days?[’\x27]?\s*(?:written )?notice[^.\n]{0,60}",
        "lock_in": r"lock[- ]in\s*(?:period)?\s*(?:is|of|:)?\s*\d+\s*months?",
        "payment": r"net[- ]\d+|payment\s*(?:is due|due|within)\s*\d+\s*days",
        "renewal": r"[^.\n]{0,40}(?:automatic(?:ally)? renew|auto[- ]renew)[^.\n]{0,80}",
        "jurisdiction": r"(?:jurisdiction|arbitration|courts)\s*(?:in|of|:)?\s*[^.\n]{2,90}",
    }
    return {key: (m.group().strip() if (m := re.search(pattern, text, re.I)) else None) for key, pattern in patterns.items()}


def detect_flags(text: str, doc_type: str, full_text: str = "", jurisdiction="india") -> list[Flag]:
    cfg = thresholds(jurisdiction)
    flags = []

    def add(fid, severity, category, evidence, explanation, suggestion):
        flags.append(
            Flag(
                flag_id=fid,
                severity=severity,
                category=category,
                matched_text=evidence,
                explanation_template=explanation,
                suggestion_template=suggestion,
            )
        )

    for fid, severity, category, pattern, exclude, explanation, suggestion in RULES.get(doc_type, []):
        match = re.search(pattern, text, re.I | re.S)
        if match and not (exclude and re.search(exclude, text, re.I)):
            add(fid, severity, category, match.group(), explanation, suggestion)
    if doc_type == "rental":
        terms = key_terms(full_text or text)

        def amount(value):
            m = re.search(r"(?:INR|Rs\.?|₹)\s*([\d,]+)", value or "", re.I)
            return float(m[1].replace(",", "")) if m else 0

        if (
            terms["deposit"]
            and terms["deposit"] in text
            and amount(terms["rent"]) > 0
            and amount(terms["deposit"]) > cfg["deposit_months"] * amount(terms["rent"])
        ):
            add(
                "large_deposit",
                "medium",
                "Deposit",
                terms["deposit"],
                cfg["qualification"],
                "Can the deposit be reduced, and can we verify the applicable state rules?",
            )
        numeric = [
            (
                "long_lock_in",
                "high",
                "Lock-in",
                r"lock[- ]in\s*(?:period)?\s*(?:is|of|:)?\s*(\d+)\s*months?",
                cfg["lock_in_months"],
                "A long lock-in limits your flexibility.",
                "Can we shorten the lock-in and agree a reasonable exit option?",
            ),
            (
                "high_escalation",
                "medium",
                "Renewal",
                r"(?:escalat\w*|increas\w*).{0,30}?(\d+(?:\.\d+)?)\s*%",
                cfg["escalation_percent"],
                "The increase is above the configured annual review threshold; verify its frequency.",
                "Can the increase and its frequency be capped?",
            ),
            (
                "high_late_fee",
                "high",
                "Late fees",
                r"(?:late fee|interest).{0,25}?(\d+(?:\.\d+)?)\s*%\s*(?:per month|monthly)",
                cfg["late_interest_percent"],
                "Monthly late charges could add up quickly.",
                "Can late fees be capped and include a grace period?",
            ),
        ]
        for fid, sev, cat, pattern, limit, explanation, question in numeric:
            m = re.search(pattern, text, re.I)
            if m and float(m[1]) > limit:
                add(fid, sev, cat, m[0], explanation, question)
        if re.search(r"escalat|rent increase", text, re.I) and not re.search(
            r"\d+\s*%|no increase|not increase|fixed", text, re.I
        ):
            add(
                "unspecified_escalation",
                "medium",
                "Renewal",
                text,
                "Rent increases are not clearly quantified.",
                "Can the amount and timing of increases be specified?",
            )
        tenant = re.search(r"tenant.{0,50}?(\d+)[- ]days?.{0,20}notice", full_text or text, re.I)
        landlord = re.search(r"landlord.{0,50}?(\d+)[- ]days?.{0,20}notice", full_text or text, re.I)
        if tenant and landlord and int(tenant[1]) > int(landlord[1]) and tenant[0] in text:
            add(
                "notice_asymmetry",
                "medium",
                "Termination",
                tenant[0],
                "The tenant must give more notice than the landlord.",
                "Can the notice periods be equal?",
            )
        term = re.search(r"(?:term|duration)\s*(?:of|is)?\s*(\d+)\s*months", text, re.I)
        if term and int(term[1]) > cfg["registration_months"] and not re.search(r"registr", full_text or text, re.I):
            add(
                "registration_check",
                "low",
                "Registration",
                term[0],
                "Verify registration and stamp duty rules in your state.",
                "Does this term require registration or additional stamp duty?",
            )
    if doc_type == "freelance":
        m = re.search(r"net[- ](\d+)|payment\s*(?:within|due|is due)\s*(\d+)\s*days", text, re.I)
        if m and int(m[1] or m[2]) >= cfg["payment_days"]:
            add(
                "slow_payment",
                "high",
                "Payment",
                m[0],
                "A long payment cycle may strain your cash flow.",
                "Can payment be due within 30 days with an upfront milestone?",
            )
    return flags


def missing_protections(full_text: str, doc_type: str) -> list[Flag]:
    """Document-wide absence findings are explicitly not quoted evidence."""
    if doc_type != "freelance":
        return []
    flags = []
    for fid, pattern, category, explanation, question in [
        (
            "missing_late_protection",
            r"late.{0,30}(?:payment|fee|interest)|overdue|suspend work",
            "Payment",
            "No late-payment protection was detected in the supplied text.",
            "Can overdue payments accrue interest or allow work to pause?",
        ),
        (
            "missing_kill_fee",
            r"kill fee|cancellation fee|pay.{0,50}(?:completed work|work completed)",
            "Termination",
            "No cancellation payment protection was detected in the supplied text.",
            "Can completed work and reserved time be paid if the project is cancelled?",
        ),
    ]:
        if not re.search(pattern, full_text, re.I):
            flags.append(
                Flag(
                    flag_id=fid,
                    severity="medium",
                    category=category,
                    matched_text="",
                    explanation_template=explanation,
                    suggestion_template=question,
                )
            )
    return flags
