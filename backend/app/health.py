"""Liveness surface for the GHOST THREAD serving tier (Task 1).

Kept deliberately dependency-free: the API container's healthcheck and the
compose `depends_on: service_healthy` gate both hit this router, so it must
never touch the store, the LLM gateway, or any collection provider.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return the canonical liveness payload."""
    return {"status": "ok"}
