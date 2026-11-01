import json
from pathlib import Path
import pytest
from app.rules.engine import detect_flags

CASES = [
    json.loads(line)
    for line in (Path(__file__).resolve().parents[2] / "eval/labeled_clauses.jsonl").read_text(encoding="utf-8").splitlines()
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["text"][:55])
def test_rule_positive_and_negative(case):
    assert {f.flag_id for f in detect_flags(case["text"], case["doc_type"])} == set(case["flags"])
