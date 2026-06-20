"""AI Documentation Route — API key is fully optional."""
from fastapi import APIRouter
from pydantic import BaseModel
from utils.config import Settings
from core.infrastructure.ai.ai_documenter import AIDocumenter

router = APIRouter()
settings = Settings()
_documenter = AIDocumenter(settings)


class AIDocRequest(BaseModel):
    file_path: str
    content: str
    language: str


@router.post("/document")
async def document_file(req: AIDocRequest) -> dict:
    """Generate AI documentation for a file. Works without API key (returns stub)."""
    return await _documenter.document_file(req.file_path, req.content, req.language)


@router.get("/status")
async def ai_status() -> dict:
    """Check AI provider configuration."""
    return {
        "enabled": settings.ai_enabled,
        "available": _documenter.is_available,
        "provider": _documenter._provider,
        "model": settings.ai_model if _documenter.is_available else None,
        "has_anthropic_key": bool(settings.anthropic_api_key),
        "has_openai_key": bool(settings.openai_api_key),
        "message": (
            "AI documentation active"
            if _documenter.is_available
            else "No API key configured — exports work normally, AI summaries will be skipped. "
                 "Add ANTHROPIC_API_KEY or OPENAI_API_KEY to backend/.env to enable."
        ),
    }
