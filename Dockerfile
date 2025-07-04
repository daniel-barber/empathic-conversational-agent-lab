# syntax=docker/dockerfile:1

#####################################
# 1) Builder stage — install into /install
#####################################
FROM python:3.10-slim AS builder

# 1) Install build tools + CPU-only PyTorch index support
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# 2) Upgrade pip, build wheels (including CPU-only torch)
#    then delete any GPU/CUDA wheels, and install only CPU wheels into /install
RUN pip install --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels \
      -r requirements.txt \
      -f https://download.pytorch.org/whl/cpu/torch_stable.html \
 && find /wheels -type f \( -iname "*cu*" -o -iname "nvidia_*" \) -delete \
 && pip install --no-cache-dir --prefix=/install \
      --no-index --find-links /wheels \
      -r requirements.txt \
 && rm -rf /wheels


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
