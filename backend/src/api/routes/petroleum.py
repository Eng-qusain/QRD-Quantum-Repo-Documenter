"""Petroleum Data Route"""
import tempfile

from fastapi import APIRouter, HTTPException

from core.infrastructure.petroleum.petroleum_parser import LASParser, ProductionCSVParser

router = APIRouter()
_las_parser = LASParser()
_prod_parser = ProductionCSVParser()


@router.get("/las/parse")
async def parse_las(file_path: str) -> dict:
    result = _las_parser.parse(file_path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/las/quicklook")
async def las_quicklook(file_path: str) -> dict:
    """Generate and return path to quick-look PNG."""
    out = tempfile.mktemp(suffix=".png")
    result = _las_parser.generate_quicklook_plot(file_path, out)
    if not result:
        raise HTTPException(status_code=500, detail="Could not generate plot")
    return {"plot_path": result}


@router.get("/production/parse")
async def parse_production(file_path: str) -> dict:
    return _prod_parser.parse(file_path)


@router.get("/production/plot")
async def production_plot(file_path: str) -> dict:
    out = tempfile.mktemp(suffix=".png")
    result = _prod_parser.generate_rate_plot(file_path, out)
    if not result:
        raise HTTPException(status_code=500, detail="Could not generate rate plot")
    return {"plot_path": result}
