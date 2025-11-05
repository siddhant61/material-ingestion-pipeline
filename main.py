#!/usr/bin/env python3
"""
Main Entry Point for Material Ingestion Pipeline

This script serves as the primary entry point for running the Material Ingestion Pipeline
using the formal MaterialIngestionPipeline orchestrator with class-based agents.

Usage:
    python main.py
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main")

# Import the pipeline and agent components
from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
from core.agents.context_agent import ContextAgent
from core.config import settings


def main():
    """
    Main function to execute the Material Ingestion Pipeline.
    
    This version runs only the course context extraction stage as the first
    step in migrating from the procedural run_enhanced_pipeline.py script.
    """
    logger.info("=" * 80)
    logger.info("Material Ingestion Pipeline - Course Context Extraction")
    logger.info("=" * 80)
    
    try:
        # Create pipeline configuration from settings
        pipeline_config = {
            "pipeline_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "version": settings.pipeline_version,
            "input_dir": str(settings.input_dir),
            "output_dir": str(settings.output_dir),
            "data_dir": str(settings.data_dir),
        }
        
        # Initialize the Material Ingestion Pipeline
        logger.info("Initializing Material Ingestion Pipeline...")
        pipeline = MaterialIngestionPipeline(config=pipeline_config)
        
        # Initialize the Context Agent with settings
        logger.info("Initializing Context Agent...")
        context_agent = ContextAgent(config=settings.to_dict())
        
        # Register the Context Agent with the pipeline
        logger.info("Registering Context Agent with pipeline...")
        pipeline.register_agent("course_context", context_agent)
        
        # Set the execution plan to run only the course context extraction
        logger.info("Setting execution plan...")
        pipeline.set_execution_plan(["course_context"])
        
        # Prepare input data
        input_data = {
            "input_dir": str(settings.input_dir),
            "course_info_path": str(settings.course_info_dir),
        }
        
        # Run the pipeline
        logger.info("Starting pipeline execution...")
        logger.info("-" * 80)
        results = pipeline.run(input_data)
        logger.info("-" * 80)
        
        # Display results
        logger.info("Pipeline execution completed!")
        logger.info(f"Status: {results['status']}")
        
        if results['status'] == 'success':
            logger.info(f"Pipeline ID: {results['pipeline_id']}")
            logger.info(f"Total execution time: {results['execution_metadata']['total_execution_time']:.2f} seconds")
            
            # Display stage outputs
            if 'course_context' in results['stage_outputs']:
                context_output = results['stage_outputs']['course_context']
                logger.info("\nCourse Context Extraction Results:")
                logger.info(f"  Status: {context_output.get('status', 'unknown')}")
                logger.info(f"  Summary: {context_output.get('summary', 'No summary available')}")
                logger.info(f"  Output file: {context_output.get('output_file', 'Not saved')}")
                
                # Display extracted course title if available
                if 'result' in context_output:
                    course_title = context_output['result'].get('title', 'Unknown')
                    logger.info(f"  Course title: {course_title}")
            
            # Save the full pipeline results
            results_file = pipeline.save_results(results)
            logger.info(f"\nFull results saved to: {results_file}")
        else:
            logger.error(f"Pipeline failed with error: {results.get('error', 'Unknown error')}")
            if 'error' in results:
                error_info = results['error']
                logger.error(f"  Stage: {error_info.get('stage', 'Unknown')}")
                logger.error(f"  Error type: {error_info.get('error_type', 'Unknown')}")
                logger.error(f"  Error message: {error_info.get('error_message', 'Unknown')}")
        
        logger.info("=" * 80)
        
        return results
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # Execute the main function
    main()
