import pytest
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError
from src.api.models import (
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineStatusResponse,
    PipelineReportResponse,
    ErrorResponse,
    HealthCheckResponse
)

# --- PipelineRunRequest Tests ---
def test_pipeline_run_request_valid():
    request = PipelineRunRequest(material_id="test-material-1", config={"key": "value"})
    assert request.material_id == "test-material-1"
    assert request.config == {"key": "value"}

def test_pipeline_run_request_valid_no_config():
    request = PipelineRunRequest(material_id="test-material-2")
    assert request.material_id == "test-material-2"
    assert request.config == {} # Default empty dict

def test_pipeline_run_request_missing_material_id():
    with pytest.raises(ValidationError):
        PipelineRunRequest(config={"key": "value"})

def test_pipeline_run_request_empty_material_id():
    with pytest.raises(ValidationError):
        PipelineRunRequest(material_id="", config={"key": "value"})

# --- PipelineRunResponse Tests ---
def test_pipeline_run_response_valid():
    pipeline_id = uuid.uuid4()
    response = PipelineRunResponse(pipeline_id=pipeline_id, status="initiated", message="Success")
    assert response.pipeline_id == pipeline_id
    assert response.status == "initiated"
    assert response.message == "Success"

def test_pipeline_run_response_invalid_status():
    pipeline_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        PipelineRunResponse(pipeline_id=pipeline_id, status="running", message="Invalid")

# --- PipelineStatusResponse Tests ---
def test_pipeline_status_response_valid_completed():
    pipeline_id = uuid.uuid4()
    response = PipelineStatusResponse(
        pipeline_id=pipeline_id,
        status="completed",
        progress=100.0,
        report_url=f"/report/{pipeline_id}"
    )
    assert response.pipeline_id == pipeline_id
    assert response.status == "completed"
    assert response.progress == 100.0
    assert response.report_url == f"/report/{pipeline_id}"
    assert response.error_details is None

def test_pipeline_status_response_valid_failed():
    pipeline_id = uuid.uuid4()
    response = PipelineStatusResponse(
        pipeline_id=pipeline_id,
        status="failed",
        progress=50.0,
        error_details="Something went wrong"
    )
    assert response.pipeline_id == pipeline_id
    assert response.status == "failed"
    assert response.progress == 50.0
    assert response.report_url is None
    assert response.error_details == "Something went wrong"

def test_pipeline_status_response_invalid_status():
    pipeline_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        PipelineStatusResponse(pipeline_id=pipeline_id, status="invalid", progress=0.0)

def test_pipeline_status_response_invalid_progress_low():
    pipeline_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        PipelineStatusResponse(pipeline_id=pipeline_id, status="pending", progress=-1.0)

def test_pipeline_status_response_invalid_progress_high():
    pipeline_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        PipelineStatusResponse(pipeline_id=pipeline_id, status="pending", progress=101.0)

# --- PipelineReportResponse Tests ---
def test_pipeline_report_response_valid():
    pipeline_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    response = PipelineReportResponse(
        pipeline_id=pipeline_id,
        report_data={"summary": "All good"},
        generated_at=now
    )
    assert response.pipeline_id == pipeline_id
    assert response.report_data == {"summary": "All good"}
    assert response.generated_at == now

def test_pipeline_report_response_missing_generated_at():
    pipeline_id = uuid.uuid4()
    with pytest.raises(ValidationError):
        PipelineReportResponse(pipeline_id=pipeline_id, report_data={"summary": "All good"})

# --- ErrorResponse Tests ---
def test_error_response_valid():
    response = ErrorResponse(detail="Not found", code="NOT_FOUND")
    assert response.detail == "Not found"
    assert response.code == "NOT_FOUND"

def test_error_response_valid_no_code():
    response = ErrorResponse(detail="Internal error")
    assert response.detail == "Internal error"
    assert response.code is None

# --- HealthCheckResponse Tests ---
def test_health_check_response_valid_ok():
    now = datetime.now(timezone.utc)
    response = HealthCheckResponse(
        status="ok",
        message="API is running",
        timestamp=now,
        dependencies={"db": "ok"}
    )
    assert response.status == "ok"
    assert response.message == "API is running"
    assert response.timestamp == now
    assert response.dependencies == {"db": "ok"}

def test_health_check_response_valid_degraded():
    now = datetime.now(timezone.utc)
    response = HealthCheckResponse(
        status="degraded",
        message="Some services are affected",
        timestamp=now
    )
    assert response.status == "degraded"
    assert response.message == "Some services are affected"
    assert response.timestamp == now
    assert response.dependencies is None

def test_health_check_response_invalid_status():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        HealthCheckResponse(status="bad", message="Invalid", timestamp=now)
