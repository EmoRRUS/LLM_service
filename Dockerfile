# ============================================================
# Bounded Emotion Memory System – GPU Container
#
# WHY ollama/ollama:latest as base?
#   The official Ollama image already ships with:
#     - CUDA 12 runtime libraries
#     - libggml-cuda.so (the GPU backend)
#     - Properly linked libc/libstdc++
#   Using it as the base is the ONLY reliable way to get
#   "inference compute id=cuda" instead of "id=cpu".
# ============================================================
FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# System dependencies + Python
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pip via official bootstrap (avoids conflicts with ollama base image)
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

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
# GPU environment
# ------------------------------------------------------------
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ------------------------------------------------------------
# Expose FastAPI port
# ------------------------------------------------------------
EXPOSE 8000

ENTRYPOINT ["/start.sh"]