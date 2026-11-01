# ClauseLoom deployment review

Reviewed 1 November 2026. Main app: original React/Vite UI, FastAPI and local
Ollama inference. Source is intended for a private Git repository. Hosting has
not been provisioned.

## Current decision

Local automated checks pass. Final container acceptance results are being
recorded below. This review is not a penetration test or a legal accuracy
certification. A broad production launch still needs the security and operating
decisions listed under Remaining work.

## Changes made

- Fixed the observed pip download timeout; builds now use longer timeouts,
  retries and a reusable dependency cache.
- Updated vulnerable FastAPI/Starlette, multipart and Pillow dependencies.
  Test and lint packages are separated from the runtime image.
- Replaced PyMuPDF with pypdfium2/PDFium for the private-source release. Text,
  password errors, page/pixel limits and scanned-PDF OCR are covered by tests.
  PDFium calls are serialized because the library is not thread-safe.
- Updated Ollama to a pinned current stable release, disabled its cloud features,
  kept inference on loopback and copied only CPU libraries into the Space image.
- Cached the model in a separate Docker build stage, with bounded startup checks
  and model-download retries.
- Added startup validation for the configured model and shutdown handling when
  the inference server exits.
- Readiness requires successful inference, not just a model name in the catalog.
  Inference request failures clear readiness.
- Restricted iframe embedding to Hugging Face in the Space image. Other builds
  retain the default frame-blocking policy.
- Derived the allowed origin from the platform's SPACE_HOST. Custom domains
  require an explicit ALLOWED_ORIGINS list.
- Rebuilt upload packaging to remove stale files, exclude environment files and
  normalize shell-script line endings. Included third-party license notices.
- Refreshed frontend model status every 15 seconds after startup.

## Verification

| Check | Result |
| --- | --- |
| Backend tests | 98 passed |
| Python lint and dependency compatibility | Passed |
| Frontend production build, type check and unit test | Passed |
| npm dependency audit | No known vulnerabilities reported |
| Python runtime dependency audit | No known vulnerabilities reported across 28 resolved packages |
| Rule regression corpus | 62 synthetic clauses; 31 true positives, no false positives/negatives |
| Standard Docker image | Builds successfully on Debian 13 |
| Single-container CPU image | Built and tested locally with original React UI |
| Rental sample with bundled 1.5B model, 2 CPUs / 4 GB | 11 clauses, 14 flags, 7 grounded AI explanations; 111.5 seconds; PDF and deletion passed |
| PDF, DOCX and PNG/JPEG OCR uploads | Live Docker API checks passed |
| English/Hindi report fonts | Mixed-script report visually verified after correcting font fallback |
| Browser UI | Rental review, search, theme, privacy dialog, PDF download and deletion checked; 390px mobile view had no horizontal overflow |
| Hosted deployment | Not performed; real hosted proxy, capacity and account checks remain |

The rule corpus is a development regression set, not an independent estimate of
accuracy on real contracts. Existing raw model evaluation also shows that
grounding rejection and rule-only fallback remain necessary.

## Container scan findings

The initial standard image produced 146 high/critical advisory entries. After
updating dependencies and the Debian runtime, the standard image produced 73
entries across 28 unique advisories: 72 high and 1 critical. The scanner lists no
available fixed Debian package version for these remaining entries. These are
package/advisory combinations, not 73 independently demonstrated exploits.

Remaining components include Tesseract, libtiff, libxml2, X11 libraries and system
utilities. Several advisories require attack paths such as malicious traineddata,
an X server or privileged local mount operations that the app does not expose as
features. That observation is not a complete reachability assessment. The image
is not certified free of vulnerabilities. Preserve the JSON reports in
`artifacts/` for assessment and future rescans.

Scans use Trivy locally with telemetry disabled, the Docker image as the only
image source and offline dependency identification. Image contents were not
uploaded to Docker Scout.

## Remaining work before launch

1. Create or identify the actual Hugging Face Space. Current platform docs
   require a paid account plan to create a Docker Space. Choose **Protected**
   visibility for a public app with private source; **Private** visibility also
   restricts the running app. Account eligibility and charges must be checked in
   the user's account. https://huggingface.co/docs/hub/spaces-overview
2. Build and run the prepared package on that Space, then run the acceptance
   scripts against its actual HTTPS URL. Check the embedded Hub view and direct
   hf.space URL, origin handling, both languages, uploads, streaming, report
   download, deletion and restart. Local tests cannot validate the hosted proxy.
3. Assess remaining native-library/OS advisories and parser isolation before a
   broad anonymous launch. Extraction/OCR uses native libraries in the app
   container. Byte/page/pixel limits and OCR timeouts help bound work but are not
   a hostile-file sandbox. Cancelling a session does not immediately terminate an
   in-flight native parsing thread.
4. Decide access and abuse controls. The app has no login. Its rate limiter uses
   the direct peer IP and does not trust arbitrary forwarding headers. Behind
   the hosting proxy, users may share the ten-analyses/hour bucket. Confirm this
   on the real Space and add trusted edge limits or access controls for growth.
5. Validate useful accuracy and response times on representative contracts with
   authorized reviewers. The small model can reject explanations or provide
   incorrect interpretations. Keep the informational-only disclaimer and clear
   rule-only labels.
6. Configure uptime/readiness monitoring, operator contact and an incident
   process. Keep document contents, filenames and bearer session URLs out of
   monitoring and proxy logs. Verify the hosting provider's data-handling terms
   before accepting confidential third-party contracts.

## Deployment settings

- SDK: Docker / Blank. Port: 7860. CPU image, one process and one replica.
- Model: qwen2.5:1.5b, bundled at build time. Changing LLM_MODEL requires rebuilding
  with that model; startup fails clearly if the configured model is absent.
- Default concurrency: 1; maximum sessions: 8; sessions expire after 30 minutes.
- Origins: automatic for SPACE_HOST; custom domain settings must list exact
  origins separated by commas. Never put hosting tokens in source files.
- Memory-only sessions are lost on restart, sleep or rebuild. Multiple replicas
  would need a shared store and routing changes; do not enable them as-is.
- Keep all installed third-party license texts. See [third-party notices](../THIRD_PARTY_NOTICES.md).

## Reproducible checks

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
python -m ruff check backend eval scripts
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend test
python scripts/prepare_space.py
docker build -t clauseloom-space:qa artifacts/huggingface-space
docker run --name clauseloom-space-qa -p 127.0.0.1:7860:7860 clauseloom-space:qa
```

After readiness returns 200:

```powershell
python scripts/verify_live.py --base http://localhost:7860 --kind rental --require-ai --output-dir artifacts/space-qa
python scripts/verify_live.py --base http://localhost:7860 --kind freelance --lang hi --require-ai --output-dir artifacts/space-qa
python scripts/verify_formats.py --base http://localhost:7860
```

Use the actual Space HTTPS URL as `--base` after deployment. These scripts upload
only fictional sample documents and delete the server sessions afterwards.
