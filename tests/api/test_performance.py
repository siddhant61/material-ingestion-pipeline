import pytest
from fastapi.testclient import TestClient
from src.api.api import app, _pipeline_statuses, run_pipeline_in_background
import uuid
import asyncio

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_pipeline_statuses_for_perf():
    _pipeline_statuses.clear()
    yield

# Benchmark for the health check endpoint
def test_benchmark_health_check(benchmark):
    response = benchmark(client.get, "/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# Benchmark for initiating a pipeline run
def test_benchmark_start_pipeline_run(benchmark):
    material_id = f"perf-material-{uuid.uuid4()}"
    config = {"param": "value"}
    headers = {"Authorization": "Bearer valid-token"}

    def run_start_pipeline_request():
        return client.post(
            "/pipeline/run",
            json={"material_id": material_id, "config": config},
            headers=headers
        )

    response = benchmark(run_start_pipeline_request)
    assert response.status_code == 202
    assert "pipeline_id" in response.json()

# Benchmark for getting pipeline status (after it's initiated)
def test_benchmark_get_pipeline_status(benchmark):
    # Setup: Initiate a pipeline once
    material_id = f"perf-material-status-{uuid.uuid4()}"
    response = client.post(
        "/pipeline/run",
        json={"material_id": material_id},
        headers={"Authorization": "Bearer valid-token"}
    )
    pipeline_id = response.json()["pipeline_id"]

    def run_get_status_request():
        return client.get(
            f"/pipeline/{pipeline_id}/status",
            headers={"Authorization": "Bearer valid-token"}
        )

    response = benchmark(run_get_status_request)
    assert response.status_code == 200
    assert response.json()["pipeline_id"] == pipeline_id
    assert response.json()["status"] == "pending"

# Benchmark for getting pipeline report (after it's completed)
# This test will be slower as it involves running the background task
@pytest.mark.asyncio
async def test_benchmark_get_pipeline_report_completed(benchmark):
    # Setup: Initiate and complete a pipeline once
    material_id = f"perf-material-report-{uuid.uuid4()}"
    config = {"test": "data"}
    response = client.post(
        "/pipeline/run",
        json={"material_id": material_id, "config": config},
        headers={"Authorization": "Bearer valid-token"}
    )
    pipeline_id = uuid.UUID(response.json()["pipeline_id"])

    # Manually run the background task to completion
    await run_pipeline_in_background(pipeline_id, material_id, config)

    def run_get_report_request():
        return client.get(
            f"/pipeline/{pipeline_id}/report",
            headers={"Authorization": "Bearer valid-token"}
        )

    response = benchmark(run_get_report_request)
    assert response.status_code == 200
    assert response.json()["pipeline_id"] == str(pipeline_id)
    assert "report_data" in response.json()
