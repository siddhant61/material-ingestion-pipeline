#!/usr/bin/env python3
"""
Material Ingestion Pipeline - Main Entry Point (Backward Compatibility Wrapper)

This module provides backward compatibility for tests and legacy code that expect
a main.py file. It wraps the production CLI (cli.py) and provides the same interface.

For new code, please use cli.py directly.
"""

import sys
import logging
from pathlib import Path

# Import the CLI components
from cli import run_pipeline, update_settings_paths, setup_sample_files

# Import configuration
from core.config import settings

# Import pipeline and agents for compatibility with existing tests
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
logger = logging.getLogger("main")


def main():
    """
    Main function - runs the complete pipeline with default settings.
    
    This function maintains backward compatibility with tests that import from main.py.
    """
    logger.info("=" * 80)
    logger.info("Material Ingestion Pipeline - Main Entry Point")
    logger.info("=" * 80)
    logger.info(f"Input Directory: {settings.input_dir}")
    logger.info(f"Output Directory: {settings.output_dir}")
    logger.info("=" * 80)
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Setup sample files if needed
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
    
    # Register Vision Agent
    vision_agent = VisionAgent()
    pipeline.register_agent("vision", vision_agent)
    logger.info("Registered VisionAgent for stage: vision")
    
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
        "vision",
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
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
