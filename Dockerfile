# ============================================================
# Bounded Emotion Memory System – GPU Container
#
# Strategy:
#   Base = nvidia/cuda:12.1.1-runtime-ubuntu22.04
#     → Full Ubuntu 22.04 apt repos (Python works reliably)
#     → CUDA 12.1 runtime libraries already present
#   Ollama = installed via official install.sh
#     → Script detects the CUDA libs and installs the GPU backend
#     → Produces "inference compute id=cuda" at runtime
# ============================================================
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
# Install Ollama via official script
# The script detects CUDA 12.1 libs from the base image and
# installs the GPU-enabled Ollama binary automatically.
# ------------------------------------------------------------
RUN curl -fsSL https://ollama.com/install.sh | sh

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