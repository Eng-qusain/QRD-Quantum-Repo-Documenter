"""
Project Scanner Service

Recursively scans a directory, classifies files, counts lines,
and builds the project tree. Supports 100K+ file repositories
via async chunked scanning with progress callbacks.
"""

from __future__ import annotations

import asyncio
import fnmatch
import hashlib
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from core.domain.entities.entities import (
    DirectoryNode,
    FileCategory,
    FileInfo,
    Language,
    ProjectScan,
    ProjectStats,
)

logger = logging.getLogger(__name__)

# ─── Extension Maps ───────────────────────────────────────────────────────────

EXTENSION_TO_LANGUAGE: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.REACT_TSX,
    ".jsx": Language.JAVASCRIPT,
    ".sh": Language.SHELL,
    ".bash": Language.BASH,
    ".zsh": Language.SHELL,
    ".yaml": Language.YAML,
    ".yml": Language.YAML,
    ".json": Language.JSON,
    ".toml": Language.TOML,
    ".ini": Language.INI,
    ".cfg": Language.INI,
    ".html": Language.HTML,
    ".htm": Language.HTML,
    ".css": Language.CSS,
    ".scss": Language.CSS,
    ".sass": Language.CSS,
    ".sql": Language.SQL,
    ".md": Language.MARKDOWN,
    ".rst": Language.MARKDOWN,
    ".xml": Language.XML,
}

EXTENSION_TO_CATEGORY: dict[str, FileCategory] = {
    # Source
    ".py": FileCategory.SOURCE,
    ".js": FileCategory.SOURCE,
    ".ts": FileCategory.SOURCE,
    ".tsx": FileCategory.SOURCE,
    ".jsx": FileCategory.SOURCE,
    ".sh": FileCategory.SOURCE,
    ".bash": FileCategory.SOURCE,
    ".zsh": FileCategory.SOURCE,
    ".yaml": FileCategory.CONFIG,
    ".yml": FileCategory.CONFIG,
    ".json": FileCategory.CONFIG,
    ".toml": FileCategory.CONFIG,
    ".ini": FileCategory.CONFIG,
    ".cfg": FileCategory.CONFIG,
    ".html": FileCategory.SOURCE,
    ".css": FileCategory.SOURCE,
    ".scss": FileCategory.SOURCE,
    ".sql": FileCategory.SOURCE,
    ".md": FileCategory.DOCUMENT,
    ".rst": FileCategory.DOCUMENT,
    ".xml": FileCategory.CONFIG,
    # Data
    ".csv": FileCategory.DATA,
    ".xlsx": FileCategory.DATA,
    ".xls": FileCategory.DATA,
    ".parquet": FileCategory.DATA,
    ".txt": FileCategory.DOCUMENT,
    # Visual
    ".svg": FileCategory.VISUAL,
    ".png": FileCategory.VISUAL,
    ".jpg": FileCategory.VISUAL,
    ".jpeg": FileCategory.VISUAL,
    ".webp": FileCategory.VISUAL,
    # Petroleum
    ".las": FileCategory.PETROLEUM,
    ".dlis": FileCategory.PETROLEUM,
    ".lis": FileCategory.PETROLEUM,
    # Documents
    ".pdf": FileCategory.DOCUMENT,
    ".docx": FileCategory.DOCUMENT,
}

BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".docx", ".xlsx", ".xls",
                     ".parquet", ".dlis", ".lis", ".gif", ".ico", ".woff", ".woff2", ".ttf"}

DEFAULT_EXCLUDE_PATTERNS = [
    "__pycache__", "*.pyc", "*.pyo", "*.pyd",
    "node_modules", ".npm",
    ".git", ".svn", ".hg",
    ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt",
    "coverage", ".nyc_output",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "*.egg-info", "*.egg",
    ".DS_Store", "Thumbs.db",
]


# ─── Scanner ──────────────────────────────────────────────────────────────────

