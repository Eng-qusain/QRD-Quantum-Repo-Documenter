"""
Domain Entities — Core Business Objects for RepoDoc Pro.

These are pure Python dataclasses with no external dependencies,
following Domain-Driven Design principles.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ─── Value Objects ────────────────────────────────────────────────────────────

class FileCategory(str, Enum):
    SOURCE = "source"
    DATA = "data"
    VISUAL = "visual"
    PETROLEUM = "petroleum"
    DOCUMENT = "document"
    CONFIG = "config"
    UNKNOWN = "unknown"


class Language(str, Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
    REACT_TSX = "React (TSX)"
    SHELL = "Shell"
    BASH = "Bash"
    YAML = "YAML"
    JSON = "JSON"
    TOML = "TOML"
    INI = "INI"
    HTML = "HTML"
    CSS = "CSS"
    SQL = "SQL"
    MARKDOWN = "Markdown"
    CSV = "CSV"
    XML = "XML"
    UNKNOWN = "Unknown"


class ExportMode(str, Enum):
    SINGLE = "single"       # One combined PDF
    FOLDER = "folder"       # One PDF per top-level folder
    FILE = "file"           # One PDF per file
    PACKAGE = "package"     # Full documentation package


# ─── Entities ─────────────────────────────────────────────────────────────────

@dataclass
class FileInfo:
    """Represents a single file in the project."""

    id: str
    name: str
    path: Path
    relative_path: str
    extension: str
    size_bytes: int
    last_modified: datetime
    category: FileCategory
    language: Optional[Language] = None
    line_count: Optional[int] = None
    encoding: str = "utf-8"
    is_binary: bool = False
    checksum: Optional[str] = None
    mime_type: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        return hashlib.md5(str(self.path).encode()).hexdigest()[:12]

    @property
    def size_kb(self) -> float:
        return self.size_bytes / 1024

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)

    @property
    def is_source_file(self) -> bool:
        return self.category == FileCategory.SOURCE

    @property
    def is_large(self) -> bool:
        return self.size_bytes > 10 * 1024 * 1024  # > 10MB


@dataclass
class DirectoryNode:
    """Represents a directory in the project tree."""

    name: str
    path: Path
    relative_path: str
    children_dirs: list[DirectoryNode] = field(default_factory=list)
    files: list[FileInfo] = field(default_factory=list)
    depth: int = 0

    @property
    def total_files(self) -> int:
        count = len(self.files)
        for child in self.children_dirs:
            count += child.total_files
        return count

    @property
    def total_size(self) -> int:
        size = sum(f.size_bytes for f in self.files)
        for child in self.children_dirs:
            size += child.total_size
        return size


@dataclass
class ProjectScan:
    """Result of scanning a project directory."""

    project_path: Path
    project_name: str
    scanned_at: datetime
    file_tree: DirectoryNode
    flat_files: list[FileInfo]
    stats: ProjectStats
    exclude_patterns: list[str] = field(default_factory=list)
    scan_duration_ms: float = 0.0


@dataclass
class ProjectStats:
    """Aggregated statistics for a project."""

    total_files: int
    total_directories: int
    total_lines: int
    total_size_bytes: int
    language_distribution: dict[str, int]
    extension_distribution: dict[str, int]
    category_distribution: dict[str, int]
    largest_files: list[dict]
    average_file_size: float
    average_line_count: float
    files_by_depth: dict[int, int] = field(default_factory=dict)


@dataclass
class AIDocumentation:
    """AI-generated documentation for a file."""

    file_id: str
    file_path: str
    summary: str
    purpose: str
    key_functions: list[str]
    inputs: list[str]
    outputs: list[str]
    dependencies: list[str]
    complexity: str  # Low / Medium / High / Very High
    notes: Optional[str] = None
    generated_at: Optional[datetime] = None
    model_used: Optional[str] = None


@dataclass
class ExportJob:
    """Represents an active or completed export operation."""

    id: str
    project_path: str
    mode: ExportMode
    output_path: str
    status: str  # pending / running / completed / failed / cancelled
    progress: float = 0.0
    current_file: str = ""
    total_files: int = 0
    processed_files: int = 0
    output_files: list[str] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def estimated_remaining_seconds(self) -> Optional[float]:
        if not self.started_at or self.progress <= 0:
            return None
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        if self.progress >= 100:
            return 0.0
        return elapsed * (100 - self.progress) / self.progress


@dataclass
class PetroleumWellData:
    """Petroleum-specific well data parsed from LAS/DLIS files."""

    well_name: str
    field: Optional[str]
    location: Optional[str]
    country: Optional[str]
    file_path: str
    file_format: str  # LAS / DLIS / LIS
    curves: list[dict]
    header: dict
    data_depth_range: Optional[tuple[float, float]] = None
    curve_count: int = 0
    sample_count: int = 0
