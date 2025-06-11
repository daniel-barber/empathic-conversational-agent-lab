# syntax=docker/dockerfile:1
FROM python:3.10-slim

# System dependencies für PDF processing
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /empathic-conversational-agent-lab

# Python dependencies zuerst (für besseres Caching)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt


# Application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check für Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Non-root user für Security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /empathic-conversational-agent-lab
USER app

# Start Streamlit
CMD ["streamlit", "run", "frontend/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]