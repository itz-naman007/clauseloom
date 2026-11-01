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

Private contract screening with a local small language model. Informational only, not legal advice.

This Space uses a single container containing FastAPI, the static React app, Tesseract and Ollama. The model is downloaded during image build. Runtime document processing calls only loopback inference.

Uploads and results are held in server memory and expire after 30 minutes. Use
"Delete my data now" to remove an active session sooner. Downloaded reports stay
on your device. Processing is local to this hosting server, not your device.
Do not upload a document unless you are authorized to share it with this server.

## Hosting configuration

- Docker SDK, CPU image, port 7860, one process and one replica. Sessions are not shared
  between replicas and are lost when the Space restarts or sleeps.
- The bundled model is `qwen2.5:1.5b`. Keep `LLM_MODEL` at that value unless you
  rebuild the image with another model.
- The app uses Hugging Face's `SPACE_HOST` to allow its exact HTTPS origin.
  For a custom domain, set `ALLOWED_ORIGINS` to a comma-separated list of the
  Space origin and your custom origin.
- Framing is allowed only from `https://huggingface.co`. Other embedding sites
  need an explicit `FRAME_ANCESTORS` setting containing exact HTTPS origins.
- `/api/health` checks the web app. `/api/ready` checks model availability.
  The Docker health check uses readiness.
- CPU inference can take minutes. Start with fictional samples and check both
  languages, streamed results, PDF download and deletion before inviting users.
- `LLM_NUM_THREADS=2` matches CPU Basic. Set it to the allocated core count when
  upgrading hardware; the app does not automatically scale across replicas.
- Choose **Protected** visibility for a publicly accessible app with a private
  source repository. **Private** visibility restricts the running app as well.

Hugging Face currently requires a paid account plan to create Docker Spaces;
confirm account eligibility and hardware in Settings before launch:
https://huggingface.co/docs/hub/spaces-overview

This is a limited contract-screening beta. The synthetic regression corpus is
not independent legal validation. Rules and AI explanations can be incomplete or
incorrect; an unflagged clause is not a guarantee of safety.
