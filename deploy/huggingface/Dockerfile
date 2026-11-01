FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ollama/ollama:0.40.13 AS inference
RUN mkdir /cpu-libs && find /usr/lib/ollama -mindepth 1 -maxdepth 1 ! -type d -exec cp -a {} /cpu-libs/ \;

FROM inference AS model
ENV OLLAMA_MODELS=/models OLLAMA_HOST=127.0.0.1:11434 LLM_MODEL=qwen2.5:1.5b OLLAMA_NO_CLOUD=1
COPY deploy/huggingface/install-model.sh /tmp/install-model.sh
RUN sh /tmp/install-model.sh

FROM python:3.11-slim-trixie
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin fonts-noto-core ca-certificates curl && rm -rf /var/lib/apt/lists/*
COPY --from=inference /bin/ollama /usr/bin/ollama
COPY --from=inference /cpu-libs /usr/lib/ollama
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install --timeout 120 --retries 8 -r backend/requirements.txt && pip uninstall -y pip setuptools wheel && useradd --create-home --uid 1000 appuser
ENV OLLAMA_MODELS=/home/appuser/models OLLAMA_HOST=127.0.0.1:11434 LLM_BASE_URL=http://127.0.0.1:11434 LLM_MODEL=qwen2.5:1.5b LLM_CONCURRENCY=1 LLM_NUM_CTX=2048 LLM_TIMEOUT=120 PORT=7860 PYTHONPATH=/app/backend PYTHONDONTWRITEBYTECODE=1
ENV HOME=/home/appuser PYTHONUNBUFFERED=1 FRAME_ANCESTORS=https://huggingface.co OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_NO_CLOUD=1 MAX_SESSIONS=8 MAX_MEMORY_MB=64
ENV LLM_NUM_THREADS=2
RUN mkdir -p /home/appuser/models && chown -R appuser:appuser /home/appuser
COPY --from=model --chown=appuser:appuser /models /home/appuser/models
COPY backend/app backend/app
COPY samples samples
COPY --from=frontend /build/backend/app/static backend/app/static
COPY deploy/huggingface/start.sh /app/start.sh
RUN chmod +x /app/start.sh
USER appuser
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','7860')+'/api/ready',timeout=8)"
CMD ["/app/start.sh"]
