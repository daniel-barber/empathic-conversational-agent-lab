#!/usr/bin/env bash
set -euo pipefail

LOGFILE=/empathic-conversational-agent-lab/data/preload.log

# 1) Kick off preload in the background
echo "Starting preload_documents.py in background…" | tee -a "$LOGFILE"
python scripts/preload_documents.py >> "$LOGFILE" 2>&1 &

# 2) Immediately exec Streamlit
echo "Launching Streamlit…" | tee -a "$LOGFILE"
exec streamlit run frontend/0_Intro.py --server.address 0.0.0.0 --server.port 8501