---
title: ClauseLoom
emoji: 📄
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# ClauseLoom

ClauseLoom helps you read rental and freelance contracts. Start with a fictional
sample to explore clause explanations, flagged terms, negotiation questions and
PDF reports. Explanations are available in English and Hindi.

This is an informational screening tool, not legal advice. Rules and explanations
can miss issues or interpret a clause incorrectly. A low score does not mean an
agreement is safe to sign.

## Documents and privacy

Processing runs on this hosting server, using a local Ollama model rather than
an external AI inference API. Upload only documents you are authorized to share
with the server.

Review state is held in memory and expires after 30 minutes. Parsing and OCR may
use temporary files. **Delete my data now** clears an active review sooner;
downloaded reports remain on your device. Reviews are lost when the service
restarts or sleeps.

## Operator notes

This Docker image bundles the React frontend, FastAPI, Tesseract and
`qwen2.5:1.5b`. It serves port 7860 and requires one worker and one replica.
Changing `LLM_MODEL` requires bundling that model in a new image.

- `SPACE_HOST` supplies the allowed HTTPS origin unless `ALLOWED_ORIGINS` is set.
  For a custom domain, list all allowed origins explicitly, separated by commas.
- Embedding defaults to `https://huggingface.co`. Additional embedding sites need
  an explicit `FRAME_ANCESTORS` value with exact HTTPS origins.
- `/api/health` checks API liveness; `/api/ready` checks model availability and
  successful inference. The Docker health check uses readiness.
- The default CPU thread count is two. Match `LLM_NUM_THREADS` to the allocated
  cores and allow for reviews that take several minutes.

Confirm account eligibility, source visibility and hardware requirements in the
[Spaces documentation](https://huggingface.co/docs/hub/spaces-overview) before
launch. Test uploads, streaming, both languages, PDF export and deletion on the
actual deployment origin before inviting users.
