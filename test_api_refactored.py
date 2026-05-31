import pytest
from fastapi.testclient import TestClient
from api_refactored import app, _pipeline_statuses, PipelineRunRequest, PipelineRunResponse, PipelineStatusResponse
import uuid

client = TestClient(app)

# Clear pipeline statuses before each test
@pytest.fixture(autouse=True)
def clear_pipeline_statuses():
    _pipeline_statuses.clear()
    yield

# --- Health Check Tests ---

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "API is running"}

# --- Start Pipeline Run Tests ---

def test_start_pipeline_run_unauthenticated():
    response = client.post("/pipeline/run", json={"material_id": "test-material-1"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_start_pipeline_run_authenticated_success():
    response = client.post(
        "/pipeline/run",
        json={"material_id": "test-material-2", "config": {"param": "value"}},
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 202
    response_data = PipelineRunResponse(**response.json())
    assert isinstance(response_data.pipeline_id, uuid.UUID)
    assert response_data.status == "initiated"
    assert response_data.message == "Pipeline run initiated successfully"
    assert response_data.pipeline_id in _pipeline_statuses
    assert _pipeline_statuses[response_data.pipeline_id]["status"] == "pending"

def test_start_pipeline_run_invalid_input():
    response = client.post(
        "/pipeline/run",
        json={},
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
    assert "material_id" in response.json()["detail"][0]["loc"]

# --- Get Pipeline Status Tests ---

def test_get_pipeline_status_unauthenticated():
    pipeline_id = uuid.uuid4()
    response = client.get(f"/pipeline/{pipeline_id}/status")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_get_pipeline_status_authenticated_not_found():
    pipeline_id = uuid.uuid4()
    response = client.get(
        f"/pipeline/{pipeline_id}/status",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Pipeline run not found"}

def test_get_pipeline_status_authenticated_success():
    # First, start a pipeline to get a valid ID
    run_response = client.post(
        "/pipeline/run",
        json={"material_id": "test-material-3"},
        headers={"Authorization": "Bearer valid-token"}
    )
    assert run_response.status_code == 202
    pipeline_id = run_response.json()["pipeline_id"]

    # Then, get its status
    status_response = client.get(
        f"/pipeline/{pipeline_id}/status",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert status_response.status_code == 200
    response_data = PipelineStatusResponse(**status_response.json())
    assert response_data.pipeline_id == uuid.UUID(pipeline_id)
    assert response_data.status == "pending" # Should be pending immediately after initiation
    assert response_data.progress == 0.0

# --- Get Pipeline Report Tests ---

def test_get_pipeline_report_unauthenticated():
    pipeline_id = uuid.uuid4()
    response = client.get(f"/pipeline/{pipeline_id}/report")
    assert response.status_code == 401

def test_get_pipeline_report_not_found():
    pipeline_id = uuid.uuid4()
    response = client.get(
        f"/pipeline/{pipeline_id}/report",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 404

def test_get_pipeline_report_not_completed():
    run_response = client.post(
        "/pipeline/run",
        json={"material_id": "test-material-4"},
        headers={"Authorization": "Bearer valid-token"}
    )
    pipeline_id = run_response.json()["pipeline_id"]

    response = client.get(
        f"/pipeline/{pipeline_id}/report",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 409 # Conflict, not completed yet
    assert response.json() == {"detail": "Pipeline run not yet completed"}

# Note: Testing a completed report would require mocking the background task's completion
# or waiting for it, which is more complex for simple unit tests.

# --- Get Pipeline Visualization Tests ---

def test_get_pipeline_visualization_unauthenticated():
    pipeline_id = uuid.uuid4()
    response = client.get(f"/pipeline/{pipeline_id}/visualization")
    assert response.status_code == 401

def test_get_pipeline_visualization_not_found():
    pipeline_id = uuid.uuid4()
    response = client.get(
        f"/pipeline/{pipeline_id}/visualization",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 404
