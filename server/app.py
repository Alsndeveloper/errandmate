import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import logging

from server.config import CORS_ORIGINS, DATABASE_URL, DEBUG, SEED_DEMO_DATA, STATIC_WEB_DIR
from server.database import init_db
from server.routes import auth, tasks, ratings, profile, stats, ai
from server.schemas import HealthResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and cleanup."""
    init_db()
    if SEED_DEMO_DATA:
        from server.seed_data import seed_database
        try:
            seed_database()
        except Exception:
            # Don't hide failures: log them, but let the API still start.
            logger.exception("Demo data seeding failed")
    yield


app = FastAPI(
    title="ErrandMate API",
    description="REST API for the ErrandMate errand-running and task marketplace platform.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=DEBUG,
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    # Auth uses Bearer tokens, not cookies, so credentials aren't needed.
    # ("*" + credentials together is an insecure combination.)
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(ratings.router)
app.include_router(profile.router)
app.include_router(stats.router)
app.include_router(ai.router)


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check endpoint to verify server and database connectivity."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": f"SQLite connected ({Path(DATABASE_URL).name})",
        "timestamp": datetime.datetime.now().isoformat(),
    }


# Mount web frontend static directory if present
if STATIC_WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_WEB_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = STATIC_WEB_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "ErrandMate API is running. Web UI not found in /web."}
else:
    @app.get("/", include_in_schema=False)
    async def serve_root():
        return {
            "message": "Welcome to ErrandMate REST API v2.0",
            "docs": "/docs",
            "health": "/api/health",
        }
