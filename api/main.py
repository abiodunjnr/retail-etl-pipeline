
from fastapi import FastAPI
import sqlite3
from fastapi import HTTPException
from api.monitoring_db import DB_PATH

# Initialise the API application
app = FastAPI(
    title="Retail ETL Platform API",
    version="1.0.0",
    description="Backend API for retail analytics and ETL monitoring"
)

# Define a health-check endpoint
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "service": "Retail ETL Platform API"
    }


# Retrieve historical ETL executions
@app.get("/api/v1/pipeline/runs", tags=["Pipeline Monitoring"])
def get_pipeline_runs(limit: int = 50):
    # Restrict the number of records returned
    if not 1 <= limit <= 200:
        raise HTTPException(
            status_code=422,
            detail="Limit must be between 1 and 200"
        )

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        records = connection.execute(
            """
            SELECT
                run_id,
                started_at,
                finished_at,
                status,
                duration_seconds,
                error_message
            FROM pipeline_runs
            ORDER BY run_id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return {
        "total_returned": len(records),
        "runs": [dict(record) for record in records]
    }


# Retrieve one execution and all its stages
@app.get(
    "/api/v1/pipeline/runs/{run_id}",
    tags=["Pipeline Monitoring"]
)
def get_pipeline_run_details(run_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        run = connection.execute(
            """
            SELECT *
            FROM pipeline_runs
            WHERE run_id = ?
            """,
            (run_id,)
        ).fetchone()

        if run is None:
            raise HTTPException(
                status_code=404,
                detail="Pipeline run not found"
            )

        stages = connection.execute(
            """
            SELECT
                stage_id,
                stage_name,
                started_at,
                finished_at,
                status,
                duration_seconds,
                error_message
            FROM pipeline_stages
            WHERE run_id = ?
            ORDER BY stage_id
            """,
            (run_id,)
        ).fetchall()

    return {
        "run": dict(run),
        "stages": [dict(stage) for stage in stages]
    }


@app.get("/api/v1/pipeline/runs/{run_id}/quality")
def get_pipeline_quality(run_id: int):
    """Return data quality metrics for a pipeline execution."""

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        # Confirm the requested pipeline run exists
        run = connection.execute(
            "SELECT run_id FROM pipeline_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()

        if run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline run {run_id} not found",
            )

        # Retrieve quality metrics
        records = connection.execute(
            """
            SELECT
                dataset_name,
                source_count,
                accepted_count,
                rejected_count
            FROM pipeline_quality_metrics
            WHERE run_id = ?
            ORDER BY dataset_name
            """,
            (run_id,),
        ).fetchall()

    quality_metrics = []

    for record in records:
        source_count = record["source_count"]
        rejected_count = record["rejected_count"]

        rejection_rate = (
            round((rejected_count / source_count) * 100, 2)
            if source_count > 0
            else 0.0
        )

        quality_metrics.append({
            "dataset_name": record["dataset_name"],
            "source_count": source_count,
            "accepted_count": record["accepted_count"],
            "rejected_count": rejected_count,
            "rejection_rate_pct": rejection_rate,
        })

    return {
        "run_id": run_id,
        "total_datasets": len(quality_metrics),
        "quality_metrics": quality_metrics,
    }

