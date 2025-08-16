# syntax=docker/dockerfile:1

########################################
# Builder — installs all Python packages
########################################
FROM python:3.10-slim AS builder
ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Upgrade pip first
RUN pip install --upgrade pip

# ---- ARM-safe pins (Pi) & x86-only extras -----------------------------
# On Raspberry Pi (arm64), newer wheels of pandas can SIGILL.
# We install conservative, ARM-friendly versions here.
# On amd64, we keep your torch install and (optionally) faiss.
RUN if [ "$TARGETARCH" = "arm64" ]; then \
      echo ">>> ARM64 build: installing ARM-safe numpy/pandas pins"; \
      pip install --no-cache-dir --prefix=/install \
        "numpy==1.24.4" "pandas==2.0.3"; \
    else \
      echo ">>> amd64 build: installing torch CPU wheel"; \
      pip install --no-cache-dir --prefix=/install \
        torch==2.7.1 \
        --index-url https://download.pytorch.org/whl/cpu; \
      # (optional) faiss on x86 only; skip on ARM
      pip install --no-cache-dir --prefix=/install faiss-cpu==1.8.0; \
    fi

# Install the rest of the dependencies
# Note: numpy/pandas/faiss may be omitted from requirements.txt so they don’t override the pins above.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


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

# copy in our background-entrypoint and make it executable
COPY --chown=app:app entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# health-probe remains the same
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# hand off to our script, which backgrounds preload and immediately starts Streamlit
ENTRYPOINT ["/entrypoint.sh"]