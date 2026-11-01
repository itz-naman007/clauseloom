#!/bin/sh
set -eu
ollama serve >/tmp/model-install.log 2>&1 &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT
attempt=0
until ollama list >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if ! kill -0 "$server" 2>/dev/null || [ "$attempt" -ge 60 ]; then
    cat /tmp/model-install.log >&2
    exit 1
  fi
  sleep 1
done
attempt=0
until ollama pull "$LLM_MODEL"; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 5 ]; then
    echo "Model download failed after five attempts." >&2
    exit 1
  fi
  sleep 5
done
