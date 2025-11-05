"""
Slide Agent Module

This module provides the SlideAgent class that processes slide files
using both course context and transcript data to extract structured information.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.config import settings
from core.agents.slide_processor import SlideProcessor

# Configure logging
logger = logging.getLogger(__name__)


class SlideAgent(BaseAgent):
    """
    Agent for processing slide files with course context and transcript data.
    
    This agent processes slide files (PDF format) using both the course context
    and transcript data to extract structured information aligned with the course structure.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Slide Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store paths from settings
        self.slides_dir = settings.slides_dir
        self.output_dir = settings.output_dir
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for slide processing."""
        # Models are initialized by the slide processor
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
        """Initialize tools for slide processing."""
        self.slide_processor = SlideProcessor()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process slide files using course context and transcript data.
        
        Args:
            input_data: Input data dictionary containing:
                - result_from_course_context: Course context from ContextAgent
                - result_from_process_transcripts: Transcript data from TranscriptAgent
                
        Returns:
            Dictionary containing processed slide data and metadata
        """
        logger.info("Processing slides with course context and transcript data...")
        
        try:
            # Extract course context from input_data
            course_context = input_data.get("result_from_course_context")
            if course_context is None:
                raise ValueError("Course context not found in input_data")
            
            logger.info("Course context received from pipeline")
            
            # Extract transcript data from input_data
            transcript_data = input_data.get("result_from_process_transcripts")
            if transcript_data is None:
                raise ValueError("Transcript data not found in input_data")
            
            logger.info("Transcript data received from pipeline")
            
            # Get slides path from input or use default
            slides_path = input_data.get("slides_path", self.slides_dir)
            slides_path = Path(slides_path)
            
            # Create output directory for processed slides
            slide_output_dir = self.output_dir / "slides"
            os.makedirs(slide_output_dir, exist_ok=True)
            
            # First check if we need to install dependencies
            try:
                import pypdf
                import fitz  # PyMuPDF
            except ImportError:
                logger.warning("Missing slide processor dependencies. Attempting to install...")
                import subprocess
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf", "PyMuPDF"])
                    logger.info("Successfully installed slide processor dependencies")
                except Exception as e:
                    logger.error(f"Failed to install dependencies: {str(e)}")
                    return {
                        "status": "error",
                        "error_type": "DependencyError",
                        "error_message": f"Could not process slides: missing dependencies (pypdf, PyMuPDF). Error: {str(e)}",
                        "summary": "Slide processing failed due to missing dependencies"
                    }
            
            # Process all slides
            processing_results = self.slide_processor.process_all_slides(
                str(slides_path),
                course_context,
                transcript_data,
                str(slide_output_dir)
            )
            
            logger.info(f"Processed {processing_results.get('processed_count', 0)} slide files")
            
            if processing_results.get('error_count', 0) > 0:
                logger.warning(f"Encountered {processing_results['error_count']} errors during slide processing")
            
            # Save overall results
            results_file = self.output_dir / "slide_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(processing_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Slide processing results saved to {results_file}")
            
            # Return the processing results
            return {
                "status": "success",
                "output_type": "slide_processing",
                "result": processing_results,
                "results_file": str(results_file),
                "summary": f"Processed {processing_results['processed_count']} slide files"
            }
            
        except Exception as e:
            logger.error(f"Error processing slides: {str(e)}")
            return {
                "status": "error",
                "error_type": str(type(e).__name__),
                "error_message": f"Slide processing failed: {str(e)}",
                "summary": "Slide processing failed"
            }
