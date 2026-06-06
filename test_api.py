import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import datetime
import uuid

# Assuming the FastAPI app and models are defined in api.py
from api import app, pipeline_runs, PipelineRunRequest, PipelineRunResponse, PipelineStatusResponse, PipelineErrorDetail

@pytest.fixture(autouse=True)
def clear_pipeline_runs_store():
    """Fixture to clear the in-memory store before each test to ensure isolation."""
    pipeline_runs.clear()
    yield

@pytest.mark.asyncio
async def test_read_root():
    """Test the root endpoint returns a success message."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Material Ingestion Pipeline API"}

@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint returns a healthy status and timestamp."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"
    assert "timestamp" in response.json()

@pytest.mark.asyncio
@patch("api._mock_pipeline_execution", new_callable=AsyncMock)
async def test_start_pipeline_run_success(mock_pipeline_execution):
    """Test successful initiation of a pipeline run with valid input."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        request_data = {
            "pipelineConfigId": "config-123",
            "inputData": {"document_url": "http://example.com/doc1.pdf"},
            "metadata": {"user": "test_user"}
        }
        response = await ac.post("/pipeline/run", json=request_data)

    assert response.status_code == 202
    response_data = response.json()
    assert "runId" in response_data
    assert response_data["status"] == "PENDING"
    assert response_data["message"] == "Pipeline run initiated successfully"
    assert "submittedAt" in response_data

    run_id = response_data["runId"]
    assert run_id in pipeline_runs
    assert pipeline_runs[run_id]["status"] == "PENDING"
    assert pipeline_runs[run_id]["pipelineConfigId"] == "config-123"
    assert pipeline_runs[run_id]["inputData"] == {"document_url": "http://example.com/doc1.pdf"}

    # Ensure the background task was added and called with correct parameters
    mock_pipeline_execution.assert_called_once_with(
        run_id, request_data["pipelineConfigId"], request_data["inputData"]
    )

@pytest.mark.asyncio
async def test_start_pipeline_run_invalid_input():
    """Test pipeline run initiation with an invalid request body (missing required field)."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Missing required field 'pipelineConfigId'
        request_data = {
            "inputData": {"document_url": "http://example.com/doc1.pdf"}
        }
        response = await ac.post("/pipeline/run", json=request_data)

    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
    assert "detail" in response.json()
    assert any("field required" in err["msg"] for err in response.json()["detail"])

@pytest.mark.asyncio
async def test_get_pipeline_status_pending():
    """Test retrieving status for a pipeline run that is currently PENDING."""
    test_run_id = str(uuid.uuid4())
    submitted_at = datetime.datetime.now(datetime.timezone.utc)
    pipeline_runs[test_run_id] = {
        "runId": test_run_id,
        "status": "PENDING",
        "progress": 0,
        "submittedAt": submitted_at,
        "lastUpdatedAt": submitted_at,
        "pipelineConfigId": "config-test",
        "inputData": {"test_key": "test_value"},
        "error": None
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/status")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["runId"] == test_run_id
    assert response_data["status"] == "PENDING"
    assert response_data["progress"] == 0
    assert response_data["submittedAt"] == submitted_at.isoformat().replace("+00:00", "Z")
    assert response_data["lastUpdatedAt"] == submitted_at.isoformat().replace("+00:00", "Z")
    assert response_data["error"] is None

@pytest.mark.asyncio
async def test_get_pipeline_status_completed():
    """Test retrieving status for a pipeline run that has COMPLETED successfully."""
    test_run_id = str(uuid.uuid4())
    submitted_at = datetime.datetime.now(datetime.timezone.utc)
    completed_at = submitted_at + datetime.timedelta(minutes=5)
    pipeline_runs[test_run_id] = {
        "runId": test_run_id,
        "status": "COMPLETED",
        "progress": 100,
        "submittedAt": submitted_at,
        "lastUpdatedAt": completed_at,
        "pipelineConfigId": "config-test",
        "inputData": {},
        "reportUrl": f"/pipeline/{test_run_id}/report",
        "visualizationUrl": f"/pipeline/{test_run_id}/visualization",
        "error": None
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/status")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["runId"] == test_run_id
    assert response_data["status"] == "COMPLETED"
    assert response_data["progress"] == 100
    assert response_data["reportUrl"] == f"/pipeline/{test_run_id}/report"
    assert response_data["visualizationUrl"] == f"/pipeline/{test_run_id}/visualization"
    assert response_data["error"] is None

@pytest.mark.asyncio
async def test_get_pipeline_status_failed():
    """Test retrieving status for a pipeline run that has FAILED."""
    test_run_id = str(uuid.uuid4())
    submitted_at = datetime.datetime.now(datetime.timezone.utc)
    failed_at = submitted_at + datetime.timedelta(minutes=2)
    pipeline_runs[test_run_id] = {
        "runId": test_run_id,
        "status": "FAILED",
        "progress": 75,
        "submittedAt": submitted_at,
        "lastUpdatedAt": failed_at,
        "pipelineConfigId": "config-test",
        "inputData": {},
        "error": PipelineErrorDetail(code="VALIDATION_ERROR", message="Input data schema mismatch").dict(),
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/status")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["runId"] == test_run_id
    assert response_data["status"] == "FAILED"
    assert response_data["progress"] == 75
    assert response_data["error"] == {"code": "VALIDATION_ERROR", "message": "Input data schema mismatch", "details": None}

@pytest.mark.asyncio
async def test_get_pipeline_status_not_found():
    """Test retrieving status for a non-existent pipeline run ID."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{uuid.uuid4()}/status")
    assert response.status_code == 404
    assert response.json() == {"detail": "Pipeline run not found"}

