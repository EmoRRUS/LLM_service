#!/bin/bash
# ============================================================
# start.sh — RunPod container startup script
#
# Execution order:
#   1. Start Ollama server in the background
#   2. Wait until Ollama is ready (health poll)
#   3. Pull the Phi-3 model (skipped automatically if already cached)
#   4. Start the FastAPI server (foreground — keeps the container alive)
# ============================================================

set -e   # exit immediately on any error

echo "=============================================="
echo "  Bounded Emotion Memory – RunPod Container"
echo "=============================================="

# ── 1. Start Ollama ─────────────────────────────────────────
echo ""
echo "[1/4] Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!
echo "      Ollama PID: $OLLAMA_PID"

# ── 2. Wait for Ollama to be ready ──────────────────────────
echo ""
echo "[2/4] Waiting for Ollama to become ready..."
MAX_WAIT=120   # seconds
ELAPSED=0
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: Ollama did not start within ${MAX_WAIT}s. Exiting."
        exit 1
    fi
    echo "      Still waiting... (${ELAPSED}s elapsed)"
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done
echo "      Ollama is ready!"

# ── 3. Pull Phi-3 model ──────────────────────────────────────
# 'ollama pull' is a no-op if the model is already cached on disk.
echo ""
echo "[3/4] Pulling Phi-3 model (skipped if already cached)..."
ollama pull phi3
echo "      Phi-3 model ready!"

# ── 4. Start FastAPI ─────────────────────────────────────────
echo ""
echo "[4/4] Starting FastAPI server on port 8000..."
echo "      API docs: http://0.0.0.0:8000/docs"
echo ""

cd /app
exec python3 -m uvicorn api_server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info
