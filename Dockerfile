# ============================================================
# CUDA BASE (clean + stable)
# ============================================================
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# Install system dependencies
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    git \
    ca-certificates \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Fix Python + pip
# ------------------------------------------------------------
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

RUN python -m pip install --upgrade pip setuptools wheel

# ------------------------------------------------------------
# Install Ollama (OFFICIAL method)
# ------------------------------------------------------------
RUN curl -fsSL https://ollama.com/install.sh | sh

# ------------------------------------------------------------
# Working directory
# ------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------
# Install Python dependencies
# ------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# Copy app
# ------------------------------------------------------------
COPY . .

# ------------------------------------------------------------
# Start script
# ------------------------------------------------------------
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ------------------------------------------------------------
# GPU env
# ------------------------------------------------------------
ENV OLLAMA_LLM_LIBRARY=cuda
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ------------------------------------------------------------
# Expose
# ------------------------------------------------------------
EXPOSE 8000

ENTRYPOINT ["/start.sh"]