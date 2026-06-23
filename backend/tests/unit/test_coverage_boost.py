"""
Unit Tests — AIDocumenter and Petroleum Parser

These test the stub/no-key path of AIDocumenter (doesn't require API key)
and the search_files function and basic parse helpers in petroleum_parser.
"""

import tempfile
import pytest
from pathlib import Path


# ─── AIDocumenter (stub mode — no API key required) ──────────────────────────

class TestAIDocumenterStub:
    """Tests the stub/offline path — no API key needed."""

    @pytest.fixture
    def settings_stub(self):
        """Minimal settings object with no API keys configured."""
        class StubSettings:
            anthropic_api_key = None
            openai_api_key = None
            ai_model = "claude-3-5-haiku-20241022"
            ai_enabled = True
        return StubSettings()

    @pytest.fixture
    def documenter(self, settings_stub):
        from core.infrastructure.ai.ai_documenter import AIDocumenter
        return AIDocumenter(settings_stub)

    def test_is_available_false_without_keys(self, documenter):
        assert documenter.is_available is False

    def test_provider_is_none_without_keys(self, documenter):
        assert documenter._provider == "none"

    def test_document_file_returns_stub(self, documenter):
        import asyncio
        result = asyncio.run(documenter.document_file(
            file_path="src/main.py",
            content="def main(): pass",
            language="python",
        ))
        assert isinstance(result, dict)
        assert "summary" in result
        assert "purpose" in result
        assert "key_functions" in result
        assert "inputs" in result
        assert "outputs" in result
        assert "dependencies" in result
        assert "complexity" in result

    def test_stub_always_returns_dict(self, documenter):
        import asyncio
        # Even empty content, binary-ish content, very long content — all return a dict
        for content in ["", "x" * 10000, "def x():\n    pass\n" * 100]:
            result = asyncio.run(documenter.document_file("f.py", content, "python"))
            assert isinstance(result, dict)
            assert len(result) >= 7  # All required keys present

    def test_stub_documentation_static_method(self):
        from core.infrastructure.ai.ai_documenter import AIDocumenter
        result = AIDocumenter._stub_documentation("path/to/file.py", "python")
        assert "summary" in result
        assert "python" in result["notes"].lower() or "Python" in result["notes"]

    def test_parse_json_response_valid(self):
        from core.infrastructure.ai.ai_documenter import AIDocumenter
        import json
        payload = {
            "summary": "test", "purpose": "test", "key_functions": [],
            "inputs": [], "outputs": [], "dependencies": [], "complexity": "Low", "notes": ""
        }
        result = AIDocumenter._parse_json_response(json.dumps(payload))
        assert result["summary"] == "test"
        assert result["complexity"] == "Low"

    def test_parse_json_response_with_markdown_fences(self):
        from core.infrastructure.ai.ai_documenter import AIDocumenter
        import json
        payload = {"summary": "ok", "purpose": "", "key_functions": [],
                   "inputs": [], "outputs": [], "dependencies": [], "complexity": "High", "notes": ""}
        raw = f"```json\n{json.dumps(payload)}\n```"
        result = AIDocumenter._parse_json_response(raw)
        assert result["summary"] == "ok"

    def test_parse_json_response_invalid_returns_dict(self):
        from core.infrastructure.ai.ai_documenter import AIDocumenter
        result = AIDocumenter._parse_json_response("not valid json at all {{{{")
        assert isinstance(result, dict)
        assert "summary" in result


# ─── Petroleum Parser — Search Route and LAS stub ─────────────────────────────

