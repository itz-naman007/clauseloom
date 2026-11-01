# Product brief

ClauseLoom is a contract-reading aid for people who need to understand an
agreement before signing. Its initial focus is rental and freelance contracts,
with India-oriented screening thresholds and English or Hindi explanations.

This brief describes the product's purpose and scope. For implementation details,
see the [architecture reference](../architecture.md); for setup, see the
[README](../../README.md).

## Who it is for

The intended users include first-time tenants, students, freelancers and small
business owners who may be unfamiliar with contract language. The app should
help them identify terms worth questioning and decide when to seek legal advice.
It cannot determine whether an agreement is lawful or safe to sign.

## The core workflow

A user uploads a document or opens a fictional sample, chooses the contract type
and explanation language, then reviews clauses alongside the source text. The
results include matched flags, key terms, a score with a visible formula, and
questions to raise with the other party. The user can export a report or delete
the review.

Supported input includes text documents, PDFs and images. Scanned pages use OCR,
so extraction quality affects the rest of the review.

## Product principles

- **Keep the source close.** A finding should lead back to the clause that
  prompted it, so users can inspect the wording for themselves.
- **Make uncertainty visible.** Distinguish checked AI explanations from
  rule-only fallbacks and explain what the score measures.
- **Give users a useful next step.** Questions and negotiation wording should
  help start a conversation, without presenting a legal conclusion.
- **Limit document retention.** Use short-lived sessions and an explicit delete
  action. Explain that processing happens on the host and that downloaded
  reports remain with the user.
- **Keep the interface readable.** Support keyboard navigation, mobile screens,
  English/Hindi explanations and clear progress feedback during slow inference.

## Technical choices and tradeoffs

The React interface talks to FastAPI. Deterministic rules select findings and
severity; a small model served through Ollama explains them. Model output is
checked for schema, source quotes and numeric consistency before display.

Self-hosted inference avoids an external AI inference API, but requires enough
host memory and CPU or GPU capacity. Small models can be slow or fail output
checks. Rule-only results keep the review usable when explanations are unavailable.

Memory-only sessions avoid a persistent document store, but require a single
worker and replica and are lost on restart. Hindi explanations improve language
access; the screening rules still primarily recognize English source wording.

## Scope and future work

The current app does not include accounts, saved contract history, collaboration,
payments or multi-replica operation. Expanding contract types or jurisdictions
requires new rules and evaluation, rather than a prompt change alone.

Before a public launch, the project needs hosted acceptance testing, security
assessment, access controls and review on representative contracts. The
[launch review](../deployment-readiness.md) tracks those remaining decisions.
