"""
Integration Tests — FastAPI Routes

Tests the HTTP API layer end-to-end using httpx AsyncClient.
"""

import pytest
import pytest_asyncio
from pathlib import Path
from httpx import AsyncClient, ASGITransport

from main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    (tmp_path / "main.py").write_text("def main(): pass\n")
    (tmp_path / "utils.py").write_text("import os\n")
    sub = tmp_path / "lib"
    sub.mkdir()
    (sub / "helper.py").write_text("def helper(): return 42\n")
    (tmp_path / "config.yaml").write_text("key: value\n")
    (tmp_path / "data.csv").write_text("name,value\nalpha,1\nbeta,2\n")
    return tmp_path


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data


class TestScannerEndpoints:
    @pytest.mark.asyncio
    async def test_scan_valid_project(self, client: AsyncClient, sample_project: Path):
        response = await client.post("/scanner/scan", json={"path": str(sample_project)})
        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == sample_project.name
        assert len(data["flat_files"]) >= 5
        assert "stats" in data
        assert data["stats"]["total_files"] >= 5

    @pytest.mark.asyncio
    async def test_scan_nonexistent_path(self, client: AsyncClient):
        response = await client.post("/scanner/scan", json={"path": "/definitely/not/real"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_scan_with_exclude_patterns(self, client: AsyncClient, sample_project: Path):
        response = await client.post("/scanner/scan", json={
            "path": str(sample_project),
            "exclude_patterns": ["*.yaml", "*.csv"],
        })
        assert response.status_code == 200
        files = response.json()["flat_files"]
        assert not any(f["extension"] in (".yaml", ".csv") for f in files)

    @pytest.mark.asyncio
    async def test_scan_returns_file_tree(self, client: AsyncClient, sample_project: Path):
        response = await client.post("/scanner/scan", json={"path": str(sample_project)})
        tree = response.json()["file_tree"]
        assert tree["type"] == "directory"
        assert "children" in tree

    @pytest.mark.asyncio
    async def test_scan_stats_have_language_distribution(self, client: AsyncClient, sample_project: Path):
        response = await client.post("/scanner/scan", json={"path": str(sample_project)})
        stats = response.json()["stats"]
        assert "Python" in stats["language_distribution"]

    @pytest.mark.asyncio
    async def test_get_file_content(self, client: AsyncClient, sample_project: Path):
        file_path = str(sample_project / "main.py")
        response = await client.get("/scanner/file-content", params={"path": file_path})
        assert response.status_code == 200
        data = response.json()
        assert "def main" in data["content"]
        assert data["line_count"] >= 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_file_content(self, client: AsyncClient):
        response = await client.get("/scanner/file-content", params={"path": "/no/such/file.py"})
        assert response.status_code == 404


class TestExportEndpoints:
    @pytest.mark.asyncio
    async def test_start_export_single(self, client: AsyncClient, sample_project: Path, tmp_path: Path):
        output = str(tmp_path / "out.pdf")
        response = await client.post("/export/start", json={
            "project_path": str(sample_project),
            "options": {
                "mode": "single",
                "output_path": output,
                "include_ai": False,
                "include_charts": False,
                "include_toc": True,
                "include_stats": True,
                "include_dependencies": False,
                "include_architecture": False,
                "syntax_highlighting": True,
                "line_numbers": True,
                "max_csv_rows": 10,
                "paper_size": "A4",
                "orientation": "portrait",
                "theme": "default",
                "font_size": 9,
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @pytest.mark.asyncio
    async def test_invalid_export_mode(self, client: AsyncClient, sample_project: Path, tmp_path: Path):
        response = await client.post("/export/start", json={
            "project_path": str(sample_project),
            "options": {
                "mode": "invalid_mode",
                "output_path": str(tmp_path / "x.pdf"),
                "include_ai": False,
                "include_charts": False,
                "include_toc": False,
                "include_stats": False,
                "include_dependencies": False,
                "include_architecture": False,
                "syntax_highlighting": False,
                "line_numbers": False,
                "max_csv_rows": 10,
                "paper_size": "A4",
                "orientation": "portrait",
                "theme": "default",
                "font_size": 9,
            },
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, client: AsyncClient):
        response = await client.get("/export/fake-job-id/status")
        assert response.status_code == 404


class TestSearchEndpoints:
    @pytest.mark.asyncio
    async def test_search_by_filename(self, client: AsyncClient, sample_project: Path):
        response = await client.get("/search/", params={
            "project_path": str(sample_project),
            "query": "main",
            "search_type": "filename",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any("main" in r["relative_path"] for r in data["results"])

    @pytest.mark.asyncio
    async def test_search_by_extension(self, client: AsyncClient, sample_project: Path):
        response = await client.get("/search/", params={
            "project_path": str(sample_project),
            "query": ".py",
            "search_type": "extension",
        })
        assert response.status_code == 200
        data = response.json()
        assert all(r["relative_path"].endswith(".py") for r in data["results"])

    @pytest.mark.asyncio
    async def test_search_by_content(self, client: AsyncClient, sample_project: Path):
        response = await client.get("/search/", params={
            "project_path": str(sample_project),
            "query": "def main",
            "search_type": "content",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
