import uuid
from typing import Dict, Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Depends
from pydantic import BaseModel, Field

# --- Pydantic Models for Request/Response Validation ---

class PipelineRunRequest(BaseModel):
    material_id: str = Field(..., description="Unique identifier for the material to be ingested")
    config: Dict = Field(default_factory=dict, description="Optional configuration parameters for the pipeline run")

class PipelineRunResponse(BaseModel):
    pipeline_id: uuid.UUID = Field(..., description="Unique ID assigned to the initiated pipeline run")
    status: str = Field("initiated", description="Current status of the pipeline run")
    message: str = Field("Pipeline run initiated successfully", description="Descriptive message")

class PipelineStatusResponse(BaseModel):
    pipeline_id: uuid.UUID = Field(..., description="Unique ID of the pipeline run")
    status: str = Field(..., description="Current status (e.g., 'pending', 'running', 'completed', 'failed')")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage of the pipeline run")
    report_url: Optional[str] = Field(None, description="URL to the detailed pipeline report, if available")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")

# --- FastAPI Application Setup ---

app = FastAPI(
    title="Material Ingestion Pipeline API",
    description="API for managing and monitoring the material ingestion pipeline.",
    version="1.0.0",
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}, 404: {"model": ErrorResponse, "description": "Not Found"}}
)

# --- In-memory store for demonstration purposes ---
# In a real application, this would be a database (e.g., PostgreSQL, Redis)
_pipeline_statuses: Dict[uuid.UUID, Dict] = {}

# --- Conceptual Authentication Dependency ---
# In a real application, this would validate a token (e.g., JWT) and fetch user info.
# For demonstration, we'll just check for a 'Bearer token' header.
async def get_current_user(authorization: Optional[str] = Depends(lambda x: x.headers.get("Authorization"))):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # In a real app, validate the token here
    token = authorization.split(" ")[1]
    if token != "valid-token": # Placeholder for actual token validation
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"username": "testuser", "roles": ["admin"]}

# --- Background Task for Pipeline Execution ---
async def _run_pipeline_task(pipeline_id: uuid.UUID, material_id: str, config: Dict):
    print(f"[BACKGROUND] Starting pipeline {pipeline_id} for material {material_id} with config {config}")
    _pipeline_statuses[pipeline_id] = {"status": "running", "progress": 10.0, "report_url": None}

    # Simulate a long-running, potentially blocking operation
    # In a real scenario, this would involve actual pipeline logic.
    # For CPU-bound tasks, consider `await asyncio.to_thread(blocking_function)`
    # For I/O-bound tasks, use async libraries.
    import asyncio
    await asyncio.sleep(5) # Simulate work

    # Update status upon completion
    _pipeline_statuses[pipeline_id].update({"status": "completed", "progress": 100.0, "report_url": f"/pipeline/{pipeline_id}/report"})
    print(f"[BACKGROUND] Pipeline {pipeline_id} completed.")

# --- API Endpoints ---

@app.get("/health", response_model=Dict[str, str], summary="Health Check")
async def health_check():
    """Checks the health of the API."""
    return {"status": "ok", "message": "API is running"}

@app.post("/pipeline/run", response_model=PipelineRunResponse, status_code=status.HTTP_202_ACCEPTED, summary="Start a new pipeline run")
async def start_pipeline_run(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Initiates a new material ingestion pipeline run in the background."""
    pipeline_id = uuid.uuid4()
    _pipeline_statuses[pipeline_id] = {"status": "pending", "progress": 0.0, "report_url": None}

    background_tasks.add_task(_run_pipeline_task, pipeline_id, request.material_id, request.config)

    return PipelineRunResponse(pipeline_id=pipeline_id)

@app.get("/pipeline/{pipeline_id}/status", response_model=PipelineStatusResponse, summary="Get pipeline run status")
async def get_pipeline_status(
    pipeline_id: uuid.UUID,
    current_user: Dict = Depends(get_current_user)
):
    """Retrieves the current status and progress of a specific pipeline run."""
    status_data = _pipeline_statuses.get(pipeline_id)
    if not status_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")

    return PipelineStatusResponse(pipeline_id=pipeline_id, **status_data)

@app.get("/pipeline/{pipeline_id}/report", response_model=Dict, summary="Get pipeline run report")
async def get_pipeline_report(
    pipeline_id: uuid.UUID,
    current_user: Dict = Depends(get_current_user)
):
    """Retrieves the detailed report for a completed pipeline run."""
    status_data = _pipeline_statuses.get(pipeline_id)
    if not status_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    if status_data["status"] != "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pipeline run not yet completed")

    # Placeholder for actual report generation/retrieval
    return {"pipeline_id": pipeline_id, "report_content": f"Report for {pipeline_id} (simulated)"}

@app.get("/pipeline/{pipeline_id}/visualization", response_model=Dict, summary="Get pipeline visualization data")
async def get_pipeline_visualization(
    pipeline_id: uuid.UUID,
    current_user: Dict = Depends(get_current_user)
):
    """Retrieves data for visualizing the pipeline execution flow."""
    status_data = _pipeline_statuses.get(pipeline_id)
    if not status_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")

    # Placeholder for actual visualization data retrieval
    return {"pipeline_id": pipeline_id, "visualization_data": f"Graph data for {pipeline_id} (simulated)"}

# Example of how to run this API (for local development):
# uvicorn api_refactored:app --reload --port 8000
