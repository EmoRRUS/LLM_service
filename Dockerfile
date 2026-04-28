# ============================================================
# GPU-enabled Ollama base image
# ============================================================
FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# Install system dependencies (VERY IMPORTANT for pip builds)
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
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Python aliases
# ------------------------------------------------------------
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# ------------------------------------------------------------
# Upgrade pip properly (IMPORTANT)
# ------------------------------------------------------------
RUN python -m pip install --upgrade pip setuptools wheel

# ------------------------------------------------------------
# Set working directory
# ------------------------------------------------------------
WORKDIR /app

# ------------------------------------------------------------
# Install Python dependencies
# ------------------------------------------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# Copy project files
# ------------------------------------------------------------
COPY . .

# ------------------------------------------------------------
# Startup script
# ------------------------------------------------------------
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ------------------------------------------------------------
# Environment variables for GPU
# ------------------------------------------------------------
ENV OLLAMA_LLM_LIBRARY=cuda
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# ------------------------------------------------------------
# Expose API port
# ------------------------------------------------------------
EXPOSE 8000

# ------------------------------------------------------------
# Start container
# ------------------------------------------------------------
ENTRYPOINT ["/start.sh"]