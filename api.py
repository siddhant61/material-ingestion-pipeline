#!/usr/bin/env python3
"""
Material Ingestion Pipeline API

FastAPI server that exposes the Material Ingestion Pipeline over HTTP.
This serves as the backend for the future User Interface.

Usage:
    uvicorn api:app --reload
    
    # To start a pipeline run:
    curl -X POST http://localhost:8000/run \
         -H "Content-Type: application/json" \
         -d '{"input_dir": "./my_course/", "output_dir": "./my_output/"}'
"""

import os
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Import configuration
from core.config import settings

# Import pipeline and agents
from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
from core.agents.context_agent import ContextAgent
from core.agents.transcript_agent import TranscriptAgent
from core.agents.slide_agent import SlideAgent
from core.agents.vision_agent import VisionAgent
from core.agents.fusion_agent import FusionAgent
from core.agents.supervision_orchestrator_agent import SupervisionOrchestratorAgent
from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
from core.agents.visualization_agent import VisualizationAgent
from core.agents.embedding_agent import EmbeddingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

# Initialize FastAPI app
app = FastAPI(
    title="Material Ingestion Pipeline API",
    description="API for running the Material Ingestion Pipeline on educational content",
    version="1.0.0"
)

# Store active pipeline runs
active_runs = {}


# ================================================================================
# API Models
# ================================================================================

class PipelineRunRequest(BaseModel):
    """Request model for starting a pipeline run."""
    input_dir: str = Field(..., description="Path to the directory containing course materials")
    output_dir: str = Field(..., description="Path to the directory where pipeline outputs will be saved")


class PipelineRunResponse(BaseModel):
    """Response model for pipeline run initiation."""
    run_id: str = Field(..., description="Unique identifier for this pipeline run")
    message: str = Field(..., description="Status message")
    input_dir: str = Field(..., description="Input directory being processed")
    output_dir: str = Field(..., description="Output directory for results")


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status check."""
    run_id: str = Field(..., description="Unique identifier for this pipeline run")
    status: str = Field(..., description="Current status: 'running', 'complete', or 'error'")
    message: str = Field(..., description="Status message")
    output_dir: Optional[str] = Field(None, description="Output directory for results")


# ================================================================================
# Helper Functions
# ================================================================================

def setup_sample_files(course_info_dir, transcripts_dir):
    """Create sample files if no course material files exist."""
    logger.info("Checking for course material files...")
    
    # Check if course info directory is empty
    course_info_files = list(course_info_dir.glob("*"))
    if not course_info_files:
        logger.warning("No course info files found. Creating a sample file.")
        
        # Create a sample course info file
        sample_course_info = """# Quantum Computing Basics
## Course Overview
This course introduces the fundamentals of quantum computing, from basic quantum mechanics to quantum algorithms.

## Learning Objectives
- Understand quantum bits (qubits) and quantum gates
- Learn about quantum superposition and entanglement
- Explore simple quantum algorithms

## Course Structure
1. Introduction to Quantum Computing
2. Quantum Bits and Gates
3. Quantum Algorithms
4. Applications of Quantum Computing
"""
        with open(course_info_dir / "course_info.md", "w", encoding="utf-8") as f:
            f.write(sample_course_info)
        
        logger.info(f"Created sample course info file at {course_info_dir / 'course_info.md'}")
    
    # Check if transcripts directory is empty
    transcript_files = list(transcripts_dir.glob("*"))
    if not transcript_files:
        logger.warning("No transcript files found. Creating a sample file.")
        
        # Create a sample transcript file in WebVTT format
        sample_transcript = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello and welcome to the first lecture on Quantum Computing Basics.

00:00:05.100 --> 00:00:10.000
In this course, we'll explore the fascinating world of quantum computing.

00:00:10.100 --> 00:00:15.000
Let's start by understanding what makes quantum computing different from classical computing.

00:00:15.100 --> 00:00:20.000
The fundamental unit of quantum information is the qubit, which can exist in a superposition of states.

00:00:20.100 --> 00:00:25.000
Unlike classical bits that can only be 0 or 1, qubits can be both 0 and 1 simultaneously.

00:00:25.100 --> 00:00:30.000
This property gives quantum computers their potential for exponential processing power.
"""
        with open(transcripts_dir / "1.1 Introduction to Quantum Computing.txt", "w", encoding="utf-8") as f:
            f.write(sample_transcript)
        
        logger.info(f"Created sample transcript file at {transcripts_dir / '1.1 Introduction to Quantum Computing.txt'}")


