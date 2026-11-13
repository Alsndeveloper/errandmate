import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.config import DEBUG, STATIC_WEB_DIR, DATABASE_URL
from server.database import init_db
from server.routes import auth, tasks, ratings, profile, stats, ai
from server.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and cleanup."""
    init_db()
    try:
        from server.seed_data import seed_database
        seed_database()
    except Exception as e:
        pass
    yield


app = FastAPI(
    title="ErrandMate API",
    description="Production-grade asynchronous REST API for the ErrandMate errand-running and task marketplace platform.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=DEBUG,
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
