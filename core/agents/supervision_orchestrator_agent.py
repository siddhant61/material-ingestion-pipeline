"""
Supervision Orchestrator Agent Module

This module provides the SupervisionOrchestratorAgent class that wraps
the existing SupervisorAgent functionality into the modular pipeline architecture.

The agent orchestrates quality control and consistency enforcement across all
previous pipeline stages by delegating to the SupervisorAgent.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.agents.supervisor import SupervisorAgent
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class SupervisionOrchestratorAgent(BaseAgent):
    """
    Orchestrator agent for supervising and refining outputs from previous pipeline stages.
    
    This agent wraps the SupervisorAgent functionality and integrates it with the
    MaterialIngestionPipeline orchestrator. It processes outputs from:
    - ContextAgent (course_context)
    - TranscriptAgent (process_transcripts)
    - SlideAgent (process_slides)
    - FusionAgent (context_fusion)
    
    The agent performs quality checks, consistency validation, and optional refinement
    on each stage's output.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Supervision Orchestrator Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store output directory from settings
        self.output_dir = settings.output_dir / "supervision"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for supervision."""
        # Models are initialized by the SupervisorAgent
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
        """Initialize the SupervisorAgent tool."""
        # Initialize the SupervisorAgent once for efficiency
        self.supervisor = SupervisorAgent({
            "output_dir": str(self.output_dir)
        })
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for the supervision agent.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if the input is valid, False otherwise
        """
        # Input must be a dictionary (checked by base class)
        if not super().validate_input(input_data):
            return False
        
        # At least one result from previous stages should be present
        has_results = any(
            key in input_data for key in [
                "result_from_course_context",
                "result_from_process_transcripts",
                "result_from_process_slides",
                "result_from_context_fusion"
            ]
        )
        
        return has_results
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate the output data from the supervision agent.
        
        Args:
            output_data: Output data to validate
            
        Returns:
            True if the output is valid, False otherwise
        """
        # Output must be a dictionary (checked by base class)
        if not super().validate_output(output_data):
            return False
        
        # Output must have required keys
        required_keys = ["status", "result", "summary", "output_type"]
        return all(key in output_data for key in required_keys)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Supervise and refine outputs from all previous pipeline stages.
        
        Args:
            input_data: Input data dictionary containing:
                - result_from_course_context: Course context from ContextAgent
                - result_from_process_transcripts: Transcript data from TranscriptAgent
                - result_from_process_slides: Slide data from SlideAgent
                - result_from_context_fusion: Fused context from FusionAgent
                
        Returns:
            Dictionary containing supervised and refined outputs
        """
        logger.info("Starting supervision orchestration...")
        
        try:
            # Gather all previous results from input_data
            agent_outputs = {}
            
            # Collect results from each previous stage
            if "result_from_course_context" in input_data:
                agent_outputs["course_context"] = input_data["result_from_course_context"]
                logger.info("Found course_context output for supervision")
            
            if "result_from_process_transcripts" in input_data:
                agent_outputs["transcript_processor"] = input_data["result_from_process_transcripts"]
                logger.info("Found process_transcripts output for supervision")
            
            if "result_from_process_slides" in input_data:
                agent_outputs["slide_processor"] = input_data["result_from_process_slides"]
                logger.info("Found process_slides output for supervision")
            
            if "result_from_context_fusion" in input_data:
                agent_outputs["context_fusion"] = input_data["result_from_context_fusion"]
                logger.info("Found context_fusion output for supervision")
            
            if not agent_outputs:
                logger.warning("No agent outputs found for supervision")
                return {
                    "status": "success",
                    "result": {},
                    "summary": "No outputs to supervise",
                    "output_type": "supervision_results"
                }
            
            logger.info(f"Supervising {len(agent_outputs)} agent outputs...")
            
            # Process each agent's output
            refined_outputs = {}
            supervision_results = {}
            
            for agent_name, content in agent_outputs.items():
                try:
                    logger.info(f"Supervising output from {agent_name}...")
                    
                    # Validate and wrap non-dictionary content (defensive measure matching original implementation)
                    if not isinstance(content, dict):
                        logger.warning(f"Content from {agent_name} is not a dictionary, wrapping it")
                        if content is None:
                            content = {"data": "empty_content"}
                        else:
                            content = {"data": content}
                    
                    # Supervise the agent output using the initialized supervisor
                    result = self.supervisor.supervise(
                        agent_name=agent_name,
                        content=content,
                        auto_refine=True
                    )
                    
                    # Store the result
                    refined_outputs[agent_name] = result.get("refined_content", content)
                    supervision_results[agent_name] = result
                    
                    logger.info(f"Supervision completed for {agent_name}")
                    
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error supervising {agent_name}: {str(json_error)}")
                    refined_outputs[agent_name] = content  # Use original content on error
                    supervision_results[agent_name] = {
                        "error": f"JSON parsing error: {str(json_error)}",
                        "agent_name": agent_name,
                        "refined_content": content
                    }
                    
                except Exception as e:
                    logger.error(f"Error supervising {agent_name}: {str(e)}")
                    refined_outputs[agent_name] = content  # Use original content on error
                    supervision_results[agent_name] = {
                        "error": str(e),
                        "agent_name": agent_name,
                        "refined_content": content
                    }
            
            # Generate timestamp once for both purposes
            timestamp_iso = datetime.now().isoformat()
            timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save all supervision results
            combined_results = {
                "refined_outputs": refined_outputs,
                "supervision_results": supervision_results,
                "timestamp": timestamp_iso
            }
            
            # Use timestamp to avoid conflicts in concurrent executions
            supervision_results_file = self.output_dir / f"supervision_results_{timestamp_file}.json"
            with open(supervision_results_file, 'w', encoding='utf-8') as f:
                json.dump(combined_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"All supervision results saved to {supervision_results_file}")
            
            # Return refined outputs in the format expected by the pipeline
            return {
                "status": "success",
                "result": refined_outputs,
                "summary": f"Supervised {len(agent_outputs)} agent outputs",
                "output_type": "supervision_results",
                "supervision_metadata": {
                    "agents_supervised": list(agent_outputs.keys()),
                    "supervision_timestamp": timestamp_iso,
                    "results_file": str(supervision_results_file)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in supervision orchestration: {str(e)}")
            # On error, return original outputs if available
            return {
                "status": "error",
                "error_message": str(e),
                "result": input_data.get("result_from_context_fusion", {}),
                "summary": f"Supervision failed: {str(e)}",
                "output_type": "supervision_results"
            }
