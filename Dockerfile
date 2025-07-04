# syntax=docker/dockerfile:1

########################################
# Builder — installs all Python packages
########################################
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Install pip + torch CPU-only + deps into /install
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install \
      torch==2.7.1 \
      --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir --prefix=/install \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      -r requirements.txt

########################################
# Final runtime image — clean and lean
########################################
FROM python:3.10-slim

# Add curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 app \
 && mkdir -p /home/app/.streamlit /empathic-conversational-agent-lab \
 && chown -R app:app /home/app/.streamlit /empathic-conversational-agent-lab

WORKDIR /empathic-conversational-agent-lab

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy app code
COPY --chown=app:app . .

# Make sure the data folder is owned by “app” so preload_documents.py can write to it
RUN mkdir -p /empathic-conversational-agent-lab/data \
 && chown -R app:app /empathic-conversational-agent-lab

USER app
ENV PYTHONPATH="/empathic-conversational-agent-lab:${PYTHONPATH}"
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["bash", "-lc", "python scripts/preload_documents.py && streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501"]
