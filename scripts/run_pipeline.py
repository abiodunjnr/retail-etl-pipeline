
from pathlib import Path
import subprocess
import sys
import logging
import time
import pandas as pd

# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Allow execution as both a script and a Python module
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.monitoring_db import (
    start_pipeline_run,
    finish_pipeline_run,
    start_pipeline_stage,
    finish_pipeline_stage,
    record_quality_metric,
)

# Pipeline execution order
PIPELINE_STAGES = [
    "01_extract.py",
    "02_profile.py",
    "02_transform.py",
    "03_load.py",
    "04_gold.py",
]

# ============================================================
# 2. LOGGING CONFIGURATION
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("RetailETL")


# ============================================================
# 3. EXECUTE INDIVIDUAL PIPELINE STAGES
# ============================================================

def run_stage(script_name, run_id):
    """Execute one ETL stage and record its execution status."""

    script_path = SCRIPTS_DIR / script_name

    stage_id = start_pipeline_stage(run_id, script_name)

    logger.info("Starting stage: %s", script_name)

    start_time = time.perf_counter()

    try:
        if not script_path.is_file():
            raise FileNotFoundError(
                f"Pipeline script not found: {script_path}"
            )

        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            check=True,
        )

    except Exception as error:
        duration = time.perf_counter() - start_time

        finish_pipeline_stage(
            stage_id,
            status="FAILED",
            duration_seconds=duration,
            error_message=str(error),
        )

        logger.exception(
            "Stage failed: %s", script_name
        )

        raise

    duration = time.perf_counter() - start_time

    finish_pipeline_stage(
        stage_id,
        status="SUCCESS",
        duration_seconds=duration,
    )

    logger.info(
        "Completed %s in %.2f seconds",
        script_name,
        duration,
    )


# ============================================================
# 4. COLLECT AND RECORD DATA QUALITY METRICS
# ============================================================

def collect_quality_metrics(run_id):
    """
    Calculate source, accepted and rejected record counts.

    Store the measurements in SQLite against the current
    pipeline execution ID.
    """

    datasets = ("customers", "products", "sales")

    for dataset_name in datasets:

        # Identify source file
        if dataset_name == "sales":
            source_filename = "sales_transactions.csv"
        else:
            source_filename = f"{dataset_name}.csv"

        source_file = (
            PROJECT_ROOT / "data" / source_filename
        )

        silver_file = (
            PROJECT_ROOT
            / "outputs"
            / "silver"
            / f"{dataset_name}_silver.csv"
        )

        quarantine_file = (
            PROJECT_ROOT
            / "outputs"
            / "quarantine"
            / f"{dataset_name}_quarantine.csv"
        )

        # Count records without loading entire datasets
        # into memory.
        def count_csv_records(file_path):
            with file_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as file:
                import csv

                reader = csv.reader(file)
                next(reader)  # Skip CSV header
                return sum(1 for row in reader if row)

        source_count = count_csv_records(source_file)
        accepted_count = count_csv_records(silver_file)
        rejected_count = count_csv_records(quarantine_file)

        # Persist quality measurements in SQLite.
        # The database function validates reconciliation.
        record_quality_metric(
            run_id=run_id,
            dataset_name=dataset_name,
            source_count=source_count,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
        )

        logger.info(
            "Quality metrics recorded: %s | "
            "Source: %s | Accepted: %s | Rejected: %s",
            dataset_name,
            source_count,
            accepted_count,
            rejected_count,
        )


# ============================================================
# 5. MAIN PIPELINE ORCHESTRATOR
# ============================================================

def main():
    """Coordinate ETL execution and historical monitoring."""

    logger.info("Retail ETL pipeline started")

    pipeline_start = time.perf_counter()

    # Create a historical execution record
    run_id = start_pipeline_run()

    logger.info("Pipeline run ID: %s", run_id)

    try:
        # Execute ETL stages sequentially
        for stage in PIPELINE_STAGES:
            run_stage(stage, run_id)

        # Collect quality metrics once all stages succeed
        collect_quality_metrics(run_id)

    except Exception as error:
        duration = time.perf_counter() - pipeline_start

        # Record failed execution
        finish_pipeline_run(
            run_id,
            status="FAILED",
            duration_seconds=duration,
            error_message=str(error),
        )

        logger.exception(
            "Pipeline failed: %s", error
        )

        sys.exit(1)

    # Calculate total pipeline duration
    duration = time.perf_counter() - pipeline_start

    # Record successful execution
    finish_pipeline_run(
        run_id,
        status="SUCCESS",
        duration_seconds=duration,
    )

    logger.info(
        "Retail ETL pipeline completed in %.2f seconds",
        duration,
    )


# ============================================================
# 6. APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
