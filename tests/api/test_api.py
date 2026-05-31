import pytest
from fastapi.testclient import TestClient
from src.api.api import app, _pipeline_statuses, run_pipeline_in_background
from src.api.models import PipelineRunRequest, PipelineRunResponse, PipelineStatusResponse, PipelineReportResponse
import uuid
import asyncio
from datetime import datetime, timezone

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
    assert response.json()["status"] == "ok"
    assert response.json()["message"] == "API is running"
    assert "timestamp" in response.json()
    assert "dependencies" in response.json()

# --- Start Pipeline Run Tests ---

def test_start_pipeline_run_unauthenticated():
    response = client.post("/pipeline/run", json={"material_id": "test-material-1"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.parametrize("auth_header", [
    "Bearer ", # Empty token
    "Bearer invalid-token", # Invalid token
    "InvalidScheme valid-token", # Invalid scheme
    "just-a-token", # Missing Bearer
    "", # Missing header entirely (already covered by unauthenticated test)
])
def test_start_pipeline_run_invalid_authentication(auth_header):
    headers = {"Authorization": auth_header} if auth_header else {}
    response = client.post(
        "/pipeline/run",
        json={"material_id": "test-material-invalid-auth"},
        headers=headers
    )
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

def test_start_pipeline_run_authenticated_success_empty_config():
    response = client.post(
        "/pipeline/run",
        json={"material_id": "test-material-empty-config", "config": {}},
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 202
    response_data = PipelineRunResponse(**response.json())
    assert isinstance(response_data.pipeline_id, uuid.UUID)
    assert response_data.pipeline_id in _pipeline_statuses
    assert _pipeline_statuses[response_data.pipeline_id]["config"] == {}

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

def test_get_pipeline_status_not_found():
    pipeline_id = uuid.uuid4()
    response = client.get(
        f"/pipeline/{pipeline_id}/status",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": f"Pipeline with ID {pipeline_id} not found."}

def test_get_pipeline_status_invalid_uuid():
    response = client.get(
        f"/pipeline/not-a-uuid/status",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
    assert "value is not a valid uuid" in response.json()["detail"][0]["msg"]

def test_get_pipeline_status_authenticated_pending():
    pipeline_id = uuid.uuid4()
    _pipeline_statuses[pipeline_id] = {
        "material_id": "test-material-pending",
        "config": {},
        "status": "pending",
        "progress": 0.0,
        "start_time": datetime.now(timezone.utc).isoformat()
    }
    response = client.get(
        f"/pipeline/{pipeline_id}/status",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 200
    response_data = PipelineStatusResponse(**response.json())
    assert response_data.pipeline_id == pipeline_id
    assert response_data.status == "pending"
    assert response_data.progress == 0.0
    assert response_data.report_url is None

def test_get_pipeline_status_authenticated_running_and_completed():
    pipeline_id = uuid.uuid4()
    material_id = "test-material-running-completed"
    config = {"test": "data"}

    # Simulate pipeline initiation
    response = client.post(
        "/pipeline/run",
        json={"material_id": material_id, "config": config},
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 202
    pipeline_id = PipelineRunResponse(**response.json()).pipeline_id

    # Manually run the background task to completion
    asyncio.run(run_pipeline_in_background(pipeline_id, material_id, config))

    # Check status after completion
    response = client.get(
        f"/pipeline/{pipeline_id}/status",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 200
    response_data = PipelineStatusResponse(**response.json())
    assert response_data.pipeline_id == pipeline_id
    assert response_data.status == "completed"
    assert response_data.progress == 100.0
    assert response_data.report_url == f"/pipeline/{pipeline_id}/report"

def test_get_pipeline_status_authenticated_failed():
    pipeline_id = uuid.uuid4()
    _pipeline_statuses[pipeline_id] = {
        "material_id": "test-material-failed",
        "config": {},
        "status": "failed",
        "progress": 50.0,
        "error_details": "Simulated error during processing.",
        "start_time": datetime.now(timezone.utc).isoformat()
    }
    response = client.get(
        f"/pipeline/{pipeline_id}/status",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 200
    response_data = PipelineStatusResponse(**response.json())
    assert response_data.pipeline_id == pipeline_id
    assert response_data.status == "failed"
    assert response_data.progress == 50.0
    assert response_data.report_url is None
    assert response_data.error_details == "Simulated error during processing."


# --- Get Pipeline Visualization Tests ---

def test_get_pipeline_visualization_unauthenticated():
    pipeline_id = uuid.uuid4()
    response = client.get(f"/pipeline/{pipeline_id}/visualization")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_get_pipeline_visualization_not_found():
    pipeline_id = uuid.uuid4()
    response = client.get(
        f"/pipeline/{pipeline_id}/visualization",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": f"Pipeline with ID {pipeline_id} not found."}

def test_get_pipeline_visualization_invalid_uuid():
    response = client.get(
        f"/pipeline/not-a-uuid/visualization",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 422
    assert "value is not a valid uuid" in response.json()["detail"][0]["msg"]

def test_get_pipeline_visualization_authenticated_success():
    pipeline_id = uuid.uuid4()
    _pipeline_statuses[pipeline_id] = {
        "material_id": "test-material-viz",
        "config": {},
        "status": "completed",
        "progress": 100.0,
        "start_time": datetime.now(timezone.utc).isoformat()
    }
    response = client.get(
        f"/pipeline/{pipeline_id}/visualization",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 200
    assert response.json()["pipeline_id"] == str(pipeline_id)
    assert "graph_data" in response.json()
    assert response.json()["graph_data"] == {"nodes": [], "edges": []} # Placeholder data

def test_get_pipeline_visualization_not_completed():
    pipeline_id = uuid.uuid4()
    _pipeline_statuses[pipeline_id] = {
        "material_id": "test-material-viz-pending",
        "config": {},
        "status": "pending",
        "progress": 0.0,
        "start_time": datetime.now(timezone.utc).isoformat()
    }
    response = client.get(
        f"/pipeline/{pipeline_id}/visualization",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Pipeline {pipeline_id} is not yet completed. Current status: pending"}


# --- Get Pipeline Report Tests ---

def test_get_pipeline_report_unauthenticated():
    pipeline_id = uuid.uuid4()
    response = client.get(f"/pipeline/{pipeline_id}/report")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_get_pipeline_report_not_found():
    pipeline_id = uuid.uuid4()
    response = client.get(
        f"/pipeline/{pipeline_id}/report",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": f"Pipeline with ID {pipeline_id} not found."}

def test_get_pipeline_report_invalid_uuid():
    response = client.get(
        f"/pipeline/not-a-uuid/report",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 422
    assert "value is not a valid uuid" in response.json()["detail"][0]["msg"]

def test_get_pipeline_report_authenticated_success():
    pipeline_id = uuid.uuid4()
    _pipeline_statuses[pipeline_id] = {
        "material_id": "test-material-report",
        "config": {},
        "status": "completed",
        "progress": 100.0,
        "report_url": f"/pipeline/{pipeline_id}/report",
        "start_time": datetime.now(timezone.utc).isoformat()
    }
    response = client.get(
        f"/pipeline/{pipeline_id}/report",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 200
    response_data = PipelineReportResponse(**response.json())
    assert response_data.pipeline_id == pipeline_id
    assert "report_data" in response_data.report_data
    assert "generated_at" in response_data.report_data
    assert isinstance(response_data.generated_at, datetime)

def test_get_pipeline_report_not_completed():
    pipeline_id = uuid.uuid4()
    _pipeline_statuses[pipeline_id] = {
        "material_id": "test-material-report-pending",
        "config": {},
        "status": "pending",
        "progress": 0.0,
        "start_time": datetime.now(timezone.utc).isoformat()
    }
    response = client.get(
        f"/pipeline/{pipeline_id}/report",
        headers={"Authorization": "Bearer valid-token"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Pipeline {pipeline_id} is not yet completed. Current status: pending"}
