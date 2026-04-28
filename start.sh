#!/bin/bash
set -e

echo "=============================================="
echo "  Bounded Emotion Memory – RunPod Container"
echo "=============================================="

# ------------------------------------------------------------
# 0. FORCE GPU USAGE (CRITICAL)
# ------------------------------------------------------------
export OLLAMA_LLM_LIBRARY=cuda
export NVIDIA_VISIBLE_DEVICES=all

echo "[0/4] GPU Environment:"
echo "      OLLAMA_LLM_LIBRARY=$OLLAMA_LLM_LIBRARY"
echo "      NVIDIA_VISIBLE_DEVICES=$NVIDIA_VISIBLE_DEVICES"

# Optional: show GPU
nvidia-smi || echo "WARNING: nvidia-smi not available"

# ------------------------------------------------------------
# 1. Start Ollama
# ------------------------------------------------------------
echo ""
echo "[1/4] Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!
echo "      Ollama PID: $OLLAMA_PID"

# ------------------------------------------------------------
# 2. Wait for Ollama
# ------------------------------------------------------------
echo ""
echo "[2/4] Waiting for Ollama to become ready..."

MAX_WAIT=120
ELAPSED=0

until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "ERROR: Ollama did not start within ${MAX_WAIT}s."
        exit 1
    fi
    echo "      Still waiting... (${ELAPSED}s elapsed)"
    sleep 3
    ELAPSED=$((ELAPSED + 3))
done

echo "      Ollama is ready!"

# ------------------------------------------------------------
# 3. Pull model
# ------------------------------------------------------------
echo ""
echo "[3/4] Pulling Phi-3 model (if needed)..."
ollama pull phi3

# 🔥 IMPORTANT: warm-up run (forces GPU load)
echo "      Warming up model (forces GPU init)..."
ollama run phi3 "hello" > /dev/null 2>&1 || true

echo "      Model ready!"

# ------------------------------------------------------------
# 4. Start FastAPI
# ------------------------------------------------------------
echo ""
echo "[4/4] Starting FastAPI server..."
echo "      API docs: http://0.0.0.0:8000/docs"
echo ""

cd /app
exec python3 -m uvicorn api_server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info