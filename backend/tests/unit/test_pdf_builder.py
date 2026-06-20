"""
Unit Tests — PDFBuilder

Tests PDF generation without requiring a full project scan.
"""

import os
import tempfile
from pathlib import Path

import pytest

from core.infrastructure.pdf.pdf_builder import PDFBuilder, THEMES


class TestPDFBuilder:
    @pytest.fixture
    def tmp_pdf(self, tmp_path: Path) -> str:
        return str(tmp_path / "test_output.pdf")

    def test_build_empty_pdf(self, tmp_pdf: str):
        """Should produce a valid PDF file."""
        builder = PDFBuilder(tmp_pdf, project_name="Test Project")
        builder.add_cover_page("Test Project")
        result = builder.build()
        assert result == tmp_pdf
        assert Path(tmp_pdf).exists()
        assert Path(tmp_pdf).stat().st_size > 1000  # Non-trivial size

    def test_pdf_with_toc(self, tmp_pdf: str):
        builder = PDFBuilder(tmp_pdf, project_name="TOC Test")
        builder.add_cover_page("TOC Test")
        builder.add_toc()
        builder.add_section_header("Section One", level=1)
        builder.add_section_header("Subsection", level=2)
        result = builder.build()
        assert Path(result).exists()

    def test_pdf_with_source_code(self, tmp_pdf: str):
        builder = PDFBuilder(tmp_pdf, project_name="Code Test")
        builder.add_cover_page("Code Test")
        file_info = {
            "name": "main.py",
            "relative_path": "src/main.py",
            "language": "Python",
            "line_count": 5,
            "size_bytes": 120,
            "last_modified": "2024-01-15",
        }
        code = "def main():\n    print('hello world')\n\nif __name__ == '__main__':\n    main()\n"
        builder.add_source_file(file_info, code, "python")
        result = builder.build()
        assert Path(result).exists()
        assert Path(result).stat().st_size > 2000

    def test_pdf_with_csv_preview(self, tmp_pdf: str):
        builder = PDFBuilder(tmp_pdf, project_name="CSV Test")
        builder.add_cover_page("CSV Test")
        file_info = {"name": "data.csv", "relative_path": "data/data.csv", "size_bytes": 500}
        headers = ["id", "name", "value", "category"]
        rows = [[str(i), f"item_{i}", str(i * 10), "A" if i % 2 == 0 else "B"] for i in range(20)]
        stats = {"row_count": 100, "column_count": 4, "truncated": True}
        builder.add_csv_preview(file_info, headers, rows, stats)
        result = builder.build()
        assert Path(result).exists()

    def test_pdf_with_statistics(self, tmp_pdf: str):
        builder = PDFBuilder(tmp_pdf, project_name="Stats Test")
        builder.add_cover_page("Stats Test")
        stats = {
            "total_files": 250,
            "total_directories": 18,
            "total_lines": 45000,
            "total_size_bytes": 2_500_000,
            "language_distribution": {"Python": 120, "TypeScript": 80, "YAML": 30, "SQL": 20},
            "average_file_size": 10000,
            "average_line_count": 180,
            "largest_files": [
                {"path": "main.py", "size": 50000, "lines": 1200},
                {"path": "api.py", "size": 30000, "lines": 800},
            ],
        }
        builder.add_statistics_page(stats)
        result = builder.build()
        assert Path(result).exists()

    def test_all_themes_produce_valid_pdf(self, tmp_path: Path):
        """Each theme should produce a valid PDF."""
        for theme_name in THEMES:
            out = str(tmp_path / f"test_{theme_name}.pdf")
            builder = PDFBuilder(out, theme=theme_name, project_name=f"Theme: {theme_name}")
            builder.add_cover_page(f"Theme Test: {theme_name}")
            builder.add_source_file(
                {"name": "test.py", "relative_path": "test.py", "language": "Python",
                 "line_count": 3, "size_bytes": 60, "last_modified": "2024-01-01"},
                "x = 1\ny = 2\nz = x + y\n",
                "python",
            )
            result = builder.build()
            assert Path(result).exists(), f"PDF not created for theme: {theme_name}"
            assert Path(result).stat().st_size > 500

    def test_all_paper_sizes(self, tmp_path: Path):
        for size in ["A4", "Letter", "A3"]:
            out = str(tmp_path / f"test_{size}.pdf")
            builder = PDFBuilder(out, paper_size=size, project_name="Size Test")
            builder.add_cover_page("Test")
            assert Path(builder.build()).exists()

    def test_line_numbers_toggle(self, tmp_pdf: str):
        builder = PDFBuilder(tmp_pdf, show_line_numbers=False)
        builder.add_cover_page("No Line Numbers")
        builder.add_source_file(
            {"name": "f.py", "relative_path": "f.py", "language": "Python",
             "line_count": 2, "size_bytes": 20, "last_modified": "2024-01-01"},
            "x = 1\ny = 2\n",
            "python",
        )
        assert Path(builder.build()).exists()

    def test_ai_summary_section(self, tmp_pdf: str):
        builder = PDFBuilder(tmp_pdf, project_name="AI Test")
        builder.add_cover_page("AI Summary Test")
        builder.add_ai_summary("src/main.py", {
            "summary": "Entry point for the application",
            "purpose": "Initializes FastAPI and registers routes",
            "key_functions": ["main()", "create_app()", "register_routes()"],
            "inputs": ["CLI arguments: --port, --host"],
            "outputs": ["Running ASGI server"],
            "dependencies": ["fastapi", "uvicorn", "pydantic"],
            "complexity": "Low",
            "notes": "Uses lifespan context manager for startup/shutdown",
        })
        assert Path(builder.build()).exists()

    def test_large_code_block(self, tmp_pdf: str):
        """Very long code files should not crash the builder."""
        builder = PDFBuilder(tmp_pdf, project_name="Large File Test")
        builder.add_cover_page("Large Code Test")
        long_code = "\n".join(f"x_{i} = {i} * {i}  # line {i}" for i in range(500))
        builder.add_source_file(
            {"name": "large.py", "relative_path": "large.py", "language": "Python",
             "line_count": 500, "size_bytes": len(long_code), "last_modified": "2024-01-01"},
            long_code,
            "python",
        )
        result = builder.build()
        assert Path(result).exists()
        assert Path(result).stat().st_size > 10_000

    def test_format_size_helper(self):
        assert PDFBuilder._format_size(500) == "500 B"
        assert PDFBuilder._format_size(2048) == "2.0 KB"
        assert PDFBuilder._format_size(1_500_000) == "1.4 MB"
        assert PDFBuilder._format_size(2_000_000_000) == "1.86 GB"
