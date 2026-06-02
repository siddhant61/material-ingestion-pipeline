import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime
import uuid

# Import the FastAPI app and models from your api.py module
# Assuming api.py is in the same directory or accessible via PYTHONPATH
from api import (
    app,
    API_KEY,
    API_KEY_NAME,
    pipeline_runs,
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineStatusResponse,
    PipelineVisualizationResponse,
    PipelineReportResponse,
    ApiError,
    run_pipeline_in_background
)

# Create a TestClient instance for your FastAPI app
@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for the FastAPI app."""
    with TestClient(app) as c:
        yield c

# Fixture to clear pipeline_runs dictionary before each test
@pytest.fixture(autouse=True)
def clear_pipeline_runs():
    """Ensures the global pipeline_runs dictionary is empty before and after each test."""
    pipeline_runs.clear()
    yield
    pipeline_runs.clear()

# --- Health Check Endpoint Tests ---
def test_health_check_success(client):
    """Test the /health endpoint returns a successful status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# --- Root Endpoint Test ---
def test_read_root_success(client):
    """Test the root endpoint returns a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Material Ingestion Pipeline API" in response.text
    assert "Welcome to the Material Ingestion Pipeline API!" in response.text

# --- Start Pipeline Run Endpoint Tests ---
def test_start_pipeline_run_success(client, clear_pipeline_runs):
    """Test initiating a pipeline run with valid data and API key."""
    material_id = str(uuid.uuid4())
    request_payload = {
        "materialId": material_id,
        "sourceType": "web_crawl",
        "configuration": {"url": "http://example.com", "depth": 2},
        "priority": 50,
        "callbackUrl": "http://callback.url/status"
    }
    response = client.post("/pipeline/run", json=request_payload, headers={API_KEY_NAME: API_KEY})

    assert response.status_code == 202
    response_data = PipelineRunResponse(**response.json())
    assert response_data.runId is not None
    assert response_data.status == "QUEUED" # The immediate response status, before background task completes
    assert response_data.message == "Pipeline run initiated successfully."
    assert response_data.timestamp is not None

    # Verify that the run was added to pipeline_runs and its final state after background task completion
    assert response_data.runId in pipeline_runs
    final_run_state = pipeline_runs.get(response_data.runId)
    assert final_run_state is not None
    assert final_run_state["status"] == "COMPLETED"
    assert final_run_state["progress"] == 100
    assert final_run_state["endTime"] is not None
    assert "Simulated pipeline run completed" in final_run_state["details"].get("message", "")

def test_start_pipeline_run_missing_api_key(client):
    """Test initiating a pipeline run without an API key."""
    request_payload = {
        "materialId": str(uuid.uuid4()),
        "sourceType": "web_crawl",
        "configuration": {"url": "http://example.com"}
    }
    response = client.post("/pipeline/run", json=request_payload) # No API key header
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_start_pipeline_run_invalid_api_key(client):
    """Test initiating a pipeline run with an invalid API key."""
    request_payload = {
        "materialId": str(uuid.uuid4()),
        "sourceType": "web_crawl",
        "configuration": {"url": "http://example.com"}
    }
    response = client.post("/pipeline/run", json=request_payload, headers={API_KEY_NAME: "wrong-key"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

@pytest.mark.parametrize("field, value, expected_error_msg", [
    ("materialId", None, "field required"),
    ("materialId", 123, "value is not a valid string"),
    ("sourceType", None, "field required"),
    ("sourceType", "", "ensure this value has at least 1 character"),
    ("configuration", None, "field required"),
    ("configuration", "not_a_dict", "value is not a valid dictionary"),
    ("priority", 0, "ensure this value is greater than or equal to 1"),
    ("priority", 101, "ensure this value is less than or equal to 100"),
])
def test_start_pipeline_run_validation_errors(client, field, value, expected_error_msg):
    """Test various validation errors for PipelineRunRequest payload."""
    base_payload = {
        "materialId": str(uuid.uuid4()),
        "sourceType": "web_crawl",
        "configuration": {"url": "http://example.com"}
    }
    if value is None:
        del base_payload[field]
    else:
        base_payload[field] = value

    response = client.post("/pipeline/run", json=base_payload, headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 422
    error_data = response.json()
    assert error_data["detail"][0]["loc"] == ["body", field]
    assert expected_error_msg in error_data["detail"][0]["msg"]

def test_start_pipeline_run_background_task_failure(client, clear_pipeline_runs):
    """Test initiating a pipeline run where the background task simulates a failure."""
    # Define a mock function that simulates a failing pipeline task
    def failing_pipeline_task(run_id: str):
        pipeline_runs[run_id]["status"] = "RUNNING"
        pipeline_runs[run_id]["currentStage"] = "Failure Simulation"
        pipeline_runs[run_id]["progress"] = 20
        error_msg = "Simulated pipeline failure during processing"
        pipeline_runs[run_id]["errors"].append(ApiError(code="SIMULATED_FAILURE", message=error_msg).dict())
        pipeline_runs[run_id]["status"] = "FAILED"
        pipeline_runs[run_id]["progress"] = 100
        pipeline_runs[run_id]["endTime"] = datetime.now().isoformat()
        pipeline_runs[run_id]["details"]["message"] = error_msg

    # Patch the actual run_pipeline_in_background function with our failing mock
    with patch('api.run_pipeline_in_background', new=failing_pipeline_task):
        material_id = str(uuid.uuid4())
        request_payload = {
            "materialId": material_id,
            "sourceType": "web_crawl",
            "configuration": {"url": "http://example.com"}
        }
        response = client.post("/pipeline/run", json=request_payload, headers={API_KEY_NAME: API_KEY})

        assert response.status_code == 202
        response_data = PipelineRunResponse(**response.json())
        assert response_data.runId is not None
        assert response_data.status == "QUEUED" # Initial response is still QUEUED

        # Verify the final state in pipeline_runs reflects the simulated failure
        final_run_state = pipeline_runs.get(response_data.runId)
        assert final_run_state is not None
        assert final_run_state["status"] == "FAILED"
        assert final_run_state["progress"] == 100
        assert final_run_state["errors"] is not None
        assert len(final_run_state["errors"]) > 0
        assert final_run_state["errors"][0]["code"] == "SIMULATED_FAILURE"
        assert "Simulated pipeline failure" in final_run_state["errors"][0]["message"]

# --- Get Pipeline Status Endpoint Tests ---
def test_get_pipeline_status_success(client, clear_pipeline_runs):
    """Test retrieving the status of an existing pipeline run."""
    run_id = str(uuid.uuid4())
    # Manually add a pipeline run to simulate it being in progress
    pipeline_runs[run_id] = {
        "runId": run_id,
        "status": "RUNNING",
        "progress": 50,
        "currentStage": "Extraction",
        "details": {"extracted_items": 10},
        "errors": [],
        "startTime": datetime.now().isoformat(),
        "endTime": None
    }

    response = client.get(f"/pipeline/{run_id}/status", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 200
    response_data = PipelineStatusResponse(**response.json())
    assert response_data.runId == run_id
    assert response_data.status == "RUNNING"
    assert response_data.progress == 50
    assert response_data.currentStage == "Extraction"

def test_get_pipeline_status_not_found(client):
    """Test retrieving status for a non-existent pipeline run."""
    non_existent_run_id = str(uuid.uuid4())
    response = client.get(f"/pipeline/{non_existent_run_id}/status", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline run not found."

def test_get_pipeline_status_invalid_run_id_format(client):
    """Test retrieving status with an invalid UUID format for run_id."""
    invalid_run_id = "not-a-uuid"
    response = client.get(f"/pipeline/{invalid_run_id}/status", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 422 # FastAPI path parameter validation error
    error_data = response.json()
    assert error_data["detail"][0]["loc"] == ["path", "run_id"]
    assert "value is not a valid uuid" in error_data["detail"][0]["msg"]

def test_get_pipeline_status_missing_api_key(client):
    """Test retrieving status without an API key."""
    run_id = str(uuid.uuid4())
    response = client.get(f"/pipeline/{run_id}/status")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_get_pipeline_status_invalid_api_key(client):
    """Test retrieving status with an invalid API key."""
    run_id = str(uuid.uuid4())
    response = client.get(f"/pipeline/{run_id}/status", headers={API_KEY_NAME: "wrong-key"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

# --- Get Pipeline Visualization Endpoint Tests ---
def test_get_pipeline_visualization_success(client, clear_pipeline_runs):
    """Test retrieving visualization data for a completed pipeline run."""
    run_id = str(uuid.uuid4())
    pipeline_runs[run_id] = {
        "runId": run_id,
        "status": "COMPLETED",
        "progress": 100,
        "currentStage": "Reporting",
        "details": {},
        "errors": [],
        "startTime": datetime.now().isoformat(),
        "endTime": datetime.now().isoformat(),
        "visualization": {
            "visualizationType": "mermaid",
            "data": "graph TD; A-->B; B-->C;",
            "description": "Simple pipeline flow"
        }
    }
    response = client.get(f"/pipeline/{run_id}/visualization", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 200
    response_data = PipelineVisualizationResponse(**response.json())
    assert response_data.runId == run_id
    assert response_data.visualizationType == "mermaid"
    assert response_data.data == "graph TD; A-->B; B-->C;"

def test_get_pipeline_visualization_not_found(client):
    """Test retrieving visualization for a non-existent pipeline run."""
    non_existent_run_id = str(uuid.uuid4())
    response = client.get(f"/pipeline/{non_existent_run_id}/visualization", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline run not found."

def test_get_pipeline_visualization_no_visualization_data(client, clear_pipeline_runs):
    """Test retrieving visualization when no data is available for the run."""
    run_id = str(uuid.uuid4())
    pipeline_runs[run_id] = {
        "runId": run_id,
        "status": "RUNNING",
        "progress": 70,
        "currentStage": "Embedding",
        "details": {},
        "errors": [],
        "startTime": datetime.now().isoformat(),
        "endTime": None,
        # No 'visualization' key
    }
    response = client.get(f"/pipeline/{run_id}/visualization", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 404
    assert response.json()["detail"] == "Visualization data not available for this run."

# --- Get Pipeline Report Endpoint Tests ---
def test_get_pipeline_report_success(client, clear_pipeline_runs):
    """Test retrieving report data for a completed pipeline run."""
    run_id = str(uuid.uuid4())
    pipeline_runs[run_id] = {
        "runId": run_id,
        "status": "COMPLETED",
        "progress": 100,
        "currentStage": "Reporting",
        "details": {},
        "errors": [],
        "startTime": datetime.now().isoformat(),
        "endTime": datetime.now().isoformat(),
        "report": {
            "reportFormat": "json",
            "reportContent": {"summary": "Ingestion successful", "items_processed": 100},
            "generatedAt": datetime.now().isoformat()
        }
    }
    response = client.get(f"/pipeline/{run_id}/report", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 200
    response_data = PipelineReportResponse(**response.json())
    assert response_data.runId == run_id
    assert response_data.reportFormat == "json"
    assert response_data.reportContent == {"summary": "Ingestion successful", "items_processed": 100}

def test_get_pipeline_report_not_found(client):
    """Test retrieving report for a non-existent pipeline run."""
    non_existent_run_id = str(uuid.uuid4())
    response = client.get(f"/pipeline/{non_existent_run_id}/report", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline run not found."

def test_get_pipeline_report_no_report_data(client, clear_pipeline_runs):
    """Test retrieving report when no data is available for the run."""
    run_id = str(uuid.uuid4())
    pipeline_runs[run_id] = {
        "runId": run_id,
        "status": "RUNNING",
        "progress": 90,
        "currentStage": "Reporting",
        "details": {},
        "errors": [],
        "startTime": datetime.now().isoformat(),
        "endTime": None,
        # No 'report' key
    }
    response = client.get(f"/pipeline/{run_id}/report", headers={API_KEY_NAME: API_KEY})
    assert response.status_code == 404
    assert response.json()["detail"] == "Report data not available for this run."

# --- Global Exception Handler Tests ---
def test_global_unexpected_exception_handler(client):
    """Test the global exception handler for unexpected internal errors."""
    # Mock run_pipeline_in_background to raise a generic Exception
    with patch('api.run_pipeline_in_background', side_effect=Exception("Simulated internal error")):
        material_id = str(uuid.uuid4())
        request_payload = {
            "materialId": material_id,
            "sourceType": "web_crawl",
            "configuration": {"url": "http://example.com"}
        }
        response = client.post("/pipeline/run", json=request_payload, headers={API_KEY_NAME: API_KEY})
        assert response.status_code == 500
        error_data = response.json()
        assert error_data["code"] == "INTERNAL_SERVER_ERROR"
        assert "Simulated internal error" in error_data["message"]
        assert "path" in error_data["details"]
        assert "method" in error_data["details"]
