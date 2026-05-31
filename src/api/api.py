import uuid
import asyncio
import logging
from typing import Dict
from datetime import datetime, timezone

from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Depends

from src.api.models import (
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineStatusResponse,
    PipelineReportResponse,
    ErrorResponse,
    HealthCheckResponse,
    UUIDStr
)
from src.api.dependencies import authenticate_user
from src.core.db import PipelineRun, get_db, init_db # Import DB models and session
from sqlalchemy.ext.asyncio import AsyncSession

# --- FastAPI Application Setup ---

app = FastAPI(
    title="Material Ingestion Pipeline API",
    description="API for managing and monitoring the material ingestion pipeline.",
    version="1.0.0",
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}, 404: {"model": ErrorResponse, "description": "Not Found"}}
)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add startup event to initialize DB
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")

# --- Background Task for Pipeline Execution ---
async def run_pipeline_in_background(pipeline_id: str, material_id: str, config: Dict, db_session: AsyncSession):
    """
    Placeholder for the actual pipeline execution logic.
    Simulates a long-running process with status updates.
    """
    logger.info(f"Starting background pipeline run {pipeline_id} for material {material_id} with config {config}")

    # Fetch the pipeline run from DB
    pipeline_run = await db_session.get(PipelineRun, pipeline_id)
    if not pipeline_run:
        logger.error(f"Error: Pipeline run {pipeline_id} not found in DB for background task.")
        return

    pipeline_run.status = "running"
    pipeline_run.progress = 0.0
    pipeline_run.start_time = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(pipeline_run)

    try:
        # Simulate work
        for i in range(1, 11):
            await asyncio.sleep(0.5) # Simulate async I/O or computation
            pipeline_run.progress = i * 10.0
            await db_session.commit() # Commit progress updates
            await db_session.refresh(pipeline_run)
            logger.debug(f"Pipeline {pipeline_id} progress: {i*10}%")

        pipeline_run.status = "completed"
        pipeline_run.report_url = f"/pipeline/{pipeline_id}/report"
        pipeline_run.end_time = datetime.now(timezone.utc)
        await db_session.commit()
        logger.info(f"Pipeline {pipeline_id} completed.")
    except Exception as e:
        pipeline_run.status = "failed"
        pipeline_run.error_details = str(e)
        pipeline_run.end_time = datetime.now(timezone.utc)
        await db_session.commit()
        logger.error(f"Pipeline {pipeline_id} failed with error: {e}", exc_info=True)

# --- API Endpoints ---

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    # In a real application, this would check database connection, external services, etc.
    return HealthCheckResponse(
        status="ok",
        message="API is running",
        timestamp=datetime.now(timezone.utc),
        dependencies={
            "database": "ok" # Placeholder, would check actual DB connection
        }
    )

@app.post("/pipeline/run", response_model=PipelineRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_pipeline_run(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(authenticate_user),
    db_session: AsyncSession = Depends(get_db)
):
    # Create a new pipeline run entry in the database
    new_pipeline_run = PipelineRun(
        material_id=request.material_id,
        config=request.config,
        status="pending",
        progress=0.0
    )
    db_session.add(new_pipeline_run)
    await db_session.commit()
    await db_session.refresh(new_pipeline_run) # Get the generated pipeline_id

    background_tasks.add_task(
        run_pipeline_in_background,
        pipeline_id=new_pipeline_run.pipeline_id, # This is a string from DB
        material_id=request.material_id,
        config=request.config,
        db_session=db_session # Pass the session to the background task
    )

    return PipelineRunResponse(
        pipeline_id=new_pipeline_run.pipeline_id, # This is already a string
        status="initiated",
        message="Pipeline run initiated successfully"
    )

@app.get("/pipeline/{pipeline_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    pipeline_id: UUIDStr, # Expect UUID as string
    current_user: str = Depends(authenticate_user),
    db_session: AsyncSession = Depends(get_db)
):
    pipeline_run = await db_session.get(PipelineRun, pipeline_id) # Query DB with string UUID
    if not pipeline_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")

    return PipelineStatusResponse(
        pipeline_id=pipeline_run.pipeline_id,
        status=pipeline_run.status,
        progress=pipeline_run.progress,
        report_url=pipeline_run.report_url,
        error_details=pipeline_run.error_details
    )

@app.get("/pipeline/{pipeline_id}/visualization", response_model=Dict)
async def get_pipeline_visualization(
    pipeline_id: UUIDStr, # Expect UUID as string
    current_user: str = Depends(authenticate_user),
    db_session: AsyncSession = Depends(get_db)
):
    pipeline_run = await db_session.get(PipelineRun, pipeline_id)
    if not pipeline_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")

    # Placeholder for actual visualization logic
    return {"pipeline_id": pipeline_id, "visualization_data": "Graph representation of pipeline stages"}

@app.get("/pipeline/{pipeline_id}/report", response_model=PipelineReportResponse)
async def get_pipeline_report(
    pipeline_id: UUIDStr, # Expect UUID as string
    current_user: str = Depends(authenticate_user),
    db_session: AsyncSession = Depends(get_db)
):
    pipeline_run = await db_session.get(PipelineRun, pipeline_id)
    if not pipeline_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")

    if pipeline_run.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline run {pipeline_id} is not yet completed. Current status: {pipeline_run.status}"
        )

    # Placeholder for actual report generation logic
    return PipelineReportResponse(
        pipeline_id=pipeline_id,
        report_data={
            "summary": f"Report for material {pipeline_run.material_id}",
            "stages_completed": ["data_load", "processing", "analysis"],
            "metrics": {"duration_seconds": (pipeline_run.end_time - pipeline_run.start_time).total_seconds() if pipeline_run.end_time and pipeline_run.start_time else 0}
        },
        generated_at=datetime.now(timezone.utc)
    )
