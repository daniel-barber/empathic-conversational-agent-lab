# syntax=docker/dockerfile:1

#####################################
# 1) Builder stage — install & cache
#####################################
FROM python:3.10-slim AS builder

# Install any build tools (if you have compilation needs; remove build-essential if not)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements so Docker can cache this layer
COPY requirements.txt .

# Install all dependencies directly into /install
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

#####################################
# 2) Runtime stage — clean & lean
#####################################
FROM python:3.10-slim

# Install only runtime deps (e.g. curl for PDF processing)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Create app user & dirs
RUN useradd -m -u 1000 app \
 && mkdir -p /home/app/.streamlit /empathic-conversational-agent-lab \
 && chown -R app:app /home/app/.streamlit /empathic-conversational-agent-lab

WORKDIR /empathic-conversational-agent-lab

# Pull in the installed Python packages
COPY --from=builder /install /usr/local

# Copy app code
COPY --chown=app:app . .

USER app
ENV PYTHONPATH="/empathic-conversational-agent-lab:${PYTHONPATH}"

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT [ "bash", "-c", "\
  python scripts/preload_documents.py && \
  streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501\
" ]
