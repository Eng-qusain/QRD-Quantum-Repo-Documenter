"""
Petroleum Data Parser

Supports LAS, DLIS, LIS well log files and production CSV data.
Generates quick-look plots using matplotlib.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LASParser:
    """Parse LAS (Log ASCII Standard) well log files."""

    def parse(self, file_path: str) -> dict:
        try:
            import lasio
            las = lasio.read(file_path)

            curves = []
            for curve in las.curves:
                curves.append({
                    "mnemonic": curve.mnemonic,
                    "unit": curve.unit,
                    "description": curve.descr,
                    "data_type": str(las[curve.mnemonic].dtype),
                    "count": len(las[curve.mnemonic]),
                    "min": float(las[curve.mnemonic].min()),
                    "max": float(las[curve.mnemonic].max()),
                })

            well_info = {}
            for section in ["well", "params", "other"]:
                section_data = getattr(las, section, {})
                for key, item in section_data.items():
                    well_info[key] = {
                        "value": str(item.value),
                        "unit": str(item.unit),
                        "description": str(item.descr),
                    }

            depth_range = None
            if "DEPT" in las.keys() or "DEPTH" in las.keys():
                dept_key = "DEPT" if "DEPT" in las.keys() else "DEPTH"
                depth_range = (float(las[dept_key].min()), float(las[dept_key].max()))

            return {
                "well_name": las.well.WELL.value if hasattr(las.well, "WELL") else Path(file_path).stem,
                "curves": curves,
                "curve_count": len(curves),
                "sample_count": len(las.index),
                "depth_range": depth_range,
                "well_info": well_info,
                "file_format": "LAS",
                "version": str(las.version.get("VERS", {}).value if las.version else ""),
            }

        except ImportError:
            return {"error": "lasio not installed. Run: pip install lasio", "curves": []}
        except Exception as e:
            logger.error(f"LAS parse error {file_path}: {e}")
            return {"error": str(e), "curves": []}

    def generate_quicklook_plot(self, file_path: str, output_path: str) -> Optional[str]:
        """Generate a quick-look wireline plot as PNG."""
        try:
            import lasio
            import matplotlib.pyplot as plt
            import matplotlib.gridspec as gridspec
            import numpy as np

            las = lasio.read(file_path)
            depth_key = "DEPT" if "DEPT" in las.keys() else (
                "DEPTH" if "DEPTH" in las.keys() else None
            )

            if not depth_key:
                return None

            depth = las[depth_key]
            curves = [k for k in las.keys() if k not in (depth_key, "DEPT", "DEPTH")][:6]

            if not curves:
                return None

            n_tracks = len(curves)
            fig = plt.figure(figsize=(3 * n_tracks, 12), facecolor="#1a1a2e")
            gs = gridspec.GridSpec(1, n_tracks, figure=fig, wspace=0.05)

            COLORS = ["#00ff88", "#ff6b6b", "#ffd93d", "#6bcfff", "#ff9f43", "#a29bfe"]

            for i, curve_name in enumerate(curves):
                ax = fig.add_subplot(gs[0, i])
                ax.set_facecolor("#0d1117")

                curve_data = las[curve_name]
                valid_mask = ~np.isnan(curve_data)

                if valid_mask.any():
                    ax.plot(
                        curve_data[valid_mask],
                        depth[valid_mask],
                        color=COLORS[i % len(COLORS)],
                        linewidth=0.8,
                        alpha=0.9,
                    )

                ax.set_xlabel(f"{curve_name}", color="white", fontsize=8, fontweight="bold")
                ax.set_ylim(depth.max(), depth.min())
                ax.tick_params(colors="white", labelsize=6)
                ax.spines[["top", "right", "bottom", "left"]].set_color("#30363d")
                ax.xaxis.set_label_position("top")
                ax.xaxis.tick_top()

                if i == 0:
                    ax.set_ylabel("Depth (m)", color="white", fontsize=8)
                else:
                    ax.set_yticklabels([])

            fig.suptitle(
                f"Quick-Look: {Path(file_path).stem}",
                color="white",
                fontsize=11,
                fontweight="bold",
            )
            plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
            plt.close(fig)
            return output_path

        except Exception as e:
            logger.error(f"Quick-look plot error: {e}")
            return None


class ProductionCSVParser:
    """Parse oil/gas production CSV files and generate rate plots."""

    RATE_COLUMNS = {
        "oil": ["oil", "oil_rate", "qo", "oil_prod", "bopd", "stb/day"],
        "gas": ["gas", "gas_rate", "qg", "gas_prod", "mcfd", "mmscfd"],
        "water": ["water", "water_rate", "qw", "water_prod", "wcut", "bwpd"],
        "date": ["date", "time", "period", "month", "year", "timestamp"],
    }

    def parse(self, file_path: str, max_rows: int = 500) -> dict:
        try:
            import pandas as pd

            df = pd.read_csv(file_path, on_bad_lines="skip")
            df.columns = [c.lower().strip() for c in df.columns]

            identified = {}
            for col_type, patterns in self.RATE_COLUMNS.items():
                for col in df.columns:
                    if any(p in col for p in patterns):
                        identified[col_type] = col
                        break

            return {
                "headers": list(df.columns),
                "identified_columns": identified,
                "row_count": len(df),
                "date_range": self._get_date_range(df, identified.get("date")),
                "is_production_data": len(identified) >= 2,
            }
        except Exception as e:
            return {"error": str(e)}

    def generate_rate_plot(self, file_path: str, output_path: str) -> Optional[str]:
        """Generate oil/gas/water rate plot."""
        try:
            import pandas as pd
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates

            df = pd.read_csv(file_path, on_bad_lines="skip")
            df.columns = [c.lower().strip() for c in df.columns]

            # Identify columns
            date_col = next(
                (c for c in df.columns if any(k in c for k in ["date", "time", "month"])),
                None,
            )
            oil_col = next(
                (c for c in df.columns if any(k in c for k in ["oil", "qo", "bopd"])),
                None,
            )
            gas_col = next(
                (c for c in df.columns if any(k in c for k in ["gas", "qg", "mcfd"])),
                None,
            )
            water_col = next(
                (c for c in df.columns if any(k in c for k in ["water", "qw", "bwpd"])),
                None,
            )

            if not date_col:
                return None

            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col]).sort_values(date_col)

            fig, axes = plt.subplots(
                sum(1 for c in [oil_col, gas_col, water_col] if c),
                1,
                figsize=(12, 8),
                facecolor="#0d1117",
                sharex=True,
            )
            if not hasattr(axes, "__iter__"):
                axes = [axes]

            ax_idx = 0
            rate_configs = [
                (oil_col, "Oil Rate", "#00ff88", "STB/day"),
                (gas_col, "Gas Rate", "#ffd93d", "Mscf/day"),
                (water_col, "Water Rate", "#6bcfff", "STB/day"),
            ]

            for col, label, color, unit in rate_configs:
                if col and ax_idx < len(axes):
                    ax = axes[ax_idx]
                    ax.set_facecolor("#1a1a2e")
                    numeric_data = pd.to_numeric(df[col], errors="coerce")
                    ax.fill_between(df[date_col], numeric_data, alpha=0.3, color=color)
                    ax.plot(df[date_col], numeric_data, color=color, linewidth=1.2)
                    ax.set_ylabel(f"{label}\n({unit})", color="white", fontsize=9)
                    ax.tick_params(colors="white")
                    ax.spines[["top", "right"]].set_visible(False)
                    ax.spines[["bottom", "left"]].set_color("#30363d")
                    ax.grid(True, alpha=0.15, color="#30363d")
                    ax_idx += 1

            if axes:
                axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
                axes[-1].tick_params(axis="x", rotation=45, colors="white")

            fig.suptitle(
                f"Production Data: {Path(file_path).stem}",
                color="white",
                fontsize=12,
                fontweight="bold",
            )
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="#0d1117")
            plt.close(fig)
            return output_path

        except Exception as e:
            logger.error(f"Rate plot error: {e}")
            return None

    @staticmethod
    def _get_date_range(df, date_col: Optional[str]) -> Optional[dict]:
        if not date_col:
            return None
        try:
            import pandas as pd
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if len(dates) == 0:
                return None
            return {"start": str(dates.min().date()), "end": str(dates.max().date())}
        except Exception:
            return None


# ─── Search Routes ────────────────────────────────────────────────────────────

from fastapi import APIRouter as _APIRouter

search_router = _APIRouter()


@search_router.get("/")
async def search_files(
    project_path: str,
    query: str,
    search_type: str = "filename",
    max_results: int = 100,
) -> dict:
    """Search files by name, extension, or content."""
    from pathlib import Path
    import fnmatch
    import os

    root = Path(project_path)
    if not root.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project path not found")

    results = []
    query_lower = query.lower()

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip common excludes
        dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "__pycache__", ".venv")]

        for fname in filenames:
            if len(results) >= max_results:
                break

            full_path = Path(dirpath) / fname
            rel_path = str(full_path.relative_to(root))

            if search_type == "filename" and query_lower in fname.lower():
                results.append({"file_path": str(full_path), "relative_path": rel_path, "match_type": "filename"})
            elif search_type == "extension" and fname.lower().endswith(query_lower.lstrip("*")):
                results.append({"file_path": str(full_path), "relative_path": rel_path, "match_type": "extension"})
            elif search_type == "content":
                try:
                    content = full_path.read_text(errors="replace")
                    if query_lower in content.lower():
                        # Find first matching line
                        for i, line in enumerate(content.split("\n"), 1):
                            if query_lower in line.lower():
                                results.append({
                                    "file_path": str(full_path),
                                    "relative_path": rel_path,
                                    "match_type": "content",
                                    "line_number": i,
                                    "snippet": line.strip()[:120],
                                })
                                break
                except (OSError, UnicodeDecodeError):
                    pass

    return {"results": results, "count": len(results), "query": query}
