"""
Unit Tests — ProjectScannerService

Coverage targets: scanner, file classification, statistics computation.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from core.services.scanner_service import ProjectScannerService, EXTENSION_TO_LANGUAGE
from core.domain.entities.entities import FileCategory, Language


@pytest.fixture
def scanner() -> ProjectScannerService:
    return ProjectScannerService(chunk_size=10)


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a sample project directory for testing."""
    # Source files
    (tmp_path / "main.py").write_text(
        "#!/usr/bin/env python3\n\ndef main():\n    print('hello')\n\nif __name__ == '__main__':\n    main()\n"
    )
    (tmp_path / "utils.py").write_text(
        "import os\nimport sys\n\ndef helper(x: int) -> str:\n    return str(x)\n"
    )

    # Subdirectory
    src = tmp_path / "src"
    src.mkdir()
    (src / "api.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n")
    (src / "models.ts").write_text("export interface User { id: number; name: string; }\n")

    # Config files
    (tmp_path / "config.yaml").write_text("name: test\nversion: 1.0\n")
    (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}\n')

    # Data file
    data = tmp_path / "data"
    data.mkdir()
    (data / "results.csv").write_text("id,name,value\n1,alpha,100\n2,beta,200\n")

    # Excluded directory
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "main.cpython-311.pyc").write_bytes(b"\x00\x01\x02cached")

    # Markdown
    (tmp_path / "README.md").write_text("# Test Project\n\nThis is a test.\n")

    return tmp_path


class TestProjectScanner:
    def test_scan_basic(self, scanner: ProjectScannerService, sample_project: Path):
        """Scan should find all non-excluded files."""
        result = asyncio.run(scanner.scan(str(sample_project)))

        assert result.project_path == sample_project
        assert result.project_name == sample_project.name
        assert len(result.flat_files) > 0

        # Should not include __pycache__
        paths = {f.relative_path for f in result.flat_files}
        assert not any("__pycache__" in p for p in paths)

    def test_scan_finds_python_files(self, scanner: ProjectScannerService, sample_project: Path):
        result = asyncio.run(scanner.scan(str(sample_project)))
        py_files = [f for f in result.flat_files if f.extension == ".py"]
        assert len(py_files) >= 3

    def test_scan_language_detection(self, scanner: ProjectScannerService, sample_project: Path):
        result = asyncio.run(scanner.scan(str(sample_project)))

        languages = {f.relative_path: f.language for f in result.flat_files}
        py_files = [f for f in result.flat_files if f.extension == ".py"]
        ts_files = [f for f in result.flat_files if f.extension == ".ts"]

        assert all(f.language == Language.PYTHON for f in py_files)
        assert all(f.language == Language.TYPESCRIPT for f in ts_files)

    def test_scan_line_counts(self, scanner: ProjectScannerService, sample_project: Path):
        result = asyncio.run(scanner.scan(str(sample_project)))
        main_file = next(f for f in result.flat_files if f.name == "main.py")
        assert main_file.line_count == 7

    def test_scan_statistics(self, scanner: ProjectScannerService, sample_project: Path):
        result = asyncio.run(scanner.scan(str(sample_project)))
        stats = result.stats

        assert stats.total_files > 0
        assert stats.total_lines > 0
        assert stats.total_size_bytes > 0
        assert "Python" in stats.language_distribution
        assert stats.largest_files[0]["size"] >= stats.largest_files[-1]["size"]

    def test_scan_custom_exclude_patterns(self, scanner: ProjectScannerService, sample_project: Path):
        result = asyncio.run(scanner.scan(
            str(sample_project),
            exclude_patterns=["*.md", "*.json"]
        ))
        paths = {f.relative_path for f in result.flat_files}
        assert not any(p.endswith(".md") for p in paths)
        assert not any(p.endswith(".json") for p in paths)

    def test_scan_invalid_path(self, scanner: ProjectScannerService):
        with pytest.raises(FileNotFoundError):
            asyncio.run(scanner.scan("/nonexistent/path/that/does/not/exist"))

    def test_scan_not_a_directory(self, scanner: ProjectScannerService, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("hello")
        with pytest.raises(ValueError):
            asyncio.run(scanner.scan(str(f)))

    def test_scan_progress_callback(self, scanner: ProjectScannerService, sample_project: Path):
        progress_calls = []

        def on_progress(pct: float, msg: str):
            progress_calls.append((pct, msg))

        asyncio.run(scanner.scan(str(sample_project), progress_callback=on_progress))

        assert len(progress_calls) > 0
        assert progress_calls[-1][0] == 100.0

    def test_scan_cancellation(self, scanner: ProjectScannerService, sample_project: Path):
        import asyncio as _asyncio

        cancel_event = _asyncio.Event()
        cancel_event.set()  # Cancel immediately

        with pytest.raises(_asyncio.CancelledError):
            asyncio.run(scanner.scan(str(sample_project), cancel_event=cancel_event))

    def test_extension_language_map(self):
        assert EXTENSION_TO_LANGUAGE[".py"] == Language.PYTHON
        assert EXTENSION_TO_LANGUAGE[".ts"] == Language.TYPESCRIPT
        assert EXTENSION_TO_LANGUAGE[".sql"] == Language.SQL
        assert EXTENSION_TO_LANGUAGE[".yaml"] == Language.YAML

    def test_file_tree_structure(self, scanner: ProjectScannerService, sample_project: Path):
        result = asyncio.run(scanner.scan(str(sample_project)))
        tree = result.file_tree

        assert tree.name == sample_project.name
        assert tree.depth == 0

        # Should have children directories
        child_names = {c.name for c in tree.children_dirs}
        assert "src" in child_names or "data" in child_names

    def test_stats_language_distribution(self, scanner: ProjectScannerService, sample_project: Path):
        result = asyncio.run(scanner.scan(str(sample_project)))
        dist = result.stats.language_distribution

        assert "Python" in dist
        assert dist["Python"] >= 3

    def test_large_file_handling(self, scanner: ProjectScannerService, tmp_path: Path):
        """Files over the size limit should be marked as binary/skipped."""
        big_file = tmp_path / "big.py"
        big_file.write_bytes(b"x = 1\n" * 100)

        scanner_small = ProjectScannerService(max_file_size_bytes=100)
        result = asyncio.run(scanner_small.scan(str(tmp_path)))

        big = next((f for f in result.flat_files if f.name == "big.py"), None)
        assert big is not None
        assert big.is_binary or big.line_count is None


class TestFileClassification:
    def test_category_source(self, scanner: ProjectScannerService, tmp_path: Path):
        (tmp_path / "app.py").write_text("print('hi')")
        result = asyncio.run(scanner.scan(str(tmp_path)))
        f = next(f for f in result.flat_files if f.name == "app.py")
        assert f.category == FileCategory.SOURCE

    def test_category_data(self, scanner: ProjectScannerService, tmp_path: Path):
        (tmp_path / "data.csv").write_text("a,b\n1,2\n")
        result = asyncio.run(scanner.scan(str(tmp_path)))
        f = next(f for f in result.flat_files if f.name == "data.csv")
        assert f.category == FileCategory.DATA

    def test_binary_detection(self, scanner: ProjectScannerService, tmp_path: Path):
        (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        result = asyncio.run(scanner.scan(str(tmp_path)))
        f = next(f for f in result.flat_files if f.name == "image.png")
        assert f.is_binary
