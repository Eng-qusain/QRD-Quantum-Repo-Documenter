"""
Scanner API Routes — FastAPI router for project scanning.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.services.scanner_service import ProjectScannerService
from core.domain.entities.entities import FileCategory, Language

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency: shared scanner instance
_scanner = ProjectScannerService()


# ─── Request/Response Models ─────────────────────────────────────────────────

class ScanRequest(BaseModel):
    path: str
    exclude_patterns: list[str] = Field(default_factory=list)
    include_patterns: list[str] = Field(default_factory=list)


class FileNodeResponse(BaseModel):
    id: str
    name: str
    path: str
    relative_path: str
    type: str  # "file" | "directory"
    size: int
    line_count: Optional[int]
    language: Optional[str]
    extension: str
    last_modified: str
    children: Optional[list["FileNodeResponse"]] = None

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    project_path: str
    project_name: str
    file_tree: dict
    flat_files: list[dict]
    stats: dict
    scan_duration_ms: float


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/scan", response_model=ScanResponse)
async def scan_project(request: ScanRequest) -> ScanResponse:
    """
    Scan a project directory and return the file tree + stats.
    For large projects, use the WebSocket endpoint /scanner/ws for real-time progress.
    """
    try:
        result = await _scanner.scan(
            project_path=request.path,
            exclude_patterns=request.exclude_patterns or None,
            include_patterns=request.include_patterns or None,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")

    return ScanResponse(
        project_path=str(result.project_path),
        project_name=result.project_name,
        file_tree=_serialize_tree(result.file_tree),
        flat_files=[_serialize_file(f) for f in result.flat_files],
        stats=_serialize_stats(result.stats),
        scan_duration_ms=result.scan_duration_ms,
    )


@router.websocket("/ws")
async def scan_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time scan progress.

    Client sends: {"path": "...", "exclude_patterns": [...]}
    Server sends: {"type": "progress"|"complete"|"error", "progress": 0-100, "message": "..."}
    """
    await websocket.accept()
    cancel_event = asyncio.Event()

    try:
        data = await websocket.receive_json()

        async def on_progress(progress: float, message: str) -> None:
            try:
                await websocket.send_json({
                    "type": "progress",
                    "progress": progress,
                    "message": message,
                })
            except Exception:
                cancel_event.set()

        result = await _scanner.scan(
            project_path=data["path"],
            exclude_patterns=data.get("exclude_patterns"),
            progress_callback=on_progress,
            cancel_event=cancel_event,
        )

        await websocket.send_json({
            "type": "complete",
            "progress": 100.0,
            "message": "Scan complete",
            "data": {
                "project_path": str(result.project_path),
                "project_name": result.project_name,
                "file_tree": _serialize_tree(result.file_tree),
                "flat_files": [_serialize_file(f) for f in result.flat_files],
                "stats": _serialize_stats(result.stats),
                "scan_duration_ms": result.scan_duration_ms,
            },
        })

    except WebSocketDisconnect:
        cancel_event.set()
        logger.info("Scanner WebSocket client disconnected")
    except asyncio.CancelledError:
        await websocket.send_json({"type": "cancelled", "message": "Scan was cancelled"})
    except Exception as e:
        logger.error(f"WebSocket scan error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        cancel_event.set()


@router.get("/file-content")
async def get_file_content(path: str, max_lines: int = 5000) -> dict:
    """Get the content of a specific file for preview."""
    from pathlib import Path

    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        content = file_path.read_text(errors="replace")
        lines = content.split("\n")
        truncated = len(lines) > max_lines

        return {
            "content": "\n".join(lines[:max_lines]),
            "line_count": len(lines),
            "truncated": truncated,
            "encoding": "utf-8",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {e}")


# ─── Serializers ──────────────────────────────────────────────────────────────

def _serialize_tree(node) -> dict:
    result = {
        "id": str(node.path),
        "name": node.name,
        "path": str(node.path),
        "relative_path": node.relative_path,
        "type": "directory",
        "size": node.total_size,
        "extension": "",
        "last_modified": "",
        "children": [_serialize_tree(c) for c in node.children_dirs]
                    + [_serialize_file(f) for f in node.files],
    }
    return result


def _serialize_file(f) -> dict:
    return {
        "id": f.id,
        "name": f.name,
        "path": str(f.path),
        "relative_path": f.relative_path,
        "type": "file",
        "size": f.size_bytes,
        "line_count": f.line_count,
        "language": f.language.value if f.language else None,
        "extension": f.extension,
        "last_modified": f.last_modified.isoformat() if f.last_modified else "",
        "category": f.category.value if f.category else "unknown",
        "is_binary": f.is_binary,
    }


def _serialize_stats(s) -> dict:
    return {
        "total_files": s.total_files,
        "total_directories": s.total_directories,
        "total_lines": s.total_lines,
        "total_size_bytes": s.total_size_bytes,
        "language_distribution": s.language_distribution,
        "extension_distribution": s.extension_distribution,
        "category_distribution": s.category_distribution,
        "largest_files": s.largest_files,
        "average_file_size": s.average_file_size,
        "average_line_count": s.average_line_count,
    }
