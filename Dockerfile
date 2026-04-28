# ============================================================
# Bounded Emotion Memory System – GPU Container
#
# Base: RunPod's official PyTorch/CUDA image
#   - Highly optimized for RunPod GPUs (including RTX A5000)
#   - Pre-installed with Python 3.10 & fully working pip
#   - Pre-installed with CUDA 12.1 runtime
# ============================================================

# ── Stage 1: Get Ollama binary + GPU runners ─────────────────
FROM ollama/ollama:latest AS ollama-src

# ── Stage 2: RunPod Official GPU Base ─────────────────────────
FROM runpod/pytorch:2.2.1-py3.10-cuda12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Copy Ollama binary and its bundled GPU backend libraries
COPY --from=ollama-src /bin/ollama /usr/bin/ollama
COPY --from=ollama-src /lib/ollama /lib/ollama

# ------------------------------------------------------------
# Working directory
# ------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------
# Python dependencies (pip works perfectly out of the box here)
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
# Expose FastAPI port
# ------------------------------------------------------------
EXPOSE 8000

ENTRYPOINT ["/start.sh"]