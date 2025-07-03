# syntax=docker/dockerfile:1
FROM python:3.10-slim

# System dependencies für PDF processing
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER app
WORKDIR /empathic-conversational-agent-lab

# Streamlit-Verzeichnis erstellen und Berechtigungen setzen
RUN mkdir -p /home/app/.streamlit && \
    chown -R app:app /home/app/.streamlit

# allow imports from project root
ENV PYTHONPATH="/empathic-conversational-agent-lab:${PYTHONPATH}"

# Python dependencies zuerst (für besseres Caching)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# Application code (inkl. scripts/preload_documents.py)
COPY . .

# make the preload script executable
RUN chmod +x scripts/preload_documents.py

# expose Streamlit port
EXPOSE 8501

# Health check für Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Non-root user für Security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /empathic-conversational-agent-lab
USER app

# At container start: fix perms, preload docs, then launch Streamlit
ENTRYPOINT [ "bash", "-lc", "\
  chown -R app:app /empathic-conversational-agent-lab/docs /empathic-conversational-agent-lab/data && \
  python scripts/preload_documents.py && \
  streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501\
" ]