@pytest.mark.asyncio
async def test_get_pipeline_report_success():
    """Test retrieving a report for a successfully completed pipeline run."""
    test_run_id = str(uuid.uuid4())
    pipeline_runs[test_run_id] = {
        "runId": test_run_id, "status": "COMPLETED", "progress": 100,
        "submittedAt": datetime.datetime.now(datetime.timezone.utc),
        "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
        "pipelineConfigId": "config-test", "inputData": {},
        "reportUrl": f"/pipeline/{test_run_id}/report_content.json",
        "error": None
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/report")
    assert response.status_code == 200
    assert response.json()["report_content"] == f"Detailed report for run {test_run_id}"
    assert response.json()["url"] == f"/pipeline/{test_run_id}/report_content.json"

@pytest.mark.asyncio
async def test_get_pipeline_report_not_found():
    """Test retrieving a report for a non-existent pipeline run ID."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{uuid.uuid4()}/report")
    assert response.status_code == 404
    assert response.json() == {"detail": "Pipeline run not found"}

@pytest.mark.asyncio
async def test_get_pipeline_report_not_completed():
    """Test retrieving a report for a pipeline run that is not yet completed."""
    test_run_id = str(uuid.uuid4())
    pipeline_runs[test_run_id] = {
        "runId": test_run_id, "status": "RUNNING", "progress": 50,
        "submittedAt": datetime.datetime.now(datetime.timezone.utc),
        "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
        "pipelineConfigId": "config-test", "inputData": {},
        "error": None
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/report")
    assert response.status_code == 400
    assert response.json() == {"detail": "Pipeline not completed yet or failed"}

@pytest.mark.asyncio
async def test_get_pipeline_report_url_not_available():
    """Test retrieving a report when the report URL is not set, even if completed."""
    test_run_id = str(uuid.uuid4())
    pipeline_runs[test_run_id] = {
        "runId": test_run_id, "status": "COMPLETED", "progress": 100,
        "submittedAt": datetime.datetime.now(datetime.timezone.utc),
        "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
        "pipelineConfigId": "config-test", "inputData": {},
        "error": None
        # No reportUrl
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/report")
    assert response.status_code == 404
    assert response.json() == {"detail": "Report not available"}


@pytest.mark.asyncio
async def test_get_pipeline_visualization_success():
    """Test retrieving visualization data for a successfully completed pipeline run."""
    test_run_id = str(uuid.uuid4())
    pipeline_runs[test_run_id] = {
        "runId": test_run_id, "status": "COMPLETED", "progress": 100,
        "submittedAt": datetime.datetime.now(datetime.timezone.utc),
        "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
        "pipelineConfigId": "config-test", "inputData": {},
        "visualizationUrl": f"/pipeline/{test_run_id}/viz_data.json",
        "error": None
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/visualization")
    assert response.status_code == 200
    assert response.json()["visualization_data"] == f"Visualization for run {test_run_id}"
    assert response.json()["url"] == f"/pipeline/{test_run_id}/viz_data.json"

@pytest.mark.asyncio
async def test_get_pipeline_visualization_not_found():
    """Test retrieving visualization data for a non-existent pipeline run ID."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{uuid.uuid4()}/visualization")
    assert response.status_code == 404
    assert response.json() == {"detail": "Pipeline run not found"}