class ProjectScannerService:
    """
    Async service that scans a project directory recursively.

    Supports:
    - Progress callbacks (for real-time UI updates via WebSocket)
    - Exclude patterns (glob-style)
    - Chunked processing to avoid blocking the event loop
    - Cancellation support via asyncio.Event
    """

    def __init__(
        self,
        chunk_size: int = 500,
        max_file_size_bytes: int = 50 * 1024 * 1024,
    ) -> None:
        self._chunk_size = chunk_size
        self._max_file_size = max_file_size_bytes

    async def scan(
        self,
        project_path: str,
        exclude_patterns: Optional[list[str]] = None,
        include_patterns: Optional[list[str]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> ProjectScan:
        """
        Scan a project directory and return a ProjectScan result.

        Args:
            project_path: Absolute path to project root
            exclude_patterns: Glob patterns to exclude
            include_patterns: If provided, only include matching files
            progress_callback: Called with (percent, current_path) as scanning progresses
            cancel_event: Set this event to cancel the scan

        Returns:
            ProjectScan with file tree and statistics
        """
        start_time = time.time()
        root = Path(project_path).resolve()

        if not root.exists():
            raise FileNotFoundError(f"Project path does not exist: {root}")
        if not root.is_dir():
            raise ValueError(f"Path is not a directory: {root}")

        patterns = list(DEFAULT_EXCLUDE_PATTERNS) + (exclude_patterns or [])
        logger.info(f"Scanning {root} with {len(patterns)} exclude patterns")

        # Phase 1: Collect all file paths
        all_paths = await self._collect_paths(root, patterns, cancel_event)
        total = len(all_paths)
        logger.info(f"Found {total} files to process")

        if progress_callback:
            progress_callback(5.0, f"Found {total} files")

        # Phase 2: Process files in chunks
        flat_files: list[FileInfo] = []
        processed = 0

        for chunk_start in range(0, total, self._chunk_size):
            if cancel_event and cancel_event.is_set():
                raise asyncio.CancelledError("Scan cancelled by user")

            chunk = all_paths[chunk_start : chunk_start + self._chunk_size]
            chunk_results = await asyncio.gather(
                *[self._process_file(p, root) for p in chunk],
                return_exceptions=True,
            )

            for result in chunk_results:
                if isinstance(result, FileInfo):
                    flat_files.append(result)
                elif isinstance(result, Exception):
                    logger.debug(f"File processing error: {result}")

            processed += len(chunk)
            pct = 5.0 + (processed / total) * 80.0
            if progress_callback:
                progress_callback(pct, f"Processed {processed}/{total} files")

            # Yield control to event loop
            await asyncio.sleep(0)

        # Phase 3: Build tree
        if progress_callback:
            progress_callback(90.0, "Building file tree...")

        file_tree = await asyncio.to_thread(self._build_tree, root, flat_files)

        # Phase 4: Compute statistics
        if progress_callback:
            progress_callback(95.0, "Computing statistics...")

        stats = self._compute_stats(flat_files)

        duration_ms = (time.time() - start_time) * 1000

        if progress_callback:
            progress_callback(100.0, "Scan complete")

        logger.info(
            f"Scan complete: {len(flat_files)} files in {duration_ms:.0f}ms"
        )

        return ProjectScan(
            project_path=root,
            project_name=root.name,
            scanned_at=datetime.utcnow(),
            file_tree=file_tree,
            flat_files=flat_files,
            stats=stats,
            exclude_patterns=patterns,
            scan_duration_ms=duration_ms,
        )

    async def _collect_paths(
        self,
        root: Path,
        exclude_patterns: list[str],
        cancel_event: Optional[asyncio.Event],
    ) -> list[Path]:
        """Collect all file paths respecting exclude patterns."""
        return await asyncio.to_thread(
            self._walk_directory, root, exclude_patterns, cancel_event
        )

    def _walk_directory(
        self,
        root: Path,
        exclude_patterns: list[str],
        cancel_event: Optional[asyncio.Event],
    ) -> list[Path]:
        """Synchronous directory walk (runs in thread pool)."""
        result: list[Path] = []

        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            if cancel_event and cancel_event.is_set():
                break

            current = Path(dirpath)
            rel = current.relative_to(root)

            # Filter directories in-place
            dirnames[:] = [
                d for d in sorted(dirnames)
                if not self._should_exclude(d, str(rel / d), exclude_patterns)
            ]

            for fname in sorted(filenames):
                rel_file = str(rel / fname) if str(rel) != "." else fname
                if not self._should_exclude(fname, rel_file, exclude_patterns):
                    result.append(current / fname)

        return result

    def _should_exclude(self, name: str, rel_path: str, patterns: list[str]) -> bool:
        """Check if a file/dir should be excluded."""
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        return False

    async def _process_file(self, path: Path, root: Path) -> FileInfo:
        """Process a single file, computing metadata."""
        return await asyncio.to_thread(self._process_file_sync, path, root)

    def _process_file_sync(self, path: Path, root: Path) -> FileInfo:
        """Synchronous file processing (runs in thread pool)."""
        stat = path.stat()
        ext = path.suffix.lower()
        rel = str(path.relative_to(root))

        is_binary = ext in BINARY_EXTENSIONS
        category = EXTENSION_TO_CATEGORY.get(ext, FileCategory.UNKNOWN)
        language = EXTENSION_TO_LANGUAGE.get(ext)
        line_count = None

        if not is_binary and stat.st_size < self._max_file_size:
            try:
                content = path.read_bytes()
                # Detect binary via null bytes
                if b"\x00" in content[:8192]:
                    is_binary = True
                else:
                    decoded = content.decode("utf-8", errors="replace")
                    line_count = decoded.count("\n") + (1 if decoded and not decoded.endswith("\n") else 0)
            except (OSError, MemoryError):
                is_binary = True

        file_id = hashlib.md5(rel.encode()).hexdigest()[:12]

        return FileInfo(
            id=file_id,
            name=path.name,
            path=path,
            relative_path=rel,
            extension=ext,
            size_bytes=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            category=category,
            language=language,
            line_count=line_count,
            is_binary=is_binary,
        )

    def _build_tree(self, root: Path, files: list[FileInfo]) -> DirectoryNode:
        """Build a directory tree from flat file list."""
        # Index files by their parent directory
        dir_files: dict[str, list[FileInfo]] = {}
        for f in files:
            parent = str(Path(f.relative_path).parent)
            if parent == ".":
                parent = ""
            dir_files.setdefault(parent, []).append(f)

        # Collect all directories
        all_dirs: set[str] = {""}
        for f in files:
            parts = Path(f.relative_path).parent.parts
            for i in range(len(parts)):
                all_dirs.add("/".join(parts[: i + 1]))

        def build_node(rel_path: str, depth: int) -> DirectoryNode:
            abs_path = root / rel_path if rel_path else root
            node = DirectoryNode(
                name=abs_path.name if rel_path else root.name,
                path=abs_path,
                relative_path=rel_path or ".",
                files=dir_files.get(rel_path, []),
                depth=depth,
            )

            # Find immediate child directories
            for d in sorted(all_dirs):
                if not d or d == rel_path:
                    continue
                parent = str(Path(d).parent) if Path(d).parent != Path(".") else ""
                if parent == rel_path:
                    node.children_dirs.append(build_node(d, depth + 1))

            return node

        return build_node("", 0)

    def _compute_stats(self, files: list[FileInfo]) -> ProjectStats:
        """Compute project-wide statistics."""
        lang_dist: dict[str, int] = {}
        ext_dist: dict[str, int] = {}
        cat_dist: dict[str, int] = {}

        total_lines = 0
        total_size = 0

        for f in files:
            # Language
            lang = f.language.value if f.language else "Unknown"
            lang_dist[lang] = lang_dist.get(lang, 0) + 1

            # Extension
            ext_dist[f.extension or "(no ext)"] = ext_dist.get(f.extension or "(no ext)", 0) + 1

            # Category
            cat = f.category.value
            cat_dist[cat] = cat_dist.get(cat, 0) + 1

            # Totals
            total_size += f.size_bytes
            if f.line_count:
                total_lines += f.line_count

        sorted_by_size = sorted(files, key=lambda f: f.size_bytes, reverse=True)
        largest = [
            {
                "path": f.relative_path,
                "size": f.size_bytes,
                "lines": f.line_count or 0,
                "language": f.language.value if f.language else "Unknown",
            }
            for f in sorted_by_size[:20]
        ]

        return ProjectStats(
            total_files=len(files),
            total_directories=len({str(Path(f.relative_path).parent) for f in files}),
            total_lines=total_lines,
            total_size_bytes=total_size,
            language_distribution=lang_dist,
            extension_distribution=ext_dist,
            category_distribution=cat_dist,
            largest_files=largest,
            average_file_size=total_size / len(files) if files else 0,
            average_line_count=total_lines / len(files) if files else 0,
        )
