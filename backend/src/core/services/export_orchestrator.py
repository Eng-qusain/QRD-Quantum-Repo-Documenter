"""
Export Orchestrator Service

Coordinates the full export pipeline:
  1. Load project scan
  2. Parse/process each file
  3. Optionally generate AI summaries
  4. Build PDF(s) according to export mode
  5. Report progress via callback
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from core.domain.entities.entities import ExportJob, ExportMode, FileCategory, FileInfo
from core.infrastructure.pdf.pdf_builder import PDFBuilder
from core.infrastructure.parsers.code_parser import CodeParser
from core.infrastructure.parsers.csv_parser import CSVParser
from core.infrastructure.parsers.excel_parser import ExcelParser
from core.infrastructure.parsers.image_parser import ImageParser
from core.infrastructure.ai.ai_documenter import AIDocumenter
from core.services.scanner_service import ProjectScannerService

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float, str], None]  # (job_id, percent, message)


class ExportOrchestratorService:
    """
    Orchestrates the complete export pipeline.

    Supports:
    - Mode A: Single combined PDF
    - Mode B: One PDF per folder
    - Mode C: One PDF per file
    - Mode D: Full documentation package
    """

    def __init__(
        self,
        scanner: ProjectScannerService,
        code_parser: CodeParser,
        csv_parser: CSVParser,
        excel_parser: ExcelParser,
        image_parser: ImageParser,
        ai_documenter: Optional[AIDocumenter] = None,
    ) -> None:
        self._scanner = scanner
        self._code_parser = code_parser
        self._csv_parser = csv_parser
        self._excel_parser = excel_parser
        self._image_parser = image_parser
        self._ai_documenter = ai_documenter

        # Active jobs registry
        self._jobs: dict[str, ExportJob] = {}
        self._cancel_events: dict[str, asyncio.Event] = {}

    async def start_export(
        self,
        project_path: str,
        output_path: str,
        mode: ExportMode,
        options: dict,
        progress_callback: Optional[ProgressCallback] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> str:
        """
        Start an export job asynchronously.

        Returns:
            job_id string for tracking progress
        """
        job_id = str(uuid.uuid4())
        cancel_event = asyncio.Event()
        self._cancel_events[job_id] = cancel_event

        job = ExportJob(
            id=job_id,
            project_path=project_path,
            mode=mode,
            output_path=output_path,
            status="pending",
            started_at=datetime.utcnow(),
        )
        self._jobs[job_id] = job

        # Run export in background
        asyncio.create_task(
            self._run_export(job, options, cancel_event, progress_callback, exclude_patterns)
        )

        return job_id

    async def cancel_export(self, job_id: str) -> None:
        """Cancel a running export job."""
        if event := self._cancel_events.get(job_id):
            event.set()
            if job := self._jobs.get(job_id):
                job.status = "cancelled"
            logger.info(f"Export job {job_id} cancelled")

    def get_job(self, job_id: str) -> Optional[ExportJob]:
        return self._jobs.get(job_id)

    async def _run_export(
        self,
        job: ExportJob,
        options: dict,
        cancel_event: asyncio.Event,
        progress_callback: Optional[ProgressCallback],
        exclude_patterns: Optional[list[str]],
    ) -> None:
        """Main export pipeline execution."""
        try:
            job.status = "running"
            self._report(progress_callback, job.id, 2.0, "Scanning project...")

            # Step 1: Scan project
            scan = await self._scanner.scan(
                project_path=job.project_path,
                exclude_patterns=exclude_patterns,
                progress_callback=lambda p, m: self._report(
                    progress_callback, job.id, p * 0.2, m  # scan = 0-20%
                ),
                cancel_event=cancel_event,
            )

            job.total_files = len(scan.flat_files)
            self._report(
                progress_callback, job.id, 20.0, f"Found {job.total_files} files"
            )

            # Step 2: Generate AI summaries (optional)
            ai_docs: dict[str, dict] = {}
            if options.get("include_ai") and self._ai_documenter and self._ai_documenter.is_available:
                self._report(progress_callback, job.id, 22.0, "Generating AI summaries...")
                ai_docs = await self._generate_ai_summaries(
                    scan.flat_files, cancel_event, progress_callback, job.id
                )
                self._report(progress_callback, job.id, 45.0, "AI summaries complete")

            # Step 3: Build PDFs based on mode
            if cancel_event.is_set():
                raise asyncio.CancelledError()

            self._report(progress_callback, job.id, 50.0, "Building PDF...")

            output_files = await self._build_pdfs(
                job, scan, ai_docs, options, cancel_event, progress_callback
            )

            job.output_files = output_files
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.progress = 100.0

            self._report(
                progress_callback,
                job.id,
                100.0,
                f"Export complete: {len(output_files)} file(s)",
            )
            logger.info(f"Export job {job.id} completed: {output_files}")

        except asyncio.CancelledError:
            job.status = "cancelled"
            logger.info(f"Export job {job.id} was cancelled")
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            logger.error(f"Export job {job.id} failed: {e}", exc_info=True)
            self._report(progress_callback, job.id, -1, f"Export failed: {e}")
        finally:
            self._cancel_events.pop(job.id, None)

    async def _generate_ai_summaries(
        self,
        files: list[FileInfo],
        cancel_event: asyncio.Event,
        progress_callback: Optional[ProgressCallback],
        job_id: str,
    ) -> dict[str, dict]:
        """Generate AI documentation for source files."""
        documenter = self._ai_documenter
        if documenter is None:
            return {}

        source_files = [
            f for f in files
            if f.category == FileCategory.SOURCE and not f.is_binary
        ][:50]  # Cap at 50 for cost control

        ai_docs: dict[str, dict] = {}
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent AI calls

        async def process_one(file_info: FileInfo) -> None:
            if cancel_event.is_set():
                return
            async with semaphore:
                try:
                    content = file_info.path.read_text(errors="replace")
                    doc = await documenter.document_file(
                        file_path=str(file_info.path),
                        content=content,
                        language=file_info.language.value if file_info.language else "unknown",
                    )
                    ai_docs[file_info.relative_path] = doc
                except Exception as e:
                    logger.warning(f"AI summary failed for {file_info.relative_path}: {e}")

        tasks = [process_one(f) for f in source_files]
        await asyncio.gather(*tasks, return_exceptions=True)
        return ai_docs

    async def _build_pdfs(
        self,
        job: ExportJob,
        scan,
        ai_docs: dict,
        options: dict,
        cancel_event: asyncio.Event,
        progress_callback: Optional[ProgressCallback],
    ) -> list[str]:
        """Build PDFs based on export mode."""
        mode = ExportMode(options.get("mode", "single"))
        output_path = Path(job.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if mode == ExportMode.SINGLE:
            return await self._build_single_pdf(
                job, scan, ai_docs, options, output_path, cancel_event, progress_callback
            )
        elif mode == ExportMode.FOLDER:
            return await self._build_folder_pdfs(
                job, scan, ai_docs, options, output_path, cancel_event, progress_callback
            )
        elif mode == ExportMode.FILE:
            return await self._build_per_file_pdfs(
                job, scan, ai_docs, options, output_path, cancel_event, progress_callback
            )
        elif mode == ExportMode.PACKAGE:
            return await self._build_package(
                job, scan, ai_docs, options, output_path, cancel_event, progress_callback
            )
        else:
            raise ValueError(f"Unknown export mode: {mode}")

    async def _build_single_pdf(
        self,
        job: ExportJob,
        scan,
        ai_docs: dict,
        options: dict,
        output_path: Path,
        cancel_event: asyncio.Event,
        progress_callback: Optional[ProgressCallback],
    ) -> list[str]:
        """Build a single combined PDF."""
        builder = self._create_builder(str(output_path), scan.project_name, options)

        stats_dict = self._stats_to_dict(scan.stats)
        builder.add_cover_page(scan.project_name, stats_dict)

        if options.get("include_toc", True):
            builder.add_toc()

        if options.get("include_stats", True):
            builder.add_statistics_page(stats_dict)

        total = len(scan.flat_files)
        for i, file_info in enumerate(scan.flat_files):
            if cancel_event.is_set():
                raise asyncio.CancelledError()

            await self._add_file_to_builder(builder, file_info, ai_docs, options)
            job.processed_files = i + 1
            job.current_file = file_info.relative_path
            pct = 50.0 + (i / total) * 48.0
            self._report(progress_callback, job.id, pct, f"Processing: {file_info.name}")

            # Yield to event loop every 10 files
            if i % 10 == 0:
                await asyncio.sleep(0)

        output_file = await asyncio.to_thread(builder.build)
        return [output_file]

    async def _build_package(
        self,
        job: ExportJob,
        scan,
        ai_docs: dict,
        options: dict,
        output_dir: Path,
        cancel_event: asyncio.Event,
        progress_callback: Optional[ProgressCallback],
    ) -> list[str]:
        """Build a full documentation package (Mode D)."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_files: list[str] = []

        tasks = [
            ("Documentation.pdf", self._build_single_pdf),
        ]

        for fname, builder_fn in tasks:
            if cancel_event.is_set():
                raise asyncio.CancelledError()

            out_path = output_dir / fname
            files = await builder_fn(
                job, scan, ai_docs, options, out_path, cancel_event, progress_callback
            )
            output_files.extend(files)

        return output_files

    async def _build_folder_pdfs(self, job, scan, ai_docs, options, output_dir, cancel_event, progress_callback) -> list[str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        files_by_folder: dict[str, list[FileInfo]] = {}

        for f in scan.flat_files:
            folder = str(Path(f.relative_path).parent)
            files_by_folder.setdefault(folder, []).append(f)

        output_files: list[str] = []
        for folder, folder_files in files_by_folder.items():
            if cancel_event.is_set():
                raise asyncio.CancelledError()

            safe_name = folder.replace("/", "_").replace("\\", "_") or "root"
            out_path = output_dir / f"{safe_name}.pdf"
            builder = self._create_builder(str(out_path), f"{scan.project_name} — {folder}", options)
            builder.add_cover_page(folder or "Root", description=f"Files in /{folder}")

            for fi in folder_files:
                await self._add_file_to_builder(builder, fi, ai_docs, options)

            result = await asyncio.to_thread(builder.build)
            output_files.append(result)

        return output_files

    async def _build_per_file_pdfs(self, job, scan, ai_docs, options, output_dir, cancel_event, progress_callback) -> list[str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_files: list[str] = []

        for i, fi in enumerate(scan.flat_files):
            if cancel_event.is_set():
                raise asyncio.CancelledError()

            safe_name = fi.relative_path.replace("/", "_").replace("\\", "_")
            out_path = output_dir / f"{safe_name}.pdf"
            builder = self._create_builder(str(out_path), fi.name, options)
            builder.add_cover_page(fi.name, description=fi.relative_path)
            await self._add_file_to_builder(builder, fi, ai_docs, options)
            result = await asyncio.to_thread(builder.build)
            output_files.append(result)

            pct = 50.0 + (i / len(scan.flat_files)) * 48.0
            self._report(progress_callback, job.id, pct, f"Built: {fi.name}")
            if i % 10 == 0:
                await asyncio.sleep(0)

        return output_files

    async def _add_file_to_builder(
        self,
        builder: PDFBuilder,
        file_info: FileInfo,
        ai_docs: dict,
        options: dict,
    ) -> None:
        """Add a single file's content to the PDF builder."""
        fi_dict = {
            "name": file_info.name,
            "relative_path": file_info.relative_path,
            "language": file_info.language.value if file_info.language else "",
            "line_count": file_info.line_count,
            "size_bytes": file_info.size_bytes,
            "last_modified": file_info.last_modified.strftime("%Y-%m-%d"),
        }

        try:
            if file_info.category == FileCategory.SOURCE and not file_info.is_binary:
                content = await asyncio.to_thread(file_info.path.read_text, errors="replace")
                builder.add_source_file(fi_dict, content, file_info.extension.lstrip("."))
                if options.get("include_ai") and file_info.relative_path in ai_docs:
                    builder.add_ai_summary(file_info.relative_path, ai_docs[file_info.relative_path])

            elif file_info.extension == ".csv":
                result = await asyncio.to_thread(
                    self._csv_parser.parse, str(file_info.path), options.get("max_csv_rows", 100)
                )
                builder.add_csv_preview(fi_dict, result["headers"], result["rows"], result["stats"])

            elif file_info.extension in (".png", ".jpg", ".jpeg", ".webp"):
                builder.add_image(fi_dict, str(file_info.path))

            elif file_info.category == FileCategory.CONFIG and not file_info.is_binary:
                content = await asyncio.to_thread(file_info.path.read_text, errors="replace")
                builder.add_source_file(fi_dict, content, file_info.extension.lstrip("."))

        except Exception as e:
            logger.warning(f"Could not add {file_info.relative_path} to PDF: {e}")

    def _create_builder(self, output_path: str, project_name: str, options: dict) -> PDFBuilder:
        return PDFBuilder(
            output_path=output_path,
            theme=options.get("theme", "default"),
            paper_size=options.get("paper_size", "A4"),
            orientation=options.get("orientation", "portrait"),
            font_size=options.get("font_size", 9),
            show_line_numbers=options.get("line_numbers", True),
            project_name=project_name,
        )

    @staticmethod
    def _stats_to_dict(stats) -> dict:
        return {
            "total_files": stats.total_files,
            "total_directories": stats.total_directories,
            "total_lines": stats.total_lines,
            "total_size_bytes": stats.total_size_bytes,
            "language_distribution": stats.language_distribution,
            "extension_distribution": stats.extension_distribution,
            "largest_files": stats.largest_files,
            "average_file_size": stats.average_file_size,
            "average_line_count": stats.average_line_count,
        }

    @staticmethod
    def _report(
        callback: Optional[ProgressCallback],
        job_id: str,
        progress: float,
        message: str,
    ) -> None:
        if callback:
            try:
                callback(job_id, progress, message)
            except Exception:
                pass
