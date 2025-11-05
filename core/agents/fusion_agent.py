"""
Fusion Agent Module

This module provides the FusionAgent class that fuses outputs from multiple
data ingestion agents (ContextAgent, TranscriptAgent, SlideAgent) into a
unified context representation.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.config import settings
from core.agents.context_fusion import ContextFusion

# Configure logging
logger = logging.getLogger(__name__)


class FusionAgent(BaseAgent):
    """
    Agent for fusing multiple content sources into a unified context.
    
    This agent processes outputs from:
    - ContextAgent (course context)
    - TranscriptAgent (transcript data)
    - SlideAgent (slide data)
    
    It combines these sources into a fused context representation suitable for
    knowledge graph construction.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Fusion Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store output directory from settings
        self.output_dir = settings.output_dir
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for context fusion."""
        # Models are initialized by the context fusion component if needed
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
        """Initialize tools for context fusion."""
        self.context_fusion = ContextFusion()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuse outputs from all previous agents into a unified context.
        
        Args:
            input_data: Input data dictionary containing:
                - result_from_course_context: Course context from ContextAgent
                - result_from_process_transcripts: Transcript data from TranscriptAgent
                - result_from_process_slides: Slide data from SlideAgent
                
        Returns:
            Dictionary containing fused context and metadata
        """
        logger.info("Generating fused context from all data sources...")
        
        try:
            # Extract results from all previous agents
            # These keys are set by the pipeline's _prepare_next_stage_input method
            course_context = input_data.get("result_from_course_context")
            transcript_data = input_data.get("result_from_process_transcripts")
            slide_data = input_data.get("result_from_process_slides")
            
            # Validate that we received all required inputs
            if course_context is None:
                raise ValueError("Course context not found in input_data (result_from_course_context)")
            if transcript_data is None:
                raise ValueError("Transcript data not found in input_data (result_from_process_transcripts)")
            if slide_data is None:
                raise ValueError("Slide data not found in input_data (result_from_process_slides)")
            
            logger.info("All input data received from previous agents")
            logger.info(f"Course context keys: {list(course_context.keys()) if isinstance(course_context, dict) else type(course_context)}")
            logger.info(f"Transcript data keys: {list(transcript_data.keys()) if isinstance(transcript_data, dict) else type(transcript_data)}")
            logger.info(f"Slide data keys: {list(slide_data.keys()) if isinstance(slide_data, dict) else type(slide_data)}")
            
            # Create a temporary directory for input files
            temp_dir = self.output_dir / "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save input data to temporary files for the ContextFusion component
            course_context_path = temp_dir / "course_context.json"
            transcript_data_path = temp_dir / "transcript_data.json"
            slide_data_path = temp_dir / "slide_data.json"
            
            with open(course_context_path, 'w', encoding='utf-8') as f:
                json.dump(course_context, f, ensure_ascii=False, indent=2)
            
            with open(transcript_data_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            with open(slide_data_path, 'w', encoding='utf-8') as f:
                json.dump(slide_data, f, ensure_ascii=False, indent=2)
            
            logger.info("Temporary input files created for ContextFusion")
            
            # Load the data into the ContextFusion component
            load_success = self.context_fusion.load_data(
                str(course_context_path),
                str(transcript_data_path),
                str(slide_data_path)
            )
            
            if not load_success:
                raise RuntimeError("Failed to load data into ContextFusion component")
            
            logger.info("Data loaded into ContextFusion component")
            
            # Generate the fused context
            fused_context_dir = self.output_dir / "fused_context"
            os.makedirs(fused_context_dir, exist_ok=True)
            
            # Call generate_fused_context with the output directory
            fused_context = self.context_fusion.generate_fused_context(str(fused_context_dir))
            
            # Save the fused context
            fused_context_file = fused_context_dir / "fused_context.json"
            
            with open(fused_context_file, 'w', encoding='utf-8') as f:
                json.dump(fused_context, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Fused context generated and saved to {fused_context_file}")
            
            # Return the fused context as the result
            return {
                "status": "success",
                "output_type": "fused_context",
                "result": fused_context,
                "fused_context_file": str(fused_context_file),
                "summary": f"Generated fused context with {fused_context.get('statistics', {}).get('concept_count', 0)} concepts"
            }
            
        except ValueError as e:
            logger.error(f"Missing required input data: {str(e)}")
            return {
                "status": "error",
                "output_type": "fused_context",
                "error_message": str(e),
                "summary": f"Failed to generate fused context: {str(e)}"
            }
        
        except Exception as e:
            logger.error(f"Error generating fused context: {str(e)}")
            return {
                "status": "error",
                "output_type": "fused_context",
                "error_message": str(e),
                "summary": f"Failed to generate fused context: {str(e)}"
            }
