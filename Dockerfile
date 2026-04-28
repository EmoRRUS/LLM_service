# ============================================================
# Bounded Emotion Memory System – GPU Container
#
# Base: ollama/ollama:latest
#   Ships with CUDA 12 runtime + libggml-cuda.so (GPU backend)
#   This guarantees Ollama uses the GPU instead of CPU.
# ============================================================
FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# System dependencies + Python + pip — all in ONE RUN step
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    ca-certificates \
    && pip3 install --no-cache-dir --upgrade pip setuptools wheel \
    && rm -rf /var/lib/apt/lists/*

# Convenience aliases
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

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