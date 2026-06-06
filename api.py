from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import datetime
import asyncio

# Pydantic models for API request and response bodies
class PipelineRunRequest(BaseModel):
    pipelineConfigId: str
    inputData: dict
    callbackUrl: str | None = None
    metadata: dict | None = None

class PipelineErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None

class PipelineRunResponse(BaseModel):
    runId: str
    status: str
    message: str
    submittedAt: datetime.datetime

class PipelineStatusResponse(BaseModel):
    runId: str
    status: str
    progress: float
    currentStage: str | None = None\n    reportUrl: str | None = None
    visualizationUrl: str | None = None
    error: PipelineErrorDetail | None = None
    lastUpdatedAt: datetime.datetime

app = FastAPI(
    title="Material Ingestion Pipeline API",
    description="API for initiating and monitoring material ingestion pipelines."
)

# In-memory store for pipeline statuses (for demonstration and testing purposes).
# In a production environment, this would be replaced by a persistent database or a dedicated state management service.
pipeline_runs = {}

async def _mock_pipeline_execution(run_id: str, config_id: str, input_data: dict):
    """Simulates the actual pipeline execution logic in a background task.
    This function updates the in-memory `pipeline_runs` store to reflect progress and final status.
    """
    print(f"Mock pipeline {run_id} started with config {config_id}")
    # Simulate initial stages
    pipeline_runs[run_id]["status"] = "RUNNING"
    pipeline_runs[run_id]["currentStage"] = "Data Validation"
    pipeline_runs[run_id]["progress"] = 10
    pipeline_runs[run_id]["lastUpdatedAt"] = datetime.datetime.now(datetime.timezone.utc)
    await asyncio.sleep(0.1) # Simulate some work

    # Simulate further processing
    pipeline_runs[run_id]["currentStage"] = "Embedding Generation"
    pipeline_runs[run_id]["progress"] = 50
    pipeline_runs[run_id]["lastUpdatedAt"] = datetime.datetime.now(datetime.timezone.utc)
    await asyncio.sleep(0.1)

    # Simulate success or failure based on input data
    if input_data.get("fail_me"): # A special key to trigger a simulated failure
        pipeline_runs[run_id]["status"] = "FAILED"
        pipeline_runs[run_id]["error"] = PipelineErrorDetail(code="INGESTION_ERROR", message="Simulated pipeline failure during processing")
        pipeline_runs[run_id]["progress"] = 100
    else:
        pipeline_runs[run_id]["status"] = "COMPLETED"
        pipeline_runs[run_id]["reportUrl"] = f"/pipeline/{run_id}/report"
        pipeline_runs[run_id]["visualizationUrl"] = f"/pipeline/{run_id}/visualization"
        pipeline_runs[run_id]["progress"] = 100
    pipeline_runs[run_id]["lastUpdatedAt"] = datetime.datetime.now(datetime.timezone.utc)
    print(f"Mock pipeline {run_id} finished with status {pipeline_runs[run_id]['status']}")


@app.get("/", summary="Root endpoint for the API")
async def read_root():
    return {"message": "Material Ingestion Pipeline API"}

@app.get("/health", summary="Health check endpoint")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()}

@app.post("/pipeline/run", response_model=PipelineRunResponse, status_code=202, summary="Initiate a new pipeline run")
async def start_pipeline_run(request: PipelineRunRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    submitted_at = datetime.datetime.now(datetime.timezone.utc)

    # Store initial pipeline state
    pipeline_runs[run_id] = {
        "runId": run_id,
        "status": "PENDING",
        "progress": 0,
        "submittedAt": submitted_at,
        "lastUpdatedAt": submitted_at,
        "pipelineConfigId": request.pipelineConfigId,
        "inputData": request.inputData,
        "callbackUrl": request.callbackUrl,
        "metadata": request.metadata,
        "error": None
    }

    # Add the mock pipeline execution to background tasks
    background_tasks.add_task(_mock_pipeline_execution, run_id, request.pipelineConfigId, request.inputData)

    return PipelineRunResponse(
        runId=run_id,
        status="PENDING",
        message="Pipeline run initiated successfully",
        submittedAt=submitted_at
    )

@app.get("/pipeline/{run_id}/status", response_model=PipelineStatusResponse, summary="Get the status of a pipeline run")
async def get_pipeline_status(run_id: str):
    run_data = pipeline_runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    # Ensure error is a Pydantic model if present
    if run_data.get("error") and not isinstance(run_data["error"], PipelineErrorDetail):
        run_data["error"] = PipelineErrorDetail(**run_data["error"])
    return PipelineStatusResponse(**run_data)

@app.get("/pipeline/{run_id}/report", summary="Get the detailed report for a completed pipeline run")
async def get_pipeline_report(run_id: str):
    run_data = pipeline_runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    if run_data["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Pipeline not completed yet or failed")
    if not run_data.get("reportUrl"): # Check if report URL was generated
        raise HTTPException(status_code=404, detail="Report not available")
    # In a real scenario, this would fetch the actual report content from storage
    return {"report_content": f"Detailed report for run {run_id}", "url": run_data["reportUrl"]}

@app.get("/pipeline/{run_id}/visualization", summary="Get visualization data for a completed pipeline run")
async def get_pipeline_visualization(run_id: str):
    run_data = pipeline_runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    if run_data["status"] != "COMPLETED":
        raise HTTPException(status_code=400, detail="Pipeline not completed yet or failed")
    if not run_data.get("visualizationUrl"): # Check if visualization URL was generated
        raise HTTPException(status_code=404, detail="Visualization not available")
    # In a real scenario, this would fetch the actual visualization data/URL from storage
    return {"visualization_data": f"Visualization for run {run_id}", "url": run_data["visualizationUrl"]}