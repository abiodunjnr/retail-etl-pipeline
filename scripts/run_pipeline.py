
from pathlib import Path
import subprocess
import sys
import logging
import time

# Project configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

PIPELINE_STAGES = [
    "01_extract.py",
    "02_profile.py",
    "02_transform.py",
    "03_load.py",
    "04_gold.py",
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("RetailETL")


def run_stage(script_name):
    """Execute a pipeline stage and stop on failure."""

    script_path = SCRIPTS_DIR / script_name

    if not script_path.is_file():
        raise FileNotFoundError(
            f"Pipeline script not found: {script_path}"
        )

    logger.info("Starting stage: %s", script_name)
    start_time = time.perf_counter()

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=True,
    )

    duration = time.perf_counter() - start_time

    logger.info(
        "Completed %s in %.2f seconds",
        script_name,
        duration,
    )


def main():
    logger.info("Retail ETL pipeline started")

    pipeline_start = time.perf_counter()

    try:
        for stage in PIPELINE_STAGES:
            run_stage(stage)

    except (subprocess.CalledProcessError, OSError) as error:
        logger.exception("Pipeline failed: %s", error)
        sys.exit(1)

    duration = time.perf_counter() - pipeline_start

    logger.info(
        "Retail ETL pipeline completed in %.2f seconds",
        duration,
    )


if __name__ == "__main__":
    main()
