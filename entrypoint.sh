#!/usr/bin/env bash
set -euo pipefail

PRELOAD_LOG=/empathic-conversational-agent-lab/data/preload.log
STREAMLIT_LOG=/empathic-conversational-agent-lab/data/streamlit.log

# 1) Preload in background with error isolation
echo "Starting preload_documents.py in background…" | tee -a "$PRELOAD_LOG"
( python scripts/preload_documents.py >> "$PRELOAD_LOG" 2>&1 || echo "⚠️ Preload failed, continuing..." >> "$PRELOAD_LOG" ) &

# 2) Run Streamlit as main process
echo "Launching Streamlit…" | tee -a "$STREAMLIT_LOG"
exec streamlit run frontend/0_Intro.py --server.address 0.0.0.0 --server.port 8501 >> "$STREAMLIT_LOG" 2>&1
