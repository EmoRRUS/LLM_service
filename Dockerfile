# ============================================================
# Bounded Emotion Memory System – RunPod Container
# ============================================================
#
# Base: NVIDIA CUDA 12.1 runtime on Ubuntu 22.04
# What this builds:
#   1. Installs Ollama (local LLM runner)
#   2. Installs Python + your project dependencies
#   3. Copies all project files + RAG knowledge base
#   4. On start: launches Ollama, pulls Phi-3, then starts FastAPI
# ============================================================

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# ── System packages ──────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    wget \
    ca-certificates \
    pciutils \
    && rm -rf /var/lib/apt/lists/*

# Make "python" point to python3
RUN ln -s /usr/bin/python3 /usr/bin/python

# ── Install Ollama (Direct Binary) ───────────────────────────
# Using direct binary download instead of the script to avoid build-time errors
RUN curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/bin/ollama && \
    chmod +x /usr/bin/ollama

# ── Working directory ────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ──────────────────────────────────────
# Copy requirements first (Docker cache layer — only re-runs if requirements change)
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# ── Copy project source ──────────────────────────────────────
# Copies everything: .py files, rag_docs_v2/, .env, config, etc.
COPY . /app

# ── Startup script ───────────────────────────────────────────
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ── Expose API port ──────────────────────────────────────────
EXPOSE 8000

# ── RunPod entrypoint ────────────────────────────────────────
CMD ["/start.sh"]
