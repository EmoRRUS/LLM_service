# ============================================================
# Bounded Emotion Memory System – GPU Container
#
# Base: python:3.11-slim (Ultra-lightweight)
#   - Solves the "no space left on device" error (image is tiny)
#   - Pip works perfectly
#   - CUDA runtime is automatically provided by RunPod host (--gpus all)
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
# Python dependencies (pip works perfectly here)
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