# ============================================================
# Bounded Emotion Memory System – RunPod Container
# ============================================================
# Multi-stage build:
#   Stage 1: Pull Ollama binary out of the official image
#   Stage 2: Clean Ubuntu 22.04 base with Python + our app
# This avoids all download URL issues — we just copy the binary.
# ============================================================

# ── Stage 1: Get the Ollama binary ───────────────────────────
FROM ollama/ollama:latest AS ollama-src

# ── Stage 2: Our application image ───────────────────────────
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python, pip, and curl (standard Ubuntu — apt-get works here)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Convenience aliases
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# ── Copy Ollama binary from official image ───────────────────
COPY --from=ollama-src /usr/bin/ollama /usr/bin/ollama
RUN chmod +x /usr/bin/ollama

# ── Working directory ────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ──────────────────────────────────────
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# ── Copy project source ──────────────────────────────────────
COPY . /app

# ── Startup script ───────────────────────────────────────────
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ── Expose API port ──────────────────────────────────────────
EXPOSE 8000

# ── Entrypoint ───────────────────────────────────────────────
ENTRYPOINT ["/start.sh"]

