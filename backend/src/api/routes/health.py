"""
Health Check Route
"""
from fastapi import APIRouter
from datetime import datetime
import sys

router = APIRouter()

@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "python": sys.version,
    }