def update_settings_paths(input_dir_str, output_dir_str):
    """
    Update the global settings object with new input and output directories.
    
    This function overrides all path-related settings to point to the user-specified
    directories, making the pipeline portable.
    """
    input_dir = Path(input_dir_str).resolve()
    output_dir = Path(output_dir_str).resolve()
    
    # Update base directories
    settings.input_dir = input_dir
    settings.output_dir = output_dir
    settings.data_dir = output_dir / "data"
    
    # Update course material directories (relative to input_dir)
    settings.course_info_dir = input_dir / "course_material" / "course_info"
    settings.transcripts_dir = input_dir / "course_material" / "transcripts"
    settings.slides_dir = input_dir / "course_material" / "slides"
    
    # Update output directories (relative to output_dir)
    settings.course_context_dir = output_dir / "course_context"
    settings.transcripts_output_dir = output_dir / "transcripts"
    settings.slides_output_dir = output_dir / "slides"
    settings.knowledge_graph_dir = output_dir / "knowledge_graph"
    
    # Ensure all directories exist
    settings.ensure_directories()
    
    logger.info(f"Updated settings: input_dir={input_dir}, output_dir={output_dir}")


def run_pipeline_in_background(run_id: str, input_dir: str, output_dir: str):
    """
    Run the complete Material Ingestion Pipeline in the background.
    
    This function contains the entire pipeline setup logic from cli.py and runs
    the pipeline asynchronously to avoid HTTP timeouts.
    
    Args:
        run_id: Unique identifier for this pipeline run
        input_dir: Path to the directory containing course materials
        output_dir: Path to the directory where pipeline outputs will be saved
    """
    try:
        logger.info(f"[{run_id}] Starting pipeline run")
        logger.info(f"[{run_id}] Input Directory: {input_dir}")
        logger.info(f"[{run_id}] Output Directory: {output_dir}")
        
        # Update active runs status
        active_runs[run_id]["status"] = "running"
        active_runs[run_id]["message"] = "Pipeline is processing..."
        
        # Update settings with user-provided paths
        update_settings_paths(input_dir, output_dir)
        
        # Setup sample files if needed
        setup_sample_files(settings.course_info_dir, settings.transcripts_dir)
        
        # Initialize the pipeline
        logger.info(f"[{run_id}] Initializing pipeline...")
        pipeline = MaterialIngestionPipeline(config={
            "input_dir": str(settings.input_dir),
            "output_dir": str(settings.output_dir)
        })
        
        # Create and register agents
        logger.info(f"[{run_id}] Registering agents...")
        
        # Register Context Agent
        context_agent = ContextAgent()
        pipeline.register_agent("course_context", context_agent)
        
        # Register Transcript Agent
        transcript_agent = TranscriptAgent()
        pipeline.register_agent("process_transcripts", transcript_agent)
        
        # Register Slide Agent
        slide_agent = SlideAgent()
        pipeline.register_agent("process_slides", slide_agent)
        
        # Register Vision Agent
        vision_agent = VisionAgent()
        pipeline.register_agent("vision", vision_agent)
        
        # Register Fusion Agent
        fusion_agent = FusionAgent()
        pipeline.register_agent("context_fusion", fusion_agent)
        
        # Register Supervision Orchestrator Agent
        supervision_orchestrator_agent = SupervisionOrchestratorAgent()
        pipeline.register_agent("supervision", supervision_orchestrator_agent)
        
        # Register Knowledge Graph Agent
        knowledge_graph_agent = KnowledgeGraphAgent()
        pipeline.register_agent("knowledge_graph", knowledge_graph_agent)
        
        # Register Visualization Agent
        visualization_agent = VisualizationAgent()
        pipeline.register_agent("visualize", visualization_agent)
        
        # Register Embedding Agent
        embedding_agent = EmbeddingAgent()
        pipeline.register_agent("embeddings", embedding_agent)
        
        # Set execution plan
        execution_plan = [
            "course_context",
            "process_transcripts",
            "process_slides",
            "vision",
            "context_fusion",
            "supervision",
            "knowledge_graph",
            "visualize",
            "embeddings"
        ]
        pipeline.set_execution_plan(execution_plan)
        
        # Run the pipeline
        logger.info(f"[{run_id}] Executing pipeline...")
        results = pipeline.run()
        
        # Save results
        results_file = pipeline.save_results(results)
        logger.info(f"[{run_id}] Results saved to: {results_file}")
        
        # Update active runs status
        if results["status"] == "success":
            active_runs[run_id]["status"] = "complete"
            active_runs[run_id]["message"] = "Pipeline completed successfully"
            logger.info(f"[{run_id}] Pipeline execution completed successfully")
        else:
            active_runs[run_id]["status"] = "error"
            active_runs[run_id]["message"] = f"Pipeline failed: {results.get('error', {}).get('error_message', 'Unknown error')}"
            logger.error(f"[{run_id}] Pipeline execution failed")
            
    except Exception as e:
        logger.error(f"[{run_id}] Pipeline execution failed with exception: {str(e)}", exc_info=True)
        active_runs[run_id]["status"] = "error"
        active_runs[run_id]["message"] = f"Pipeline failed with exception: {str(e)}"


