# Deployment and troubleshooting

All deployment options in this repository use the React interface and FastAPI
backend. Run the commands below from the repository root. Source is intended to
remain private; credentials and model weights must not be committed.

This guide explains the provided deployment files. It does not claim an existing
hosted URL or provision cloud resources. Review [deployment readiness](deployment-readiness.md)
before a broad public launch.

## Choose the deployment layout

| Layout | Entry point | API port | Inference |
| --- | --- | --- | --- |
| Docker Compose | `docker-compose.yml` and root `Dockerfile` | 8080 | Separate private Ollama service and persistent model volume |
| CPU single-container | `deploy/huggingface/Dockerfile` | 7860 by default | Bundled Ollama, CPU libraries and predownloaded 1.5B model |
| Development | `python scripts/dev.py` | 8080 API / 5173 UI | Existing local Ollama installation |

The root Dockerfile builds the frontend in a Node stage and copies its assets
into a non-root Python runtime with OCR and report fonts. The single-container
variant adds CPU inference and supervises both the API and model process.

## Docker Compose

```sh
cp .env.example .env
# Set ALLOWED_ORIGINS to the actual HTTPS origin for a hosted deployment.
docker compose config --quiet
docker compose up --build -d
docker compose logs -f ollama-init app
```

Startup order is:

1. Ollama starts and passes its catalog health check.
2. `ollama-init` pulls the configured model into the persistent volume and exits.
3. The API starts after model initialization succeeds, then warms inference.

The API uses a read-only filesystem, a bounded `/tmp` tmpfs, dropped Linux
capabilities, `no-new-privileges` and a 1 GB container memory limit. Ollama's model
memory is separate. Port 11434 is not published to the host.

```sh
docker compose ps -a
curl -f http://127.0.0.1:8080/api/health
curl -f http://127.0.0.1:8080/api/ready
sh scripts/smoke.sh
```

`/api/health` is API liveness. `/api/ready` checks catalog availability and whether
inference has succeeded; inference errors clear readiness. A liveness success
alone does not prove the model is usable.

`docker compose down` stops the stack while preserving model weights. Removing
the model volume forces a fresh download on the next deployment.

### CPU / low-resource profile

```sh
cp deploy/low-resource.env .env
# Add the real ALLOWED_ORIGINS value for hosting.
docker compose up --build -d
```

This uses `qwen2.5:1.5b`, concurrency 1 and context 2048. Set `LLM_NUM_THREADS` to
the CPU quota when the host exposes more physical threads than the container can
use. A measured two-CPU test improved substantially after setting two threads;
hardware and document length still affect latency.

### GPU profile

The host needs a compatible NVIDIA driver and NVIDIA Container Toolkit.

```sh
cp deploy/gpu.env .env
docker compose -f docker-compose.yml -f deploy/compose.gpu.yml up --build -d
```

This override applies to the separate Ollama service. The CPU single-container
image intentionally excludes CUDA libraries and is not the GPU deployment path.

## VPS and HTTPS

1. Install Docker Engine and Compose on the Linux host.
2. Transfer or clone the private repository, configure `.env`, and start Compose.
3. Put a reverse proxy in front of the API. `deploy/Caddyfile` is a hostname
   template with streaming enabled and an upload-body limit.
4. Change the Compose host binding to `127.0.0.1:8080:8080` when the reverse proxy
   runs on the same host. Route public traffic through HTTPS.
5. Set `ALLOWED_ORIGINS` to the exact public origin. Keep inference private.
6. Apply host firewall/access controls and configure proxy logging so it does not
   retain bearer session paths, filenames or document bodies.

Do not increase Uvicorn workers or app replicas: reviews and cancellation state
live in one process. Native parsing limits are not a hostile-file sandbox.
Confirm architecture compatibility before using an ARM cloud VM; the completed
container acceptance run was on Linux amd64.

## Single-container CPU hosting

```sh
docker build -f deploy/huggingface/Dockerfile -t clauseloom:cpu .
docker run --name clauseloom -p 127.0.0.1:7860:7860 \
  -e ALLOWED_ORIGINS=http://localhost:7860 clauseloom:cpu
```

The image includes `qwen2.5:1.5b`, model concurrency 1, context 2048 and two CPU
threads. Its independent model-build stage avoids downloading weights again for
ordinary application rebuilds. Change thread count for your allocated CPU cores.
Changing `LLM_MODEL` alone does not install another model; rebuild the model stage
when changing the bundled tag.

