"""
RepoDoc Pro Backend — FastAPI Application Entry Point
"""

import argparse
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.routes import scanner, export, ai, search, petroleum, health
from api.middleware.logging_middleware import RequestLoggingMiddleware
from api.middleware.error_handler import ErrorHandlerMiddleware
from core.infrastructure.storage.temp_manager import TempManager
from utils.logging_config import setup_logging
from utils.config import Settings

# ─── Settings ─────────────────────────────────────────────────────────────────
settings = Settings()

# ─── Logging ──────────────────────────────────────────────────────────────────
setup_logging(level=settings.log_level, log_file=settings.log_file)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle."""
    logger.info("RepoDoc Pro backend starting up...")

    # Initialize temp directory
    temp_manager = TempManager(settings.temp_dir)
    await temp_manager.initialize()
    app.state.temp_manager = temp_manager

    logger.info(f"Backend ready on port {settings.port}")
    yield

    # Cleanup
    logger.info("Shutting down backend...")
    await temp_manager.cleanup()
    logger.info("Backend shutdown complete")


# ─── Application ──────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="RepoDoc Pro API",
        description="Backend API for RepoDoc Pro documentation generator",
        version="1.0.0",
        docs_url="/docs" if settings.env == "development" else None,
        redoc_url="/redoc" if settings.env == "development" else None,
        lifespan=lifespan,
    )

    # ─── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "app://.", "file://"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Routers ──────────────────────────────────────────────────────────────
    app.include_router(health.router, tags=["health"])
    app.include_router(scanner.router, prefix="/scanner", tags=["scanner"])
    app.include_router(export.router, prefix="/export", tags=["export"])
    app.include_router(ai.router, prefix="/ai", tags=["ai"])
    app.include_router(search.router, prefix="/search", tags=["search"])
    app.include_router(petroleum.router, prefix="/petroleum", tags=["petroleum"])

    # ─── Root & Favicon (avoid noisy 404s on bare GET /) ───────────────────────
    @app.get("/", tags=["health"])
    async def root() -> dict:
        """Friendly landing response — points to the real endpoints."""
        return {
            "name": "RepoDoc Pro API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if settings.env == "development" else "disabled in production (set REPODOC_ENV=development to enable)",
            "health": "/health",
            "endpoints": {
                "scanner": "/scanner/scan",
                "export": "/export/start",
                "ai_status": "/ai/status",
                "search": "/search/",
                "petroleum": "/petroleum/las/parse",
            },
        }

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        """Silence noisy browser favicon 404s in the logs."""
        return Response(status_code=204)

    return app


app = create_app()


# ─── Entry Point ──────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="RepoDoc Pro Backend")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--reload", action="store_true", help="Enable hot reload (dev)")
    args = parser.parse_args()

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
        workers=1,  # Single worker for Electron IPC compatibility
        ws_ping_interval=20,
        ws_ping_timeout=10,
    )


if __name__ == "__main__":
    main()
