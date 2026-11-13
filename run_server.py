"""
ErrandMate Server Runner
Launches the FastAPI backend and web interface with Uvicorn.
Auto-detects and uses local virtual environment if present.
"""
import os
import sys
import webbrowser

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Auto-reexec in .venv if not already active and .venv python exists
VENV_PYTHON = os.path.join(BASE_DIR, ".venv", "bin", "python3")
if os.path.exists(VENV_PYTHON) and sys.executable != VENV_PYTHON:
    if "VIRTUAL_ENV" not in os.environ:
        os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

import uvicorn
from server.config import HOST, PORT, DEFAULT_DB_PATH


def main():
    print("=" * 68)
    print("           ErrandMate Modern Full-Stack & AI Autonomous Platform")
    print("=" * 68)
    print(f" [*] Database:        {DEFAULT_DB_PATH}")
    print(f" [*] Web Application: http://{HOST}:{PORT}/")
    print(f" [*] Swagger API Docs:http://{HOST}:{PORT}/docs")
    print(f" [*] ReDoc Reference: http://{HOST}:{PORT}/redoc")
    print(f" [*] Health Check:    http://{HOST}:{PORT}/api/health")
    print(f" [*] AI Telemetry:    http://{HOST}:{PORT}/api/ai/telemetry")
    print("=" * 68)
    print(" Starting Uvicorn asynchronous server...")
    print(" Press Ctrl+C to terminate.")
    print("=" * 68)

    # Automatically open web UI in default browser
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(f"http://{HOST}:{PORT}/")
        except Exception:
            pass

    uvicorn.run("server.app:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
