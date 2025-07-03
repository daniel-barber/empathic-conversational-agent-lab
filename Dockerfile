# syntax=docker/dockerfile:1
FROM python:3.10-slim

# System dependencies für PDF processing
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# User EINMAL erstellen
RUN useradd -m -u 1000 app

# Streamlit-Verzeichnis erstellen und Berechtigungen setzen (als root)
RUN mkdir -p /home/app/.streamlit && \
    chown -R app:app /home/app/.streamlit

# Python dependencies (als root installieren für alle)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Working directory erstellen und Berechtigungen setzen
RUN mkdir -p /empathic-conversational-agent-lab && \
    chown -R app:app /empathic-conversational-agent-lab

# Jetzt zu User wechseln
USER app
WORKDIR /empathic-conversational-agent-lab

# Environment für Python imports
ENV PYTHONPATH="/empathic-conversational-agent-lab:${PYTHONPATH}"

# Application code kopieren
COPY --chown=app:app . .

# Expose Streamlit port
EXPOSE 8501

# Health check für Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Preload script im ENTRYPOINT ausführen (nicht im Build)
ENTRYPOINT [ "bash", "-c", "\
  python scripts/preload_documents.py && \
  streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501\
" ]