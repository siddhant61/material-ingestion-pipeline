"""
Transcript Agent Module

This module provides the TranscriptAgent class that processes transcript files
using course context to extract structured information.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class TranscriptAgent(BaseAgent):
    """
    Agent for processing transcript files with course context.
    
    This agent processes transcript files (WebVTT format) using the course context
    to extract structured information aligned with the course structure.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Transcript Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store paths from settings
        self.transcripts_dir = settings.transcripts_dir
        self.output_dir = settings.output_dir
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for transcript processing."""
        # Models are initialized by the transcript processor
        pass
    
    def _init_memory(self):
        """Initialize memory for state tracking."""
        self.memory = {}
    
    def _init_orchestration(self):
        """Initialize orchestration components."""
        pass
    
    def _init_reasoning(self):
        """Initialize reasoning components."""
        pass
    
    def _init_tools(self):
        """Initialize tools for transcript processing."""
        # Import components here to avoid circular imports
        from core.agents.transcript_processor import TranscriptProcessor
        
        self.transcript_processor = TranscriptProcessor()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process transcript files using course context.
        
        Args:
            input_data: Input data dictionary containing:
                - previous_output: Output from the previous stage (course context)
                - result_from_course_context: Direct reference to course context
                
        Returns:
            Dictionary containing processed transcript data and metadata
        """
        logger.info("Processing transcripts with course context...")
        
        try:
            # Extract course context from input_data
            # The pipeline passes previous stage output in multiple ways
            course_context = None
            
            # Try to get course context from various possible locations
            if "result_from_course_context" in input_data:
                course_context = input_data["result_from_course_context"]
            elif "previous_output" in input_data:
                previous_output = input_data["previous_output"]
                if isinstance(previous_output, dict) and "result" in previous_output:
                    course_context = previous_output["result"]
            
            if course_context is None:
                raise ValueError("Course context not found in input_data")
            
            logger.info("Course context received from previous agent")
            
            # Get transcripts path from input or use default
            transcripts_path = input_data.get("transcripts_path", self.transcripts_dir)
            transcripts_path = Path(transcripts_path)
            
            # Run the transcript template fixer first
            logger.info("Fixing transcript template issues...")
            try:
                from core.pipeline.pipeline_fixes import fix_transcript_templates
                fix_transcript_templates()
                logger.info("Transcript template fixes completed successfully")
            except Exception as e:
                logger.warning(f"Warning: Transcript template fixes had issues: {str(e)}")
            
            # Create output directory for processed transcripts
            transcript_output_dir = self.output_dir / "transcripts"
            os.makedirs(transcript_output_dir, exist_ok=True)
            
            # Process all transcripts
            processing_results = self.transcript_processor.process_all_transcripts(
                str(transcripts_path),
                course_context,
                str(transcript_output_dir)
            )
            
            logger.info(f"Processed {processing_results['processed_count']} transcript files")
            
            if processing_results.get('error_count', 0) > 0:
                logger.warning(f"Encountered {processing_results['error_count']} errors during transcript processing")
            
            # Save overall results
            results_file = self.output_dir / "transcript_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(processing_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Transcript processing results saved to {results_file}")
            
            # Return the processing results
            return {
                "status": "success",
                "output_type": "transcript_processing",
                "result": processing_results,
                "results_file": str(results_file),
                "summary": f"Processed {processing_results['processed_count']} transcript files"
            }
            
        except Exception as e:
            logger.error(f"Error processing transcripts: {str(e)}")
            return {
                "status": "error",
                "error_type": str(type(e).__name__),
                "error_message": f"Transcript processing failed: {str(e)}",
                "summary": "Transcript processing failed"
            }
