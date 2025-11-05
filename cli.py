#!/usr/bin/env python3
"""
Material Ingestion Pipeline CLI

This is the production-ready command-line interface for the Material Ingestion Pipeline.
It allows users to run the pipeline on any set of course materials by specifying
input and output directories.

Usage:
    python cli.py run-pipeline --input-dir ./my_course/ --output-dir ./my_output/
"""

import sys
import logging
from pathlib import Path
import click

# Import configuration
from core.config import settings

# Import pipeline and agents
from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
from core.agents.context_agent import ContextAgent
from core.agents.transcript_agent import TranscriptAgent
from core.agents.slide_agent import SlideAgent
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
logger = logging.getLogger("cli")


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


@click.group()
def cli():
    """Material Ingestion Pipeline - Production CLI"""
    pass


@cli.command("run-pipeline")
@click.option(
    "--input-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="Path to the directory containing course materials. Will be created with sample files if it doesn't exist."
)
@click.option(
    "--output-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help="Path to the directory where pipeline outputs will be saved. Will be created if it doesn't exist."
)
def run_pipeline(input_dir, output_dir):
    """
    Run the complete 8-stage Material Ingestion Pipeline.
    
    This command processes educational content through all pipeline stages:
    1. Course Context Extraction
    2. Transcript Processing
    3. Slide Processing
    4. Context Fusion
    5. Supervision
    6. Knowledge Graph Generation
    7. Visualization
    8. Embeddings
    
    Example:
        python cli.py run-pipeline --input-dir ./my_course/ --output-dir ./my_output/
    """
    logger.info("=" * 80)
    logger.info("Material Ingestion Pipeline - Production CLI")
    logger.info("=" * 80)
    logger.info(f"Input Directory: {input_dir}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info("=" * 80)
    
    # Update settings with user-provided paths
    # This also calls ensure_directories() which creates the required directory structure
    update_settings_paths(input_dir, output_dir)
    
    # Setup sample files if needed (directories are already created by update_settings_paths)
    setup_sample_files(settings.course_info_dir, settings.transcripts_dir)
    
    # Initialize the pipeline
    logger.info("Initializing pipeline...")
    pipeline = MaterialIngestionPipeline(config={
        "input_dir": str(settings.input_dir),
        "output_dir": str(settings.output_dir)
    })
    
    # Create and register agents
    logger.info("Registering agents...")
    
    # Register Context Agent
    context_agent = ContextAgent()
    pipeline.register_agent("course_context", context_agent)
    logger.info("Registered ContextAgent for stage: course_context")
    
    # Register Transcript Agent
    transcript_agent = TranscriptAgent()
    pipeline.register_agent("process_transcripts", transcript_agent)
    logger.info("Registered TranscriptAgent for stage: process_transcripts")
    
    # Register Slide Agent
    slide_agent = SlideAgent()
    pipeline.register_agent("process_slides", slide_agent)
    logger.info("Registered SlideAgent for stage: process_slides")
    
    # Register Fusion Agent
    fusion_agent = FusionAgent()
    pipeline.register_agent("context_fusion", fusion_agent)
    logger.info("Registered FusionAgent for stage: context_fusion")
    
    # Register Supervision Orchestrator Agent
    supervision_orchestrator_agent = SupervisionOrchestratorAgent()
    pipeline.register_agent("supervision", supervision_orchestrator_agent)
    logger.info("Registered SupervisionOrchestratorAgent for stage: supervision")
    
    # Register Knowledge Graph Agent
    knowledge_graph_agent = KnowledgeGraphAgent()
    pipeline.register_agent("knowledge_graph", knowledge_graph_agent)
    logger.info("Registered KnowledgeGraphAgent for stage: knowledge_graph")
    
    # Register Visualization Agent
    visualization_agent = VisualizationAgent()
    pipeline.register_agent("visualize", visualization_agent)
    logger.info("Registered VisualizationAgent for stage: visualize")
    
    # Register Embedding Agent
    embedding_agent = EmbeddingAgent()
    pipeline.register_agent("embeddings", embedding_agent)
    logger.info("Registered EmbeddingAgent for stage: embeddings")
    
    # Set execution plan
    execution_plan = [
        "course_context",
        "process_transcripts",
        "process_slides",
        "context_fusion",
        "supervision",
        "knowledge_graph",
        "visualize",
        "embeddings"
    ]
    pipeline.set_execution_plan(execution_plan)
    logger.info(f"Execution plan: {' -> '.join(execution_plan)}")
    
    # Run the pipeline
    logger.info("=" * 80)
    logger.info("Executing pipeline...")
    logger.info("=" * 80)
    
    results = pipeline.run()
    
    # Display results
    logger.info("=" * 80)
    logger.info("Pipeline Execution Complete")
    logger.info("=" * 80)
    logger.info(f"Status: {results['status']}")
    logger.info(f"Pipeline ID: {results['pipeline_id']}")
    
    if results["status"] == "success":
        logger.info(f"Total execution time: {results['execution_metadata']['total_execution_time']:.2f} seconds")
        logger.info("\nStage Results:")
        for stage_name, stage_output in results["stage_outputs"].items():
            summary = stage_output.get("summary", "No summary available")
            logger.info(f"  - {stage_name}: {summary}")
    else:
        logger.error(f"Pipeline failed with error: {results.get('error', {}).get('error_message', 'Unknown error')}")
    
    # Save results
    results_file = pipeline.save_results(results)
    logger.info(f"\nFull results saved to: {results_file}")
    
    # Return exit code
    exit_code = 0 if results["status"] == "success" else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
