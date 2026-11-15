
import sqlite3
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "retail_sales.db"


def test_gold_reconciliation():
    """Validate Silver and Gold transaction and revenue totals."""

    if not DATABASE_PATH.is_file():
        pytest.skip(
            "Local SQLite database unavailable; "
            "full pipeline integration test not configured yet."
        )

    with sqlite3.connect(DATABASE_PATH) as connection:
        silver_count, silver_revenue = connection.execute(
            """
            SELECT COUNT(*), ROUND(SUM(line_total_gbp), 2)
            FROM sales_transactions
            """
        ).fetchone()

        gold_count, gold_revenue = connection.execute(
            """
            SELECT
                SUM(total_transactions),
                ROUND(SUM(total_revenue_gbp), 2)
            FROM gold_category_sales
            """
        ).fetchone()

    assert silver_count == gold_count
    assert silver_revenue is not None
    assert gold_revenue is not None
    assert abs(silver_revenue - gold_revenue) <= 0.01

def test_end_to_end_pipeline(tmp_path):
    """Run the ETL pipeline in an isolated test workspace."""

    # Create temporary project directories
    test_root = tmp_path / "retail_etl"
    scripts_dir = test_root / "scripts"
    data_dir = test_root / "data"

    scripts_dir.mkdir(parents=True)
    data_dir.mkdir()

    # Copy actual pipeline scripts
    for script in [
        "run_pipeline.py",
        "01_extract.py",
        "02_profile.py",
        "02_transform.py",
        "03_load.py",
        "04_gold.py",
    ]:
        shutil.copy2(
            PROJECT_ROOT / "scripts" / script,
            scripts_dir / script,
        )

    # Copy controlled input datasets
    for filename in [
        "customers.csv",
        "products.csv",
        "sales_transactions.csv",
    ]:
        shutil.copy2(
            PROJECT_ROOT / "data" / filename,
            data_dir / filename,
        )

 
def execute_pipeline():
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "run_pipeline.py")],
        cwd=test_root,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        "ETL pipeline execution failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


    # First pipeline execution
    execute_pipeline()

    db_path = test_root / "database" / "retail_sales.db"

    assert db_path.is_file(), "Pipeline did not create SQLite database"

    # Check Silver outputs
    for filename in [
        "customers_silver.csv",
        "products_silver.csv",
        "sales_silver.csv",
    ]:
        assert (test_root / "outputs" / "silver" / filename).is_file()

    def get_metrics():
        with sqlite3.connect(db_path) as connection:
            silver_count, silver_revenue = connection.execute(
                """
                SELECT COUNT(*), ROUND(SUM(line_total_gbp), 2)
                FROM sales_transactions
                """
            ).fetchone()

            gold_count, gold_revenue = connection.execute(
                """
                SELECT
                    SUM(total_transactions),
                    ROUND(SUM(total_revenue_gbp), 2)
                FROM gold_category_sales
                """
            ).fetchone()

        return silver_count, silver_revenue, gold_count, gold_revenue

    first_run = get_metrics()

    assert first_run[0] > 0
    assert first_run[0] == first_run[2]
    assert first_run[1] is not None
    assert first_run[3] is not None
    assert abs(first_run[1] - first_run[3]) <= 0.01

    # Second execution: verify idempotency
    execute_pipeline()

    second_run = get_metrics()

    assert first_run == second_run, (
        "Pipeline is not idempotent: results changed after rerun"
    )
