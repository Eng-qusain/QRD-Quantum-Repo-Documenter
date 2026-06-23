"""
Temp Manager — handles lifecycle of the application's temporary working directory.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class TempManager:
    """Creates and cleans up the temp directory used for intermediate
    artifacts (generated plots, scratch files) during export jobs."""

    def __init__(self, temp_dir: Path) -> None:
        self.temp_dir = Path(temp_dir)

    async def initialize(self) -> None:
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Temp dir: {self.temp_dir}")

    async def cleanup(self) -> None:
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Temp cleanup error: {e}")
