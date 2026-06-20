"""Search Route"""
from fastapi import APIRouter
from core.infrastructure.petroleum.petroleum_parser import search_router as _sr
router = _sr
