# Evaluation results

The rule engine was checked against 62 synthetic, hand-labeled clauses used during development. This measures regression coverage, not accuracy on unseen contracts.

| Rule metric | Result |
|---|---:|
| Flag precision | 100.0% |
| Flag recall | 100.0% |
| True / false positives / false negatives | 31 / 0 / 0 |
| Seconds per clause | 0.0006 |

Unit tests cover document-wide missing-protection checks separately from this clause-level corpus.

## Local model comparison

| Model | Clauses | Schema validity (first attempt) | Grounded outputs | Risk agreement | Seconds/clause |
|---|---:|---:|---:|---:|---:|
| qwen2.5:3b | 6 | 83.3% | 0.0% | 50.0% | 10.81 |
| qwen2.5:1.5b | 6 | 100.0% | 16.7% | 50.0% | 2.51 |

These model results use raw first responses, before the app's repair attempt and rule-enforced severity. Failed requests count as failures. With only six clauses per model in the recorded comparison, the results are too limited to rank models. The low grounding rates show why the app needs output checks and rule-only fallback.

## Rule mismatches

```json
[]
```
