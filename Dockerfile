# ============================================================
# Bounded Emotion Memory System – GPU Container
#
# Strategy (multi-stage, targeted copy):
#   Stage 1: ollama/ollama:latest
#     → Source of the Ollama binary (/bin/ollama)
#     → Source of the GPU runner libs (/lib/ollama/)
#   Stage 2: nvidia/cuda:12.1.1-runtime-ubuntu22.04
#     → Provides CUDA 12.1 runtime (.so files)
#     → Full Ubuntu 22.04 apt repos → Python/pip work reliably
#     → We copy ONLY the ollama binary + runner libs (not all /usr)
#       so there are no library conflicts
# ============================================================

# ── Stage 1: Ollama source ───────────────────────────────────
FROM ollama/ollama:latest AS ollama-src

# ── Stage 2: Main image ───────────────────────────────────────
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# System dependencies + Python
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Convenience aliases
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# ------------------------------------------------------------
# Copy ONLY the Ollama binary + runner libs (targeted copy)
# /bin/ollama       → main executable
# /lib/ollama/      → GPU runner shared libraries (libggml-cuda.so etc.)
# This avoids the /usr conflict that broke Python packages before.
# ------------------------------------------------------------
COPY --from=ollama-src /bin/ollama /usr/bin/ollama
COPY --from=ollama-src /lib/ollama /lib/ollama

# ------------------------------------------------------------
# Working directory
# ------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------
# Python dependencies
# ------------------------------------------------------------
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

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
# GPU environment
# ------------------------------------------------------------
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ------------------------------------------------------------
# Expose FastAPI port
# ------------------------------------------------------------
EXPOSE 8000

ENTRYPOINT ["/start.sh"]