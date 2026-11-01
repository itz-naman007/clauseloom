#!/bin/sh
set -eu
ollama serve &
model_pid=$!
api_pid=''
cleanup() {
  kill "$model_pid" ${api_pid:+$api_pid} 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
attempt=0
until ollama list >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  kill -0 "$model_pid" 2>/dev/null || exit 1
  if [ "$attempt" -ge 60 ]; then
    echo "Ollama failed to start within 60 seconds." >&2
    exit 1
  fi
  sleep 1
done
ollama show "$LLM_MODEL" >/dev/null || {
  echo "Configured model is not installed: $LLM_MODEL" >&2
  exit 1
}
if [ -z "${ALLOWED_ORIGINS:-}" ] && [ -n "${SPACE_HOST:-}" ]; then
  export ALLOWED_ORIGINS="https://$SPACE_HOST"
fi
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}" --workers 1 --no-access-log --limit-concurrency 32 &
api_pid=$!
while kill -0 "$api_pid" 2>/dev/null; do
  if ! kill -0 "$model_pid" 2>/dev/null; then
    echo "Ollama exited; stopping the app so the platform can restart it." >&2
    exit 1
  fi
  sleep 1
done
wait "$api_pid"
