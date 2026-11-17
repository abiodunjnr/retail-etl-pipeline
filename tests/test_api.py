
import sqlite3

import pytest
from fastapi.testclient import TestClient

import api.main as api_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Create an isolated monitoring database for API tests.

    The real development database is never modified.
    """

    test_db = tmp_path / "test_monitoring.db"

    with sqlite3.connect(test_db) as connection:
        connection.executescript(
            """
            CREATE TABLE pipeline_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                duration_seconds REAL,
                error_message TEXT
            );

            CREATE TABLE pipeline_stages (
                stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                duration_seconds REAL,
                error_message TEXT
            );

            CREATE TABLE pipeline_quality_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                dataset_name TEXT NOT NULL,
                source_count INTEGER NOT NULL,
                accepted_count INTEGER NOT NULL,
                rejected_count INTEGER NOT NULL
            );

            INSERT INTO pipeline_runs
                (run_id, started_at, finished_at,
                 status, duration_seconds)
            VALUES
                (1, '2026-11-17T10:00:00',
                 '2026-11-17T10:00:02',
                 'SUCCESS', 2.0),
                (2, '2026-11-17T11:00:00',
                 '2026-11-17T11:00:02',
                 'SUCCESS', 2.0);

            INSERT INTO pipeline_stages
                (run_id, stage_name, started_at,
                 finished_at, status, duration_seconds)
            VALUES
                (1, '01_extract.py',
                 '2026-11-17T10:00:00',
                 '2026-11-17T10:00:01',
                 'SUCCESS', 1.0);

            INSERT INTO pipeline_quality_metrics
                (run_id, dataset_name, source_count,
                 accepted_count, rejected_count)
            VALUES
                (1, 'customers', 500, 500, 0),
                (1, 'products', 150, 148, 2),
                (1, 'sales', 5000, 4839, 161);
            """
        )

    # Redirect the API to our temporary database.
    monkeypatch.setattr(api_module, "DB_PATH", test_db)

    with TestClient(api_module.app) as test_client:
        yield test_client


# ============================================================
# 1. HEALTH CHECK
# ============================================================

def test_health_check(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ============================================================
# 2. PIPELINE EXECUTION HISTORY
# ============================================================

def test_get_pipeline_runs(client):
    response = client.get("/api/v1/pipeline/runs")

    assert response.status_code == 200

    data = response.json()

    assert data["total_returned"] == 2
    assert len(data["runs"]) == 2


# ============================================================
# 3. PIPELINE RUN DETAILS
# ============================================================

def test_get_pipeline_run_details(client):
    response = client.get("/api/v1/pipeline/runs/1")

    assert response.status_code == 200

    data = response.json()

    assert data["run"]["run_id"] == 1
    assert data["run"]["status"] == "SUCCESS"
    assert len(data["stages"]) == 1


def test_pipeline_run_not_found(client):
    response = client.get("/api/v1/pipeline/runs/999")

    assert response.status_code == 404


# ============================================================
# 4. DATA QUALITY API
# ============================================================

def test_get_pipeline_quality(client):
    response = client.get(
        "/api/v1/pipeline/runs/1/quality"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_id"] == 1
    assert data["total_datasets"] == 3
    assert len(data["quality_metrics"]) == 3


def test_quality_record_counts(client):
    response = client.get(
        "/api/v1/pipeline/runs/1/quality"
    )

    metrics = {
        item["dataset_name"]: item
        for item in response.json()["quality_metrics"]
    }

    assert metrics["customers"]["source_count"] == 500
    assert metrics["customers"]["accepted_count"] == 500
    assert metrics["customers"]["rejected_count"] == 0

    assert metrics["products"]["accepted_count"] == 148
    assert metrics["products"]["rejected_count"] == 2

    assert metrics["sales"]["source_count"] == 5000
    assert metrics["sales"]["accepted_count"] == 4839
    assert metrics["sales"]["rejected_count"] == 161


def test_quality_rejection_rates(client):
    response = client.get(
        "/api/v1/pipeline/runs/1/quality"
    )

    metrics = {
        item["dataset_name"]: item
        for item in response.json()["quality_metrics"]
    }

    assert metrics["customers"]["rejection_rate_pct"] == 0
    assert metrics["products"]["rejection_rate_pct"] == 1.33
    assert metrics["sales"]["rejection_rate_pct"] == 3.22


def test_quality_run_not_found(client):
    response = client.get(
        "/api/v1/pipeline/runs/999/quality"
    )

    assert response.status_code == 404


def test_quality_empty_history(client):
    """
    Run 2 exists but has no quality records.
    The API should return an empty collection.
    """

    response = client.get(
        "/api/v1/pipeline/runs/2/quality"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["run_id"] == 2
    assert data["total_datasets"] == 0
    assert data["quality_metrics"] == []
