# Verification record

Recorded on 1 November 2026. These results cover local checks and the initial
GitHub Actions run; hosted acceptance testing is still pending.

| Check | Result |
| --- | --- |
| Backend | 98 tests passed; Ruff and dependency compatibility checks passed |
| Frontend | Unit test, TypeScript check and production build passed |
| Application dependencies | Python and npm audits reported no known advisories in the audited sets |
| Docker builds | Standard Compose app image and bundled CPU image built successfully |
| Live file uploads | PDF, DOCX, PNG and JPEG checks passed, including OCR |
| Browser | Results, search, theme, keyboard dismissal of the privacy dialog, PDF download and deletion worked |
| Mobile layout | No horizontal overflow at a 390 CSS-pixel viewport |
| Report rendering | Mixed English/Hindi glyphs checked visually |

## CPU review trial

With the bundled `qwen2.5:1.5b` model and a limit of two CPUs / 4 GB RAM, the
fictional rental sample completed in **111.5 seconds**. It produced 11 clauses,
14 flags and seven AI explanations that passed the output checks. PDF export
and session deletion also passed. This is one observed run, not a latency target
or a measure of legal correctness.

## Continuous integration

The [initial GitHub Actions run](https://github.com/itz-naman007/clauseloom/actions/runs/41315162523)
passed for commit `bb5558ff343b08664b0b243dc92bfd2a2c172e24`. It covers backend
lint/tests and frontend tests/build; it does not deploy or test a hosted service.

Application dependency audits do not cover all operating-system packages in the
container. Outstanding image advisories, hosted proxy behavior, abuse controls
and representative-contract accuracy are tracked in the
[launch review](deployment-readiness.md).
