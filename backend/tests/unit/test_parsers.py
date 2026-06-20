"""
Unit Tests — File Parsers (CSV, Excel, Code)
"""

import csv
import tempfile
from pathlib import Path
import pytest

from core.infrastructure.parsers.code_parser import CSVParser, ExcelParser, CodeParser


class TestCSVParser:
    @pytest.fixture
    def parser(self):
        return CSVParser()

    @pytest.fixture
    def sample_csv(self, tmp_path: Path) -> str:
        f = tmp_path / "data.csv"
        rows = [["id", "name", "value", "category"]]
        rows += [[str(i), f"item_{i}", str(i * 10), "A" if i % 2 == 0 else "B"] for i in range(150)]
        with open(f, "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerows(rows)
        return str(f)

    def test_parse_returns_headers(self, parser, sample_csv):
        result = parser.parse(sample_csv)
        assert result["headers"] == ["id", "name", "value", "category"]

    def test_parse_limits_rows(self, parser, sample_csv):
        result = parser.parse(sample_csv, max_rows=50)
        assert len(result["rows"]) <= 50

    def test_parse_stats_row_count(self, parser, sample_csv):
        result = parser.parse(sample_csv)
        assert result["stats"]["row_count"] >= 149

    def test_parse_stats_column_count(self, parser, sample_csv):
        result = parser.parse(sample_csv)
        assert result["stats"]["column_count"] == 4

    def test_parse_empty_csv(self, tmp_path: Path, parser):
        f = tmp_path / "empty.csv"
        f.write_text("col1,col2\n")
        result = parser.parse(str(f))
        assert result["headers"] == ["col1", "col2"]
        assert result["rows"] == []

    def test_parse_invalid_file(self, parser):
        result = parser.parse("/nonexistent/file.csv")
        assert "error" in result


class TestCodeParser:
    @pytest.fixture
    def parser(self):
        return CodeParser()

    def test_parse_python_functions(self, parser):
        code = """
def greet(name: str) -> str:
    return f"Hello, {name}"

async def fetch_data(url: str, timeout: int = 30) -> dict:
    pass
"""
        result = parser.parse("test.py", code, "python")
        names = [f["name"] for f in result["functions"]]
        assert "greet" in names
        assert "fetch_data" in names

    def test_parse_python_classes(self, parser):
        code = """
class UserService:
    def __init__(self):
        pass

    def get_user(self, user_id: int):
        pass

    def create_user(self, data: dict):
        pass
"""
        result = parser.parse("service.py", code, "python")
        assert len(result["classes"]) == 1
        assert result["classes"][0]["name"] == "UserService"
        assert "get_user" in result["classes"][0]["methods"]

    def test_parse_python_imports(self, parser):
        code = """
import os
import sys
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
"""
        result = parser.parse("imports.py", code, "python")
        assert "os" in result["imports"]
        assert "sys" in result["imports"]
        assert "pathlib" in result["imports"]
        assert "fastapi" in result["imports"]

    def test_parse_python_complexity(self, parser):
        code = """
def complex_function(x, y, z):
    if x > 0:
        for i in range(x):
            while y > 0:
                try:
                    if z:
                        pass
                except ValueError:
                    pass
                y -= 1
    return x + y + z
"""
        result = parser.parse("complex.py", code, "python")
        assert result["complexity_score"] > 3

    def test_parse_typescript_functions(self, parser):
        code = """
function greet(name: string): string {
  return `Hello, ${name}`;
}

const fetchUser = async (id: number) => {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
};

export const processData = (data: unknown[]) => data.filter(Boolean);
"""
        result = parser.parse("utils.ts", code, "typescript")
        names = [f["name"] for f in result["functions"]]
        assert "greet" in names

    def test_parse_typescript_imports(self, parser):
        code = """
import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';
import type { User } from './types';
"""
        result = parser.parse("Component.tsx", code, "react (tsx)")
        assert "react" in result["imports"]
        assert "axios" in result["imports"]

    def test_parse_python_syntax_error(self, parser):
        """Gracefully handles broken Python code."""
        code = "def broken_func(\n    x: int\n    # missing closing paren"
        result = parser.parse("broken.py", code, "python")
        assert "line_count" in result
        assert isinstance(result.get("functions", []), list)

    def test_line_count_accuracy(self, parser):
        code = "line1\nline2\nline3\nline4\nline5"
        result = parser.parse("f.py", code, "python")
        assert result["line_count"] == 5
