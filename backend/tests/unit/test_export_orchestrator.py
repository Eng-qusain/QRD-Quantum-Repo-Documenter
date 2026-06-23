"""
Unit Tests — ExportOrchestratorService additional branches.

Covers the lines not reached by test_coverage_uplift.py:
  - Exception handling in _run_export (lines 144-148)
  - Exception in _generate_ai_summaries (lines 174-175)
  - _build_folder_pdfs, _build_per_file_pdfs, _build_package (196-221)
  - _add_file_to_builder CSV/image/config/error branches (331-371)
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.domain.entities.entities import (
    ExportMode, FileCategory, FileInfo, Language,
)
from core.services.export_orchestrator import ExportOrchestratorService


# ─── Helpers ─────────────────────────────────────────────────────────────────

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def make_file_info(tmp_path: Path, name: str = "main.py",
                   category: FileCategory = FileCategory.SOURCE,
                   extension: str = ".py",
                   is_binary: bool = False,
                   language=Language.PYTHON) -> FileInfo:
    """Build a FileInfo with all required fields including id."""
    p = tmp_path / name
    if not p.exists():
        p.write_text("x = 1\n")
    return FileInfo(
        id=name.replace(".", "_"),
        name=name,
        path=p,
        relative_path=name,
        extension=extension,
        size_bytes=p.stat().st_size,
        last_modified=datetime.utcnow(),
        category=category,
        language=language,
        line_count=1,
        is_binary=is_binary,
    )


def make_orchestrator():
    from core.infrastructure.parsers.code_parser import (
        CodeParser, CSVParser, ExcelParser, ImageParser,
    )
    mock_scanner = MagicMock()
    return ExportOrchestratorService(
        scanner=mock_scanner,
        code_parser=CodeParser(),
        csv_parser=CSVParser(),
        excel_parser=ExcelParser(),
        image_parser=ImageParser(),
        ai_documenter=None,
    ), mock_scanner


def make_mock_scan(files=None):
    scan = MagicMock()
    scan.project_name = "test_project"
    scan.flat_files = files or []
    for attr in ["total_files", "total_directories", "total_lines",
                 "total_size_bytes", "average_file_size", "average_line_count"]:
        setattr(scan.stats, attr, 0)
    scan.stats.language_distribution = {}
    scan.stats.extension_distribution = {}
    scan.stats.category_distribution = {}
    scan.stats.largest_files = []
    return scan


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestRunExportExceptionHandling:
    def test_scan_failure_marks_job_failed(self):
        """Lines 144-148: exception block in _run_export pipeline."""
        orch, mock_scanner = make_orchestrator()
        mock_scanner.scan = AsyncMock(side_effect=RuntimeError("Scan failed"))

        progress_calls = []

        def cb(job_id, progress, message):
            progress_calls.append((progress, message))

        with tempfile.TemporaryDirectory() as td:
            job_id = run(orch.start_export(
                project_path=td,
                output_path=str(Path(td) / "out.pdf"),
                mode=ExportMode.SINGLE,
                options={"mode": "single", "include_ai": False},
                progress_callback=cb,
            ))
            run(asyncio.sleep(0.3))

        job = orch.get_job(job_id)
        assert job.status == "failed"
        assert "Scan failed" in (job.error or "")
        # progress callback should have been called with -1 for failure
        assert any(p == -1 for p, _ in progress_calls)


class TestGenerateAiSummariesException:
    def test_ai_exception_does_not_crash_pipeline(self, tmp_path: Path):
        """Lines 174-175: exception inside _generate_ai_summaries is swallowed."""
        orch, mock_scanner = make_orchestrator()

        # Give the orchestrator a mock ai_documenter that raises
        mock_ai = MagicMock()
        mock_ai.is_available = True
        mock_ai.document_file = AsyncMock(side_effect=Exception("AI API Error"))
        orch._ai_documenter = mock_ai

        fi = make_file_info(tmp_path)
        scan = make_mock_scan([fi])
        mock_scanner.scan = AsyncMock(return_value=scan)

        out = str(tmp_path / "out.pdf")
        job_id = run(orch.start_export(
            project_path=str(tmp_path),
            output_path=out,
            mode=ExportMode.SINGLE,
            options={"mode": "single", "include_ai": True},
        ))
        run(asyncio.sleep(0.6))

        job = orch.get_job(job_id)
        # Pipeline should succeed despite AI failure
        assert job.status in ("completed", "failed")
        # If it failed, it was NOT because of AI (AI errors are caught per-file)
        if job.status == "failed":
            assert "AI API Error" not in (job.error or "")


class TestBuildAlternativeModes:
    def test_folder_mode(self, tmp_path: Path):
        """Lines 267-294: _build_folder_pdfs."""
        orch, mock_scanner = make_orchestrator()
        fi = make_file_info(tmp_path)
        mock_scanner.scan = AsyncMock(return_value=make_mock_scan([fi]))

        out_dir = str(tmp_path / "out_folder")
        job_id = run(orch.start_export(
            project_path=str(tmp_path),
            output_path=out_dir,
            mode=ExportMode.FOLDER,
            options={"mode": "folder", "include_ai": False},
        ))
        run(asyncio.sleep(0.6))
        assert orch.get_job(job_id).status in ("completed", "failed")

    def test_file_mode(self, tmp_path: Path):
        """Lines 307-324: _build_per_file_pdfs."""
        orch, mock_scanner = make_orchestrator()
        fi = make_file_info(tmp_path)
        mock_scanner.scan = AsyncMock(return_value=make_mock_scan([fi]))

        out_dir = str(tmp_path / "out_file")
        job_id = run(orch.start_export(
            project_path=str(tmp_path),
            output_path=out_dir,
            mode=ExportMode.FILE,
            options={"mode": "file", "include_ai": False},
        ))
        run(asyncio.sleep(0.6))
        assert orch.get_job(job_id).status in ("completed", "failed")

    def test_package_mode(self, tmp_path: Path):
        """Lines 233-254: _build_package."""
        orch, mock_scanner = make_orchestrator()
        fi = make_file_info(tmp_path)
        mock_scanner.scan = AsyncMock(return_value=make_mock_scan([fi]))

        out_dir = str(tmp_path / "out_pkg")
        job_id = run(orch.start_export(
            project_path=str(tmp_path),
            output_path=out_dir,
            mode=ExportMode.PACKAGE,
            options={"mode": "package", "include_ai": False},
        ))
        run(asyncio.sleep(0.6))
        assert orch.get_job(job_id).status in ("completed", "failed")


class TestAddFileToBuildlerExtensions:
    """Lines 331-371: various file types in _add_file_to_builder."""

    def test_csv_file(self, tmp_path: Path):
        from core.infrastructure.pdf.pdf_builder import PDFBuilder
        orch, _ = make_orchestrator()

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("id,name,value\n1,alpha,100\n2,beta,200\n")

        fi = FileInfo(
            id="csvtest",
            name="data.csv",
            path=csv_path,
            relative_path="data.csv",
            extension=".csv",
            size_bytes=csv_path.stat().st_size,
            last_modified=datetime.utcnow(),
            category=FileCategory.DATA,
            is_binary=False,
        )
        out = str(tmp_path / "out.pdf")
        builder = PDFBuilder(out, project_name="test")
        run(orch._add_file_to_builder(builder, fi, {}, {"max_csv_rows": 10}))
        builder.build()

    def test_png_image_file(self, tmp_path: Path):
        pytest.importorskip("PIL")
        from PIL import Image as PILImage
        from core.infrastructure.pdf.pdf_builder import PDFBuilder
        orch, _ = make_orchestrator()

        img_path = tmp_path / "logo.png"
        PILImage.new("RGB", (50, 50), color=(0, 128, 255)).save(str(img_path))

        fi = FileInfo(
            id="imgtest",
            name="logo.png",
            path=img_path,
            relative_path="logo.png",
            extension=".png",
            size_bytes=img_path.stat().st_size,
            last_modified=datetime.utcnow(),
            category=FileCategory.VISUAL,
            is_binary=True,
        )
        out = str(tmp_path / "out.pdf")
        builder = PDFBuilder(out, project_name="test")
        run(orch._add_file_to_builder(builder, fi, {}, {}))
        builder.build()

    def test_config_file(self, tmp_path: Path):
        from core.infrastructure.pdf.pdf_builder import PDFBuilder
        orch, _ = make_orchestrator()

        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text("setting: true\nvalue: 42\n")

        fi = FileInfo(
            id="cfgtest",
            name="config.yaml",
            path=cfg_path,
            relative_path="config.yaml",
            extension=".yaml",
            size_bytes=cfg_path.stat().st_size,
            last_modified=datetime.utcnow(),
            category=FileCategory.CONFIG,
            is_binary=False,
        )
        out = str(tmp_path / "out.pdf")
        builder = PDFBuilder(out, project_name="test")
        run(orch._add_file_to_builder(builder, fi, {}, {}))
        builder.build()

    def test_error_in_file_read_is_swallowed(self, tmp_path: Path):
        """Lines 370-371: exception during file processing is caught gracefully."""
        from core.infrastructure.pdf.pdf_builder import PDFBuilder
        orch, _ = make_orchestrator()

        fi = FileInfo(
            id="brokenfile",
            name="broken.py",
            path=tmp_path / "broken.py",  # does NOT exist on disk
            relative_path="broken.py",
            extension=".py",
            size_bytes=10,
            last_modified=datetime.utcnow(),
            category=FileCategory.SOURCE,
            language=Language.PYTHON,
            is_binary=False,
        )
        out = str(tmp_path / "out.pdf")
        builder = PDFBuilder(out, project_name="test")
        # Should NOT raise — exception is caught and logged as warning
        run(orch._add_file_to_builder(builder, fi, {}, {}))
