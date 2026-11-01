"""Create the fixed, synthetic screening evaluation set (not a legal benchmark)."""

import json
from pathlib import Path

# Manually written positive and contrast examples, not generated from detector regexes.
CASES = [
    (
        "rental",
        "The deposit is non-refundable.",
        ["nonrefundable_deposit"],
        "high",
        "The deposit is refundable after documented deductions.",
    ),
    (
        "rental",
        "The landlord may deduct charges at sole discretion.",
        ["unitemized_deductions"],
        "medium",
        "Deductions require itemized receipts.",
    ),
    (
        "rental",
        "The lock-in is binding on the tenant only.",
        ["tenant_only_lock"],
        "high",
        "Both parties have equal exit rights.",
    ),
    (
        "rental",
        "The agreement will automatically renew every year.",
        ["auto_renewal"],
        "medium",
        "The agreement does not automatically renew.",
    ),
    (
        "rental",
        "The landlord may enter without notice.",
        ["entry_without_notice"],
        "high",
        "Entry requires 24 hours prior written notice.",
    ),
    (
        "rental",
        "Early exit triggers forfeiture of the deposit.",
        ["early_exit_penalty"],
        "high",
        "Early exit carries no penalty.",
    ),
    ("rental", "The tenant shall pay for all repairs.", ["major_repairs"], "high", "The landlord pays for structural repairs."),
    ("rental", "The landlord may evict without cause.", ["eviction"], "high", "The landlord cannot evict without cause."),
    ("rental", "No pets are allowed.", ["restrictions"], "low", "Pets and guests are allowed."),
    ("rental", "Interest is compounded monthly.", ["compound_interest"], "high", "Interest does not compound."),
    (
        "rental",
        "Monthly rent is INR 10,000. Deposit is INR 40,000.",
        ["large_deposit"],
        "medium",
        "Monthly rent is INR 10,000. Deposit is INR 20,000.",
    ),
    ("rental", "The lock-in period is 12 months.", ["long_lock_in"], "high", "The lock-in period is 3 months."),
    ("rental", "Rent will increase by 15% annually.", ["high_escalation"], "medium", "Rent will increase by 5% annually."),
    ("rental", "A late fee of 3% per month applies.", ["high_late_fee"], "high", "A late fee of 1% per month applies."),
    (
        "rental",
        "Rent escalation is at the landlord discretion.",
        ["unspecified_escalation"],
        "medium",
        "Rent is fixed throughout the term.",
    ),
    (
        "rental",
        "Tenant gives 90 days notice. Landlord gives 15 days notice.",
        ["notice_asymmetry"],
        "medium",
        "Tenant gives 30 days notice. Landlord gives 30 days notice.",
    ),
    ("rental", "The term is 24 months.", ["registration_check"], "low", "The term is 24 months and registration is required."),
    ("freelance", "Services automatically renew each year.", ["auto_renewal"], "medium", "Services do not automatically renew."),
    (
        "freelance",
        "Payment depends on the client's satisfaction.",
        ["payment_satisfaction"],
        "high",
        "Payment is due within 30 days of invoice.",
    ),
    (
        "freelance",
        "The client may request unlimited revisions.",
        ["unlimited_scope"],
        "high",
        "The fee covers two rounds of revisions.",
    ),
    (
        "freelance",
        "The freelancer assigns all pre-existing tools.",
        ["ip_preexisting"],
        "high",
        "The freelancer retains all pre-existing tools.",
    ),
    (
        "freelance",
        "Intellectual property transfers before payment.",
        ["ip_before_payment"],
        "high",
        "Intellectual property transfers only after payment.",
    ),
    (
        "freelance",
        "A non-compete applies for 24 months throughout India.",
        ["non_compete"],
        "high",
        "There is no non-compete requirement.",
    ),
    (
        "freelance",
        "The client may terminate immediately.",
        ["one_sided_termination"],
        "high",
        "Both parties may terminate on 30 days written notice.",
    ),
    (
        "freelance",
        "The freelancer accepts unlimited liability.",
        ["unlimited_liability"],
        "high",
        "Liability is capped at the project fee.",
    ),
    ("freelance", "Liquidated damages apply to delayed delivery.", ["damages"], "high", "No liquidated damages are payable."),
    (
        "freelance",
        "Confidentiality continues indefinitely.",
        ["perpetual_confidentiality"],
        "medium",
        "Confidentiality ends after two years.",
    ),
    (
        "freelance",
        "The freelancer bears all arbitration costs.",
        ["dispute_costs"],
        "high",
        "Arbitration costs are shared equally.",
    ),
    (
        "freelance",
        "Arbitration in London will resolve disputes.",
        ["foreign_forum"],
        "medium",
        "Disputes are mediated online by mutual agreement.",
    ),
    ("freelance", "Exclusivity applies during the project.", ["exclusivity"], "medium", "This engagement is non-exclusive."),
    ("freelance", "Invoices are payable net-90.", ["slow_payment"], "high", "Invoices are payable net-15."),
]

if __name__ == "__main__":
    rows = []
    for kind, positive, flags, risk, negative in CASES:
        rows += [
            {"doc_type": kind, "text": positive, "flags": flags, "risk": risk},
            {"doc_type": kind, "text": negative, "flags": [], "risk": "low"},
        ]
    path = Path(__file__).resolve().parents[1] / "eval/labeled_clauses.jsonl"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} labeled clauses")
