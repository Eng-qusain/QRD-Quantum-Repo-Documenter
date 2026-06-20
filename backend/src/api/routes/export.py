"""
Export API Routes — FastAPI router for PDF export operations.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.domain.entities.entities import ExportMode
from core.services.export_orchestrator import ExportOrchestratorService
from core.services.scanner_service import ProjectScannerService
from core.infrastructure.parsers.code_parser import CodeParser
from core.infrastructure.parsers.csv_parser import CSVParser
from core.infrastructure.parsers.excel_parser import ExcelParser
from core.infrastructure.parsers.image_parser import ImageParser
from core.infrastructure.ai.ai_documenter import AIDocumenter
from utils.config import Settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = Settings()

# ─── Shared Orchestrator ──────────────────────────────────────────────────────
_ai_documenter = AIDocumenter(settings) if settings.ai_enabled else None

_orchestrator = ExportOrchestratorService(
    scanner=ProjectScannerService(),
    code_parser=CodeParser(),
    csv_parser=CSVParser(),
    excel_parser=ExcelParser(),
    image_parser=ImageParser(),
    ai_documenter=_ai_documenter,
)


# ─── Request / Response Models ────────────────────────────────────────────────

class ExportOptions(BaseModel):
    mode: str = "single"
    output_path: str
    include_ai: bool = True
    include_charts: bool = True
    include_toc: bool = True
    include_stats: bool = True
    include_dependencies: bool = True
    include_architecture: bool = False
    syntax_highlighting: bool = True
    line_numbers: bool = True
    max_csv_rows: int = 100
    paper_size: str = "A4"
    orientation: str = "portrait"
    theme: str = "default"
    font_size: int = 9
    selected_files: list[str] = Field(default_factory=list)


class StartExportRequest(BaseModel):
    project_path: str
    options: ExportOptions
    exclude_patterns: list[str] = Field(default_factory=list)


class ExportStartResponse(BaseModel):
    job_id: str
    message: str


class JobStatusResponse(BaseModel):
    id: str
    status: str
    progress: float
    current_file: str
    total_files: int
    processed_files: int
    output_files: list[str]
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    estimated_remaining_seconds: Optional[float]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/start", response_model=ExportStartResponse)
async def start_export(request: StartExportRequest) -> ExportStartResponse:
    """Start an export job. Returns job_id for tracking."""
    try:
        mode = ExportMode(request.options.mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid export mode: {request.options.mode}",
        )

    job_id = await _orchestrator.start_export(
        project_path=request.project_path,
        output_path=request.options.output_path,
        mode=mode,
        options=request.options.model_dump(),
        exclude_patterns=request.exclude_patterns,
    )

    return ExportStartResponse(
        job_id=job_id,
        message="Export started",
    )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Poll export job status."""
    job = _orchestrator.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobStatusResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        current_file=job.current_file,
        total_files=job.total_files,
        processed_files=job.processed_files,
        output_files=job.output_files,
        error=job.error,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        estimated_remaining_seconds=job.estimated_remaining_seconds,
    )


@router.post("/{job_id}/cancel")
async def cancel_export(job_id: str) -> dict:
    """Cancel a running export job."""
    await _orchestrator.cancel_export(job_id)
    return {"message": f"Job {job_id} cancellation requested"}


@router.websocket("/ws/{job_id}")
async def export_progress_ws(websocket: WebSocket, job_id: str) -> None:
    """
    WebSocket for real-time export progress.

    Server pushes: {"progress": 0-100, "message": "...", "status": "..."}
    Until status is "completed", "failed", or "cancelled".
    """
    await websocket.accept()

    try:
        while True:
            job = _orchestrator.get_job(job_id)
            if not job:
                await websocket.send_json({"error": "Job not found"})
                break

            await websocket.send_json({
                "progress": job.progress,
                "message": job.current_file or job.status,
                "status": job.status,
                "processed_files": job.processed_files,
                "total_files": job.total_files,
                "output_files": job.output_files,
                "error": job.error,
            })

            if job.status in ("completed", "failed", "cancelled"):
                break

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info(f"Export WebSocket client disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"Export WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
