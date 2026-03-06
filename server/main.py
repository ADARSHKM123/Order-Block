"""FastAPI application entry point."""

import logging
import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database.connection import init_db
from .routers import images, processing, sessions

logger = logging.getLogger("order_block.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    logger.info(f"Image Sorter GUI running at http://{settings.host}:{settings.port}")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS for development (Vite dev server on :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers (must come before static mount)
app.include_router(sessions.router)
app.include_router(processing.router)
app.include_router(images.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": settings.app_version}


# Serve built frontend in production (must be last — catches all non-API routes)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


def start_server(open_browser: bool = True):
    """Start the server and optionally open the browser."""
    if open_browser:
        # Open browser after a short delay so server has time to start
        def _open():
            time.sleep(1.5)
            webbrowser.open(f"http://{settings.host}:{settings.port}")

        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
