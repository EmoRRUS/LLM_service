# ============================================================
# Bounded Emotion Memory System – RunPod Container
# ============================================================
#
# Base: Official Ollama image (includes CUDA + Ollama pre-installed)
# What this builds:
#   1. Ollama is already installed in the base image
#   2. Installs Python + your project dependencies
#   3. Copies all project files + RAG knowledge base
#   4. On start: launches Ollama, pulls Phi-3, then starts FastAPI
# ============================================================

FROM ollama/ollama:latest

# ── System packages ──────────────────────────────────────────
# ollama/ollama is based on Rocky Linux — use microdnf, not apt-get
ENV DEBIAN_FRONTEND=noninteractive
RUN microdnf install -y \
    python3 \
    python3-pip \
    curl \
    && microdnf clean all

# Make "python" point to python3
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

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

# ── Override the ollama/ollama default entrypoint ───────────
# The base image sets ENTRYPOINT ["/bin/ollama"] — we override
# it so our custom start.sh runs instead.
ENTRYPOINT ["/start.sh"]

