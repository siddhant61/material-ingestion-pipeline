#!/usr/bin/env python3
"""
Main Entry Point for Material Ingestion Pipeline

This script runs the modular material ingestion pipeline using the
MaterialIngestionPipeline orchestrator with registered agents.

Usage:
    python main.py
"""

import os
import sys
import logging
from pathlib import Path

# Import configuration
from core.config import settings

# Import pipeline and agents
from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
from core.agents.context_agent import ContextAgent
from core.agents.transcript_agent import TranscriptAgent
from core.agents.slide_agent import SlideAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")


def setup_sample_files():
    """Create sample files if no course material files exist."""
    logger.info("Checking for course material files...")
    
    course_info_dir = settings.course_info_dir
    transcripts_dir = settings.transcripts_dir
    
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


def main():
    """Main execution function."""
    logger.info("Starting Material Ingestion Pipeline")
    logger.info("=" * 80)
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Setup sample files if needed
    setup_sample_files()
    
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
    
    # Set execution plan
    execution_plan = ["course_context", "process_transcripts", "process_slides"]
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
    return 0 if results["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