The entry point verifies model installation, bounds startup waiting and stops
the API if Ollama exits so the hosting platform can restart the service. Its
Docker health check uses `/api/ready` and honors `PORT`.

### Hugging Face Docker Spaces

```sh
python scripts/prepare_space.py
```

Upload the contents of `artifacts/huggingface-space/` to the Space repository root.
The generated README declares `sdk: docker` and `app_port: 7860`, and the root
Dockerfile is the single-container CPU variant. The packaging script excludes
environment files, caches and generated frontend assets, and replaces stale
generated contents.

The container derives its allowed HTTPS origin from `SPACE_HOST` when
`ALLOWED_ORIGINS` is not explicitly set. For a custom domain, set the complete
comma-separated origin list. Embedding is restricted to `https://huggingface.co`
by default; other exact HTTPS ancestors need an explicit `FRAME_ANCESTORS` value.

Check the platform's current account, visibility and hardware requirements before
creating a Space: [Docker Spaces documentation](https://huggingface.co/docs/hub/spaces-sdks-docker).
Choose visibility that preserves the intended source privacy. No hosting tokens
belong in this repository or container image.

### Render / Railway

Use repository-root build context and `deploy/huggingface/Dockerfile` for the
single-container layout. `deploy/render.yaml` is the Render Blueprint template.
Set the real allowed origin and the platform port, and allow long streaming
responses. Choose resources that can hold the model, API and OCR workload.

The provided Render template checks `/api/health`; monitor `/api/ready` separately
for model availability. These platforms have not been provisioned or load-tested
from this workspace. Check current account, plan and resource restrictions rather
than assuming the full workload fits a free tier.

## Acceptance tests

After readiness returns 200, test the actual deployment origin:

```sh
python scripts/verify_live.py --base https://YOUR-ACTUAL-APP-ORIGIN --kind rental --require-ai
python scripts/verify_live.py --base https://YOUR-ACTUAL-APP-ORIGIN --kind freelance --lang hi --require-ai
python scripts/verify_formats.py --base https://YOUR-ACTUAL-APP-ORIGIN
```

Replace the example origin. The scripts use fictional documents, check streamed
completion, findings, PDFs and deletion, and retain QA outputs under ignored
`artifacts/`. `verify_formats.py` checks PDF/DOCX extraction and real PNG/JPEG OCR;
its local document generation needs an available DejaVu or Windows Arial font.

Also check both the direct origin and any embedded view, browser origin policy,
mobile layout, clear model-outage labels, restart behavior and real CPU latency.
Configure ongoing liveness/readiness monitoring separately from this repository.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Docker named-pipe / daemon connection error | Confirm Docker Desktop's Linux engine is running; this occurs before app code executes |
| Build stops downloading a Python package | Inspect the build log and connectivity; Dockerfiles already use a dependency cache, retries and a longer download timeout |
| `ollama-init` fails or app waits to start | Inspect `docker compose logs ollama-init ollama`; check the exact model tag, disk space and registry access |
| Readiness stays 503 | Check model installation and startup/warmup logs; a catalog entry alone is not successful inference |
| UI shows rule-only results | Inference failed, was disabled or failed grounding checks; rules still run and labels explain the fallback |
| Homepage is 404 during local API development | Build `frontend` first, or use Vite on port 5173 |
| Upload returns 403 | Check the actual Origin header against `ALLOWED_ORIGINS`, especially behind HTTPS proxies |
| Embedded page is blocked | Check the `frame-ancestors` CSP; the normal app blocks framing by default |
| OCR fails | Confirm Tesseract is on PATH and both `eng` and `hin` language data are installed |
| Hindi or Latin PDF text renders as boxes | Install the appropriate report fonts or set `REPORT_FONT` and `REPORT_HINDI_FONT` |
| Review is slow on a small CPU quota | Lower concurrency/context, use the 1.5B model and match `LLM_NUM_THREADS` to allocated cores |
| Users receive 429 together | The direct-peer rate limiter may see the proxy as one client; add trusted edge controls |
| Sessions return 404 after restart | Expected: session state is memory-only and is not restored |

See [architecture](architecture.md) for API/status semantics and
[verification](verification.md) for what was actually tested.