class TestSearchFiles:
    """Tests the search_files function via HTTP (already tested in integration)
    and directly to cover the petroleum_parser.py code paths."""

    @pytest.fixture
    def project_dir(self, tmp_path: Path) -> Path:
        (tmp_path / "main.py").write_text("def main(): pass\n")
        (tmp_path / "utils.py").write_text("import os\nHELLO = 'world'\n")
        sub = tmp_path / "lib"
        sub.mkdir()
        (sub / "helper.ts").write_text("export function help() { return 42; }\n")
        (tmp_path / "data.csv").write_text("a,b\n1,2\n")
        return tmp_path

    @pytest.mark.asyncio
    async def test_search_by_filename(self, project_dir: Path):
        from core.infrastructure.petroleum.petroleum_parser import search_files
        result = await search_files(
            project_path=str(project_dir),
            query="main",
            search_type="filename",
        )
        assert result["count"] >= 1
        assert any("main" in r["relative_path"] for r in result["results"])

    @pytest.mark.asyncio
    async def test_search_by_extension(self, project_dir: Path):
        from core.infrastructure.petroleum.petroleum_parser import search_files
        result = await search_files(
            project_path=str(project_dir),
            query=".py",
            search_type="extension",
        )
        assert result["count"] >= 2
        assert all(r["relative_path"].endswith(".py") for r in result["results"])

    @pytest.mark.asyncio
    async def test_search_by_content(self, project_dir: Path):
        from core.infrastructure.petroleum.petroleum_parser import search_files
        result = await search_files(
            project_path=str(project_dir),
            query="HELLO",
            search_type="content",
        )
        assert result["count"] >= 1
        assert any("utils" in r["relative_path"] for r in result["results"])

    @pytest.mark.asyncio
    async def test_search_nonexistent_project(self):
        from fastapi import HTTPException
        from core.infrastructure.petroleum.petroleum_parser import search_files
        with pytest.raises(HTTPException) as exc_info:
            await search_files(
                project_path="/no/such/path",
                query="anything",
                search_type="filename",
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_search_max_results_respected(self, project_dir: Path):
        from core.infrastructure.petroleum.petroleum_parser import search_files
        result = await search_files(
            project_path=str(project_dir),
            query="",
            search_type="filename",
            max_results=2,
        )
        assert result["count"] <= 2

    def test_las_parser_missing_file(self):
        from core.infrastructure.petroleum.petroleum_parser import LASParser
        parser = LASParser()
        result = parser.parse("/nonexistent/file.las")
        assert "error" in result

    def test_production_csv_parser_empty(self, tmp_path: Path):
        from core.infrastructure.petroleum.petroleum_parser import ProductionCSVParser
        f = tmp_path / "prod.csv"
        f.write_text("date,oil_rate,gas_rate\n2024-01,100,500\n2024-02,95,480\n")
        parser = ProductionCSVParser()
        result = parser.parse(str(f))
        assert "identified_columns" in result
        assert "oil" in result["identified_columns"] or "date" in result["identified_columns"]

    def test_production_csv_empty_file(self, tmp_path: Path):
        from core.infrastructure.petroleum.petroleum_parser import ProductionCSVParser
        f = tmp_path / "empty.csv"
        f.write_text("col1,col2\n")
        parser = ProductionCSVParser()
        result = parser.parse(str(f))
        assert isinstance(result, dict)


# ─── ExcelParser ─────────────────────────────────────────────────────────────

class TestExcelParser:
    def test_parse_nonexistent_file(self):
        from core.infrastructure.parsers.code_parser import ExcelParser
        result = ExcelParser().parse("/no/such/file.xlsx")
        assert "error" in result

    def test_parse_valid_xlsx(self, tmp_path: Path):
        pytest.importorskip("openpyxl")
        import openpyxl
        from core.infrastructure.parsers.code_parser import ExcelParser

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["Name", "Value", "Category"])
        ws.append(["alpha", 1, "A"])
        ws.append(["beta", 2, "B"])
        f = tmp_path / "test.xlsx"
        wb.save(str(f))

        result = ExcelParser().parse(str(f))
        assert result["sheet_count"] == 1
        assert result["sheets"][0]["name"] == "Sheet1"
        assert result["sheets"][0]["headers"] == ["Name", "Value", "Category"]


# ─── ImageParser ─────────────────────────────────────────────────────────────

class TestImageParser:
    def test_parse_nonexistent_image(self):
        from core.infrastructure.parsers.code_parser import ImageParser
        result = ImageParser().parse("/no/such/image.png")
        assert result["path"] == "/no/such/image.png"
        # Should not raise — just return basic info with error key if Pillow errors

    def test_parse_valid_image(self, tmp_path: Path):
        pytest.importorskip("PIL")
        from PIL import Image as PILImage
        from core.infrastructure.parsers.code_parser import ImageParser

        img_path = tmp_path / "test.png"
        img = PILImage.new("RGB", (100, 50), color=(255, 0, 0))
        img.save(str(img_path))

        result = ImageParser().parse(str(img_path))
        assert result["width"] == 100
        assert result["height"] == 50
        assert result["format"] == "PNG"