@pytest.mark.asyncio
async def test_get_pipeline_visualization_not_completed():
    """Test retrieving visualization data for a pipeline run that is not yet completed."""
    test_run_id = str(uuid.uuid4())
    pipeline_runs[test_run_id] = {
        "runId": test_run_id, "status": "RUNNING", "progress": 50,
        "submittedAt": datetime.datetime.now(datetime.timezone.utc),
        "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
        "pipelineConfigId": "config-test", "inputData": {},
        "error": None
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/visualization")
    assert response.status_code == 400
    assert response.json() == {"detail": "Pipeline not completed yet or failed"}

@pytest.mark.asyncio
async def test_get_pipeline_visualization_url_not_available():
    """Test retrieving visualization data when the URL is not set, even if completed."""
    test_run_id = str(uuid.uuid4())
    pipeline_runs[test_run_id] = {
        "runId": test_run_id, "status": "COMPLETED", "progress": 100,
        "submittedAt": datetime.datetime.now(datetime.timezone.utc),
        "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
        "pipelineConfigId": "config-test", "inputData": {},
        "error": None
        # No visualizationUrl
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/pipeline/{test_run_id}/visualization")
    assert response.status_code == 404
    assert response.json() == {"detail": "Visualization not available"}

# Integration test: simulate a full run from start to completion (mocking background task internals)
@pytest.mark.asyncio
async def test_full_pipeline_run_lifecycle_success():
    """Integration test for a full successful pipeline run lifecycle, from initiation to report/visualization retrieval."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Start pipeline
        request_data = {
            "pipelineConfigId": "config-full-success",
            "inputData": {"document_id": "doc-full-success"},
        }
        start_response = await ac.post("/pipeline/run", json=request_data)
        assert start_response.status_code == 202
        run_id = start_response.json()["runId"]

        # 2. Check status immediately (should be PENDING)
        status_response_pending = await ac.get(f"/pipeline/{run_id}/status")
        assert status_response_pending.status_code == 200
        assert status_response_pending.json()["status"] == "PENDING"
        assert status_response_pending.json()["progress"] == 0

        # 3. Manually advance the state to COMPLETED (simulating background task finishing)
        # In a real integration test, you might wait for the background task or use a more sophisticated mock
        # For this test, we directly manipulate the shared state as if the background task completed.
        pipeline_runs[run_id].update({
            "status": "COMPLETED",
            "progress": 100,
            "currentStage": "Finished",
            "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
            "reportUrl": f"/pipeline/{run_id}/report",
            "visualizationUrl": f"/pipeline/{run_id}/visualization",
            "error": None
        })

        # 4. Check status again (should be COMPLETED)
        status_response_completed = await ac.get(f"/pipeline/{run_id}/status")
        assert status_response_completed.status_code == 200
        assert status_response_completed.json()["status"] == "COMPLETED"
        assert status_response_completed.json()["progress"] == 100
        assert "reportUrl" in status_response_completed.json()
        assert "visualizationUrl" in status_response_completed.json()

        # 5. Get report
        report_response = await ac.get(f"/pipeline/{run_id}/report")
        assert report_response.status_code == 200
        assert "report_content" in report_response.json()

        # 6. Get visualization
        viz_response = await ac.get(f"/pipeline/{run_id}/visualization")
        assert viz_response.status_code == 200
        assert "visualization_data" in viz_response.json()

@pytest.mark.asyncio
async def test_full_pipeline_run_lifecycle_failure():
    """Integration test for a full failed pipeline run lifecycle, including attempts to retrieve reports/visualizations."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Start pipeline with input that triggers failure
        request_data = {
            "pipelineConfigId": "config-full-fail",
            "inputData": {"document_id": "doc-full-fail", "fail_me": True}, # This input will trigger failure in _mock_pipeline_execution
        }
        start_response = await ac.post("/pipeline/run", json=request_data)
        assert start_response.status_code == 202
        run_id = start_response.json()["runId"]

        # 2. Check status immediately (should be PENDING)
        status_response_pending = await ac.get(f"/pipeline/{run_id}/status")
        assert status_response_pending.status_code == 200
        assert status_response_pending.json()["status"] == "PENDING"

        # 3. Manually advance the state to FAILED
        pipeline_runs[run_id].update({
            "status": "FAILED",
            "progress": 75,
            "currentStage": "Data Processing",
            "lastUpdatedAt": datetime.datetime.now(datetime.timezone.utc),
            "error": PipelineErrorDetail(code="PROCESSING_ERROR", message="Failed to process document").dict(),
        })

        # 4. Check status again (should be FAILED)
        status_response_failed = await ac.get(f"/pipeline/{run_id}/status")
        assert status_response_failed.status_code == 200
        assert status_response_failed.json()["status"] == "FAILED"
        assert status_response_failed.json()["progress"] == 75
        assert "error" in status_response_failed.json()

        # 5. Attempt to get report (should fail as not completed)
        report_response = await ac.get(f"/pipeline/{run_id}/report")
        assert report_response.status_code == 400
        assert report_response.json() == {"detail": "Pipeline not completed yet or failed"}

        # 6. Attempt to get visualization (should fail as not completed)
        viz_response = await ac.get(f"/pipeline/{run_id}/visualization")
        assert viz_response.status_code == 400
        assert viz_response.json() == {"detail": "Pipeline not completed yet or failed"}