# ================================================================================
# API Endpoints
# ================================================================================

@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "name": "Material Ingestion Pipeline API",
        "version": "1.0.0",
        "description": "API for running the Material Ingestion Pipeline on educational content",
        "endpoints": {
            "POST /run": "Start a new pipeline run",
            "GET /status/{run_id}": "Check the status of a pipeline run",
            "GET /results/{run_id}/visualization": "Get the interactive visualization HTML",
            "GET /results/{run_id}/report": "Get the pipeline execution report"
        }
    }


@app.post("/run", response_model=PipelineRunResponse)
async def start_pipeline_run(request: PipelineRunRequest, background_tasks: BackgroundTasks):
    """
    Start a new pipeline run asynchronously.
    
    This endpoint accepts input and output directories, generates a unique run ID,
    and starts the pipeline execution in the background using FastAPI's BackgroundTasks.
    
    The pipeline runs asynchronously to avoid HTTP timeouts, as it can take several
    minutes to complete.
    
    Args:
        request: PipelineRunRequest with input_dir and output_dir
        background_tasks: FastAPI BackgroundTasks for async execution
        
    Returns:
        PipelineRunResponse with run_id and status message
    """
    # Generate a unique run ID (timestamp-based UUID)
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    # Validate directories exist or can be created
    input_dir = Path(request.input_dir)
    output_dir = Path(request.output_dir)
    
    logger.info(f"Received pipeline run request: run_id={run_id}, input_dir={input_dir}, output_dir={output_dir}")
    
    # Store run information
    active_runs[run_id] = {
        "run_id": run_id,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "status": "initializing",
        "message": "Pipeline run has been queued",
        "started_at": datetime.now().isoformat()
    }
    
    # Add the pipeline run to background tasks
    background_tasks.add_task(run_pipeline_in_background, run_id, str(input_dir), str(output_dir))
    
    logger.info(f"Pipeline run {run_id} has been queued for execution")
    
    return PipelineRunResponse(
        run_id=run_id,
        message="Pipeline run started. Use the run_id to check status.",
        input_dir=str(input_dir),
        output_dir=str(output_dir)
    )


