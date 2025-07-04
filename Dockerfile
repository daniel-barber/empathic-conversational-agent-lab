# syntax=docker/dockerfile:1

#####################################
# 1) Builder stage — install into /install
#####################################
FROM python:3.10-slim AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# 1) Upgrade pip
# 2) Install torch CPU‐only into /install
# 3) Build & install the remaining deps into /install
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install torch>=2.7.1 \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt \
 && rm -rf ~/.cache/pip

#####################################
# 2) Runtime stage — clean & lean
#####################################
FROM python:3.10-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 app \
 && mkdir -p /home/app/.streamlit /empathic-conversational-agent-lab \
 && chown -R app:app /home/app/.streamlit /empathic-conversational-agent-lab

WORKDIR /empathic-conversational-agent-lab

# Copy the installed Python packages (torch + the rest)
COPY --from=builder /install /usr/local

COPY --chown=app:app . .

USER app
ENV PYTHONPATH="/empathic-conversational-agent-lab:${PYTHONPATH}"
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["bash","-lc","python scripts/preload_documents.py && streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501"]
