# ============================================================
# Bounded Emotion Memory System – GPU Container
#
# KEY INSIGHT (from gist.github.com/usrbinkat/...):
#   RunPod GPU pods automatically pass "--gpus all" to containers.
#   This means CUDA runtime libraries are mounted from the HOST.
#   The Docker image does NOT need to ship CUDA itself.
#
# Strategy:
#   Stage 1: ollama/ollama:latest
#     → copy /bin/ollama (binary)
#     → copy /lib/ollama (GPU runner libs: libggml-cuda.so etc.)
#   Stage 2: python:3.11-slim
#     → Python + pip work perfectly here (no apt conflicts)
#     → libggml-cuda.so links against CUDA libs from RunPod host
# ============================================================

# ── Stage 1: Get Ollama binary + GPU runners ─────────────────
FROM ollama/ollama:latest AS ollama-src

# ── Stage 2: Python base (clean pip environment) ─────────────
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Ollama binary and its bundled GPU backend libraries
COPY --from=ollama-src /bin/ollama /usr/bin/ollama
COPY --from=ollama-src /lib/ollama /lib/ollama

# ------------------------------------------------------------
# Working directory
# ------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------
# Python dependencies (pip works perfectly on python:3.11-slim)
# ------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# Copy app source
# ------------------------------------------------------------
COPY . .

# ------------------------------------------------------------
# Start script (strip Windows CRLF line endings)
# ------------------------------------------------------------
COPY start.sh /start.sh
RUN sed -i 's/\r//' /start.sh && chmod +x /start.sh

# ------------------------------------------------------------
# GPU passthrough env (RunPod host provides CUDA runtime)
# ------------------------------------------------------------
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ------------------------------------------------------------
# Expose FastAPI port
# ------------------------------------------------------------
EXPOSE 8000

ENTRYPOINT ["/start.sh"]