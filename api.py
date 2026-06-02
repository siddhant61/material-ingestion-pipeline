import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, ValidationError

# --- Configuration and Logging Setup ---
API_KEY_NAME = "X-API-Key"
API_KEY = "your-super-secret-api-key" # WARNING: This API_KEY is hardcoded for demonstration.
                                     # In a production environment, it MUST be loaded from environment variables or a secure secret management system.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Material Ingestion Pipeline API",
    description="API for initiating and monitoring the material ingestion pipeline.",
    version="1.0.0",
    openapi_tags=[
        {"name": "pipeline", "description": "Operations related to pipeline execution and status."},
        {"name": "health", "description": "Health check endpoint."}
    ]
)

# --- Shared Pydantic Models (aligned with shared-api-contracts.ts) ---

class ApiError(BaseModel):
    code: str = Field(..., example="VALIDATION_ERROR")
    message: str = Field(..., example="Invalid input provided for materialId.")
    details: Optional[Dict[str, Any]] = Field(None, example={"field": "materialId", "reason": "must be a UUID"})

class PipelineRunRequest(BaseModel):
    materialId: str = Field(..., description="Unique identifier for the material to be ingested.", example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    sourceType: str = Field(..., description="Type of the source material (e.g., 'web_crawl', 'document_upload').", example="web_crawl")
    configuration: Dict[str, Any] = Field(..., description="Flexible configuration object for the pipeline run.")
    priority: Optional[int] = Field(10, ge=1, le=100, description="Priority of the pipeline run (1-100, 10 is default).")
    callbackUrl: Optional[str] = Field(None, description="Optional URL for status updates during/after the run.")
    output_dir: Optional[str] = Field(None, description="Path to the directory where pipeline outputs will be saved. If not provided, a default will be used.")


class PipelineRunResponse(BaseModel):
    runId: str = Field(..., description="Unique identifier for this pipeline run.", example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    status: str = Field(..., example="QUEUED", description="Current status: 'QUEUED', 'RUNNING', 'FAILED', 'COMPLETED', 'CANCELLED'.")
    message: str = Field(..., example="Pipeline run initiated successfully.", description="Status message.")
    timestamp: str = Field(..., example="2023-10-27T10:00:00Z", description="ISO 8601 format timestamp of initiation.")

class PipelineStatusResponse(BaseModel):
    runId: str = Field(..., description="Unique identifier for this pipeline run.", example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    status: str = Field(..., example="RUNNING", description="Current status: 'QUEUED', 'RUNNING', 'FAILED', 'COMPLETED', 'CANCELLED'.")
    progress: int = Field(0, ge=0, le=100, description="Percentage completion (0-100).")
    currentStage: Optional[str] = Field(None, example="Extraction", description="Current stage of the pipeline (e.g., 'Extraction', 'Validation', 'Embedding').")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the current stage or overall run.")
    errors: Optional[List[ApiError]] = Field(None, description="List of errors encountered during the run.")
    startTime: str = Field(..., example="2023-10-27T10:00:00Z", description="ISO 8601 format timestamp of start.")
    endTime: Optional[str] = Field(None, example="2023-10-27T10:15:00Z", description="ISO 8601 format timestamp of completion/failure.")

class PipelineVisualizationResponse(BaseModel):
    runId: str = Field(..., description="Unique identifier for this pipeline run.")
    visualizationType: str = Field(..., example="html", description="Type of visualization (e.g., 'graph', 'mermaid', 'image_url', 'html').")
    data: str = Field(..., description="Graph definition (e.g., Mermaid syntax), base64 image, URL, or HTML content.")
    description: Optional[str] = Field(None, description="Description of the visualization.")

class PipelineReportResponse(BaseModel):
    runId: str = Field(..., description="Unique identifier for this pipeline run.")
    reportFormat: str = Field(..., example="json", description="Format of the report (e.g., 'json', 'pdf', 'html').")
    reportContent: Any = Field(..., description="JSON object or URL/base64 content.") # Use Any for flexible content type
    generatedAt: str = Field(..., example="2023-10-27T10:15:00Z", description="ISO 8601 format timestamp of report generation.")


# --- In-memory store for pipeline run statuses ---
# In a real application, this would be a persistent store (database, Redis, etc.)
class PipelineRunState(PipelineStatusResponse):
    # Add internal fields not exposed directly via API if needed
    _output_path: Optional[Path] = None # Internal path for output files

pipeline_runs: Dict[str, PipelineRunState] = {}

# --- Dependency for API Key Authentication ---
def get_api_key(api_key: str = Depends(lambda x: x.headers.get(API_KEY_NAME))):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key

# --- Global Exception Handlers ---
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    errors = []
    for error in exc.errors():
        errors.append(ApiError(
            code="VALIDATION_ERROR",
            message=f"Field '{error['loc'][0]}' validation failed: {error['msg']}",
            details={"field": error['loc'][0], "reason": error['msg'], "type": error['type']}
        ).dict())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "errors": errors,
            "message": "Validation Error",
            "code": "VALIDATION_ERROR"
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "errors": [ApiError(code=str(exc.status_code), message=exc.detail).dict()],
            "message": exc.detail,
            "code": str(exc.status_code)
        },
    )

# --- Background Task for Pipeline Execution ---
# This function is designed to be run in a background thread by FastAPI's BackgroundTasks.
# It should not be async itself if the underlying pipeline logic is synchronous.
# The actual pipeline logic (e.g., from cli.py or core.pipeline) would be called here.
def run_pipeline_in_background(run_id: str, material_id: str, source_type: str, config: Dict[str, Any], output_dir: Path):
    logger.info(f"Starting pipeline run {run_id} for material {material_id} (source: {source_type}) with config: {config} and output to {output_dir}")
    
    # Update status to RUNNING
    if run_id in pipeline_runs:
        pipeline_runs[run_id].status = "RUNNING"
        pipeline_runs[run_id].currentStage = "Initialization"
        pipeline_runs[run_id].progress = 5
        pipeline_runs[run_id]._output_path = output_dir # Store internal path
    else:
        logger.error(f"Run ID {run_id} not found in pipeline_runs dictionary during background execution.")
        return # Cannot proceed without a valid run_id entry

    try:
        # --- Integration Point for Actual Pipeline Execution Logic ---
        # In a production scenario, this section would contain the actual call to the core
        # pipeline logic, adapting the new materialId, sourceType, and configuration
        # parameters to the pipeline's expected input format (e.g., input_dir, output_dir).
        # Example:
        # from core.pipeline.main import run_pipeline_core
        # run_pipeline_core(material_id, source_type, config, output_dir)
        # This might involve creating temporary input files or an adapter layer.
        # For this formalization, we assume the core pipeline will be updated or an
        # adapter will be provided to handle the new API contract.

        logger.info(f"Pipeline logic for run {run_id} would execute here. Currently simulating instant completion.")
        
        # Simulate output file creation for status checks and retrieval endpoints
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "knowledge_graph_interactive.html").write_text("<html><body><h1>Visualization Content</h1></body></html>")
        (output_dir / "pipeline_report.json").write_text('{"status": "success", "data": {"processed_items": 10, "errors": 0}}')

        # Update status to COMPLETED
        pipeline_runs[run_id].status = "COMPLETED"
        pipeline_runs[run_id].endTime = datetime.now().isoformat()
        pipeline_runs[run_id].progress = 100
        pipeline_runs[run_id].currentStage = "Finished"
        logger.info(f"Pipeline run {run_id} completed successfully (simulated).")

    except Exception as e:
        logger.error(f"Pipeline run {run_id} failed with error: {e}", exc_info=True)
        pipeline_runs[run_id].status = "FAILED"
        pipeline_runs[run_id].endTime = datetime.now().isoformat()
        pipeline_runs[run_id].errors = [ApiError(code="PIPELINE_EXECUTION_ERROR", message=str(e))]
        pipeline_runs[run_id].currentStage = "Error"

