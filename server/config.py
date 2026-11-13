import logging
import os
import secrets
from pathlib import Path

# Base Paths
SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "ErrandMate" / "ErrandMate.db"

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_PATH", str(DEFAULT_DB_PATH))

# Server Configuration
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
DEBUG = os.environ.get("DEBUG", "false").lower() in ("1", "true", "yes")

# Security Configuration
# Never ship a hardcoded key: anyone who reads the repo could forge login tokens.
# Without SECRET_KEY set, a random key is generated per run (logins reset on restart).
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
if "SECRET_KEY" not in os.environ:
    logging.getLogger(__name__).warning(
        "SECRET_KEY not set: using a random per-process key. Set SECRET_KEY for persistent sessions."
    )
TOKEN_EXPIRY_HOURS = 24

# Browser origins allowed to call the API (comma-separated)
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
    if o.strip()
]

# Demo personas (admin/admin123 etc.) are for local demos only
SEED_DEMO_DATA = os.environ.get("SEED_DEMO_DATA", "true").lower() in ("1", "true", "yes")

# Static Web UI Path
STATIC_WEB_DIR = PROJECT_ROOT / "web"
