# Evaluation results

Synthetic, hand-labeled development set: 62 clauses. This is not held-out legal validation.

| Rule metric | Result |
|---|---:|
| Flag precision | 100.0% |
| Flag recall | 100.0% |
| True / false positives / false negatives | 31 / 0 / 0 |
| Seconds per clause | 0.0006 |

Document-wide missing-protection checks are covered separately by unit tests. Numbers do not estimate performance on unseen contracts.

## Local model comparison

| Model | Clauses | Schema validity (first attempt) | Grounded outputs | Risk agreement | Seconds/clause |
|---|---:|---:|---:|---:|---:|
| qwen2.5:3b | 6 | 83.3% | 0.0% | 50.0% | 10.81 |
| qwen2.5:1.5b | 6 | 100.0% | 16.7% | 50.0% | 2.51 |

Model evaluation measures raw first attempts independently from rule-enforced production risk levels. Failed requests count as failures. Small subsets are smoke comparisons, not model rankings.

## Rule mismatches

```json
[]
```