# --- API Endpoints ---

@app.get("/", tags=["health"])
def read_root():
    """Root endpoint with API information."""
    return {
        "name": "Material Ingestion Pipeline API",
        "version": "1.0.0",
        "description": "API for running the Material Ingestion Pipeline on educational content",
        "endpoints": {
            "POST /pipeline/run": "Start a new pipeline run",
            "GET /pipeline/status/{run_id}": "Check the status of a pipeline run",
            "GET /pipeline/results/{run_id}/visualization": "Get the interactive visualization for a run",
            "GET /pipeline/results/{run_id}/report": "Get the execution report for a run",
            "GET /health": "Health check endpoint"
        }
    }

@app.post("/pipeline/run", response_model=PipelineRunResponse, status_code=status.HTTP_202_ACCEPTED, tags=["pipeline"])
async def start_pipeline_run(request: PipelineRunRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    """
    Start a new pipeline run asynchronously.
    
    This endpoint accepts material details and configuration, generates a unique run ID,
    and starts the pipeline execution in the background using FastAPI's BackgroundTasks.
    The pipeline runs asynchronously to avoid HTTP timeouts, as it can take several
    minutes to complete.
    """
    run_id = str(uuid4())
    current_time = datetime.now().isoformat()

    # Determine output directory
    base_output_dir = Path("./pipeline_outputs") # Default base output directory
    if request.output_dir:
        output_path = Path(request.output_dir).resolve()
    else:
        output_path = base_output_dir / run_id # Create a unique subdirectory for each run

    # Ensure output directory exists for initial status files if needed
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize pipeline run state
    pipeline_runs[run_id] = PipelineRunState(
        runId=run_id,
        status="QUEUED",
        progress=0,
        startTime=current_time,
        message="Pipeline run queued.",
        _output_path=output_path # Store the resolved path internally
    )
    
    background_tasks.add_task(
        run_pipeline_in_background,
        run_id,
        request.materialId,
        request.sourceType,
        request.configuration,
        output_path # Pass the resolved Path object
    )

    logger.info(f"Pipeline run {run_id} initiated for material {request.materialId}. Output to {output_path}")
    return PipelineRunResponse(
        runId=run_id,
        status="QUEUED",
        message="Pipeline run initiated successfully. Check status endpoint for updates.",
        timestamp=current_time
    )

@app.get("/pipeline/status/{run_id}", response_model=PipelineStatusResponse, tags=["pipeline"])
def get_pipeline_status(run_id: str, api_key: str = Depends(get_api_key)):
    """
    Check the status of a pipeline run.
    
    This endpoint checks if the pipeline run exists and its current status.
    For completed runs, it verifies the existence of output files to confirm completion.
    """
    run_state = pipeline_runs.get(run_id)
    if not run_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run with ID '{run_id}' not found."
        )
    
    # If the run is marked as complete, verify output files exist
    if run_state.status == "COMPLETED" and run_state._output_path:
        output_path = run_state._output_path
        if not (output_path / "knowledge_graph_interactive.html").is_file() or \
           not (output_path / "pipeline_report.json").is_file():
            # This scenario indicates an inconsistency, perhaps files were deleted or not created properly
            logger.warning(f"Run {run_id} marked COMPLETED but output files missing in {output_path}. Updating status to FAILED.")
            run_state.status = "FAILED"
            run_state.errors = [ApiError(code="OUTPUT_FILES_MISSING", message="Expected output files not found.")]
            run_state.currentStage = "Verification Failed"

    return run_state

