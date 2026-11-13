import os
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
DEBUG = os.environ.get("DEBUG", "true").lower() in ("1", "true", "yes")

# Security Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "errandmate-cv-portfolio-super-secret-key-2026")
TOKEN_EXPIRY_HOURS = 24

# Static Web UI Path
STATIC_WEB_DIR = PROJECT_ROOT / "web"
