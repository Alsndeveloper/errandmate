#!/bin/bash
# ErrandMate Server Startup Script for macOS / Linux

cd "$(dirname "$0")"

echo "=============================================================="
echo "          ErrandMate FastAPI & AI Platform Server"
echo "=============================================================="

# Use virtual environment if present
if [ -d ".venv" ]; then
    echo "[*] Activating Python virtual environment (.venv)..."
    source .venv/bin/activate
fi

python3 run_server.py "$@"