@app.get("/status/{run_id}", response_model=PipelineStatusResponse)
def get_pipeline_status(run_id: str):
    """
    Check the status of a pipeline run.
    
    This endpoint checks if the pipeline run exists and its current status.
    For completed runs, it verifies the existence of output files to confirm completion.
    
    Args:
        run_id: The unique identifier of the pipeline run
        
    Returns:
        PipelineStatusResponse with current status
        
    Raises:
        HTTPException: If the run_id is not found
    """
    # Check if run exists in active runs
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")
    
    run_info = active_runs[run_id]
    output_dir = Path(run_info["output_dir"])
    
    # Check for completion indicators
    knowledge_graph_file = output_dir / "knowledge_graph" / "knowledge_graph.json"
    pipeline_report_file = output_dir / "pipeline_report.json"
    
    # Determine status based on file existence
    current_status = run_info["status"]
    
    if current_status == "running":
        # Double-check if files exist (pipeline might have completed)
        if knowledge_graph_file.exists() or pipeline_report_file.exists():
            current_status = "complete"
            run_info["status"] = "complete"
            run_info["message"] = "Pipeline completed successfully"
    
    logger.info(f"Status check for {run_id}: {current_status}")
    
    return PipelineStatusResponse(
        run_id=run_id,
        status=current_status,
        message=run_info["message"],
        output_dir=run_info["output_dir"]
    )


@app.get("/results/{run_id}/visualization")
async def get_pipeline_visualization(run_id: str):
    """
    Get the interactive visualization HTML for a completed pipeline run.
    
    This endpoint returns the knowledge_graph_interactive.html file if it exists.
    
    Args:
        run_id: The unique identifier of the pipeline run
        
    Returns:
        HTMLResponse with the visualization content
        
    Raises:
        HTTPException: If the run_id is not found or visualization is not available
    """
    # Check if run exists
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")
    
    run_info = active_runs[run_id]
    output_dir = Path(run_info["output_dir"])
    
    # Check for visualization file
    visualization_file = output_dir / "visualizations" / "knowledge_graph_interactive.html"
    
    if not visualization_file.exists():
        # Check if pipeline is still running
        if run_info["status"] == "running":
            raise HTTPException(
                status_code=202,
                detail="Pipeline is still running. Visualization not yet available."
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Visualization file not found. Pipeline may have failed or not completed yet."
            )
    
    logger.info(f"Serving visualization for {run_id}")
    
    # Read and return the HTML file
    with open(visualization_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)


@app.get("/results/{run_id}/report")
async def get_pipeline_report(run_id: str):
    """
    Get the pipeline execution report for a completed pipeline run.
    
    This endpoint returns the pipeline_report.json file if it exists.
    
    Args:
        run_id: The unique identifier of the pipeline run
        
    Returns:
        JSONResponse with the report content
        
    Raises:
        HTTPException: If the run_id is not found or report is not available
    """
    # Check if run exists
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")
    
    run_info = active_runs[run_id]
    output_dir = Path(run_info["output_dir"])
    
    # Check for report file
    report_file = output_dir / "pipeline_report.json"
    
    if not report_file.exists():
        # Check if pipeline is still running
        if run_info["status"] == "running":
            raise HTTPException(
                status_code=202,
                detail="Pipeline is still running. Report not yet available."
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Report file not found. Pipeline may have failed or not completed yet."
            )
    
    logger.info(f"Serving report for {run_id}")
    
    # Return the JSON file as response
    return FileResponse(
        path=report_file,
        media_type="application/json",
        filename=f"pipeline_report_{run_id}.json"
    )


# ================================================================================
# Health Check
# ================================================================================

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Material Ingestion Pipeline API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
