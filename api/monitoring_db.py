
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Resolve the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Monitoring database location
DB_PATH = PROJECT_ROOT / "database" / "pipeline_monitoring.db"


def initialise_monitoring_db():
    # Ensure database directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        # One record for each complete ETL execution
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                duration_seconds REAL,
                error_message TEXT
            )
        """)

        # Individual stages within each execution
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_stages (
                stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                duration_seconds REAL,
                error_message TEXT,

                FOREIGN KEY (run_id)
                    REFERENCES pipeline_runs(run_id)
            )
        """)

        # Data quality measurements per run
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_quality_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                dataset_name TEXT NOT NULL,
                source_count INTEGER NOT NULL,
                accepted_count INTEGER NOT NULL,
                rejected_count INTEGER NOT NULL,

                FOREIGN KEY (run_id)
                    REFERENCES pipeline_runs(run_id)
            )
        """)

        connection.commit()

    print("Monitoring database initialised successfully")



def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def start_pipeline_run():
    initialise_monitoring_db()

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO pipeline_runs (started_at, status)
            VALUES (?, ?)
            """,
            (current_timestamp(), "RUNNING")
        )
        return cursor.lastrowid


def finish_pipeline_run(
    run_id, status, duration_seconds, error_message=None
):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            UPDATE pipeline_runs
            SET finished_at = ?,
                status = ?,
                duration_seconds = ?,
                error_message = ?
            WHERE run_id = ?
            """,
            (
                current_timestamp(),
                status,
                duration_seconds,
                error_message,
                run_id
            )
        )


def start_pipeline_stage(run_id, stage_name):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        cursor = connection.execute(
            """
            INSERT INTO pipeline_stages
                (run_id, stage_name, started_at, status)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, stage_name, current_timestamp(), "RUNNING")
        )
        return cursor.lastrowid


def finish_pipeline_stage(
    stage_id, status, duration_seconds, error_message=None
):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            UPDATE pipeline_stages
            SET finished_at = ?,
                status = ?,
                duration_seconds = ?,
                error_message = ?
            WHERE stage_id = ?
            """,
            (
                current_timestamp(),
                status,
                duration_seconds,
                error_message,
                stage_id
            )
        )

def record_quality_metric(
    run_id,
    dataset_name,
    source_count,
    accepted_count,
    rejected_count,
):
    """Record data quality statistics for one dataset in a pipeline run."""

    if any(
        count < 0
        for count in (source_count, accepted_count, rejected_count)
    ):
        raise ValueError("Record counts cannot be negative")

    if source_count != accepted_count + rejected_count:
        raise ValueError(
            "Source count must equal accepted count plus rejected count"
        )

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            INSERT INTO pipeline_quality_metrics (
                run_id,
                dataset_name,
                source_count,
                accepted_count,
                rejected_count
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                dataset_name,
                source_count,
                accepted_count,
                rejected_count,
            ),
        )

if __name__ == "__main__":
    initialise_monitoring_db()