@app.get("/pipeline/results/{run_id}/visualization", response_model=PipelineVisualizationResponse, tags=["pipeline"])
async def get_pipeline_visualization(run_id: str, api_key: str = Depends(get_api_key)):
    """
    Get the interactive visualization HTML for a completed pipeline run.
    
    This endpoint returns the knowledge_graph_interactive.html file if it exists.
    """
    run_state = pipeline_runs.get(run_id)
    if not run_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run with ID '{run_id}' not found."
        )
    
    if run_state.status != "COMPLETED" or not run_state._output_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Visualization not available for run '{run_id}'. Status: {run_state.status}. Output path: {run_state._output_path}"
        )

    visualization_file = run_state._output_path / "knowledge_graph_interactive.html"
    if not visualization_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Visualization file not found for run '{run_id}' at {visualization_file}."
        )
    
    try:
        content = visualization_file.read_text()
        return PipelineVisualizationResponse(
            runId=run_id,
            visualizationType="html",
            data=content,
            description="Interactive knowledge graph visualization."
        )
    except Exception as e:
        logger.error(f"Error reading visualization file for run {run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read visualization content."
        )

@app.get("/pipeline/results/{run_id}/report", response_model=PipelineReportResponse, tags=["pipeline"])
async def get_pipeline_report(run_id: str, api_key: str = Depends(get_api_key)):
    """
    Get the pipeline execution report for a completed pipeline run.
    
    This endpoint returns the pipeline_report.json file if it exists.
    """
    run_state = pipeline_runs.get(run_id)
    if not run_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run with ID '{run_id}' not found."
        )
    
    if run_state.status != "COMPLETED" or not run_state._output_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report not available for run '{run_id}'. Status: {run_state.status}. Output path: {run_state._output_path}"
        )

    report_file = run_state._output_path / "pipeline_report.json"
    if not report_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file not found for run '{run_id}' at {report_file}."
        )
    
    try:
        content = report_file.read_text()
        import json
        report_data = json.loads(content)
        return PipelineReportResponse(
            runId=run_id,
            reportFormat="json",
            reportContent=report_data,
            generatedAt=datetime.now().isoformat() # Use current time for report generation timestamp
        )
    except json.JSONDecodeError:
        logger.error(f"Error decoding report file for run {run_id}: Invalid JSON.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse report content (invalid JSON)."
        )
    except Exception as e:
        logger.error(f"Error reading report file for run {run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read report content."
        )

@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Material Ingestion Pipeline API",
        "version": "1.0.0"
    }