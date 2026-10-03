"""FastAPI application factory for GHOST THREAD (Task 1).

Scaffold only — no agent logic, no store, no collection. Later phases mount
their routers here (`api/routes.py`, `api/websocket.py`, `api/mcp_server.py`)
via :func:`create_app` so this module stays the single composition root.

Run locally:
    uvicorn backend.app.main:app --reload
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.health import router as health_router

__all__ = ["app", "create_app"]

APP_NAME = "GHOST THREAD"
APP_VERSION = "0.1.0"


def _cors_origins() -> list[str]:
    """Dev-time CORS allowlist, overridable via `GHOST_CORS_ORIGINS` (comma separated)."""
    raw = os.getenv("GHOST_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    """Build the FastAPI app. Routers are mounted here and nowhere else."""
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        summary="Agentic OSINT gap-detection system — absence is the signal.",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Task 1: health only. Task 56/57 add /v1 REST, WebSocket, and MCP routers.
    app.include_router(health_router)

    @app.get("/", tags=["meta"], summary="Service banner")
    async def root() -> dict[str, str]:
        return {"service": APP_NAME, "version": APP_VERSION, "status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=os.getenv("GHOST_API_HOST", "0.0.0.0"),  # noqa: S104 - container-facing bind
        port=int(os.getenv("GHOST_API_PORT", "8000")),
        reload=bool(os.getenv("GHOST_API_RELOAD")),
    )
