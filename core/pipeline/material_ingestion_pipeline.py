"""
Material Ingestion Pipeline

This module provides the MaterialIngestionPipeline class, which orchestrates the entire
workflow for ingesting educational materials and creating a knowledge graph.

The pipeline coordinates the execution of multiple agents in a defined sequence,
handling data flow between agents, error management, and progress tracking.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Type
from pathlib import Path

from core.agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

class MaterialIngestionPipeline:
    """
    Orchestrates the material ingestion pipeline from input materials to knowledge graph.
    
    This pipeline manages the workflow of processing educational materials through a 
    series of specialized agents, including:
    - Document Loader Agent
    - Transcript Agent
    - Context Extraction Agent
    - Vision Model Agent
    - Targeted Image Extraction Agent
    - Embedding Agent
    - Concept Extraction Agent
    - Graph Builder Agent
    
    The pipeline handles agent registration, execution sequencing, data passing,
    error management, and result aggregation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Material Ingestion Pipeline.
        
        Args:
            config (Dict[str, Any], optional): Pipeline configuration
        """
        # Initialize configuration with defaults
        self.config = config or {}
        
        # Set pipeline properties
        self.pipeline_id = self.config.get("pipeline_id", datetime.now().strftime("%Y%m%d%H%M%S"))
        self.version = self.config.get("version", "1.0.0")
        
        # Set I/O directories
        self.input_dir = Path(self.config.get("input_dir", "input"))
        self.output_dir = Path(self.config.get("output_dir", "output"))
        self.data_dir = Path(self.config.get("data_dir", "data"))
        
        # Ensure directories exist
        self.input_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize agent registry and execution plan
        self.agents = {}
        self.execution_plan = self.config.get("execution_plan", [])
        
        # Initialize pipeline state
        self.state = {
            "status": "initialized",
            "current_stage": None,
            "progress": 0.0,
            "start_time": None,
            "end_time": None,
            "stages_completed": [],
            "stages_pending": [],
            "errors": []
        }
        
        logger.info(f"Initialized Material Ingestion Pipeline v{self.version} with ID: {self.pipeline_id}")
    
    def register_agent(self, stage_name: str, agent: BaseAgent):
        """
        Register an agent with the pipeline.
        
        Args:
            stage_name (str): The name of the pipeline stage
            agent (BaseAgent): The agent to register
        """
        if stage_name in self.agents:
            logger.warning(f"Overriding existing agent for stage: {stage_name}")
        
        self.agents[stage_name] = agent
        logger.info(f"Registered agent {agent.agent_name} for stage: {stage_name}")
    
    def set_execution_plan(self, execution_plan: List[str]):
        """
        Set the execution plan for the pipeline.
        
        Args:
            execution_plan (List[str]): List of stage names in execution order
        """
        self.execution_plan = execution_plan
        self.state["stages_pending"] = execution_plan.copy()
        logger.info(f"Set execution plan: {', '.join(execution_plan)}")
    
    def run(self, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the pipeline with the given input data.
        
        Args:
            input_data (Dict[str, Any], optional): Input data for the pipeline
            
        Returns:
            Dict[str, Any]: Pipeline results
        """
        # Initialize default input if none provided
        if input_data is None:
            input_data = {"input_dir": str(self.input_dir)}
        
        # Update pipeline state
        self.state["status"] = "running"
        self.state["start_time"] = datetime.now().isoformat()
        self.state["current_stage"] = None
        self.state["progress"] = 0.0
        self.state["stages_completed"] = []
        self.state["stages_pending"] = self.execution_plan.copy()
        self.state["errors"] = []
        
        # Initialize pipeline results
        results = {
            "status": "success",
            "pipeline_id": self.pipeline_id,
            "version": self.version,
            "execution_metadata": {
                "start_time": self.state["start_time"],
                "stages": []
            },
            "stage_outputs": {},
            "final_output": None
        }
        
        # Validate execution plan
        if not self.execution_plan:
            error_msg = "No execution plan defined for the pipeline"
            logger.error(error_msg)
            self._handle_pipeline_error(results, Exception(error_msg), "pipeline_initialization")
            return results
        
        # Validate agents
        for stage_name in self.execution_plan:
            if stage_name not in self.agents:
                error_msg = f"No agent registered for stage: {stage_name}"
                logger.error(error_msg)
                self._handle_pipeline_error(results, Exception(error_msg), "pipeline_initialization")
                return results
        
        # Execute each stage in the execution plan
        current_data = input_data
        total_stages = len(self.execution_plan)
        
        for i, stage_name in enumerate(self.execution_plan):
            # Update current stage and progress
            self.state["current_stage"] = stage_name
            self.state["progress"] = (i / total_stages) * 100
            
            logger.info(f"Executing stage {i+1}/{total_stages}: {stage_name}")
            
            try:
                # Get the agent for this stage
                agent = self.agents[stage_name]
                
                # Execute the agent
                stage_start_time = datetime.now()
                stage_output = agent.run_with_error_handling(current_data)
                stage_end_time = datetime.now()
                
                # Check for agent errors
                if stage_output.get("status") == "error":
                    error_msg = f"Error in stage {stage_name}: {stage_output.get('error_message', 'Unknown error')}"
                    logger.error(error_msg)
                    self._handle_pipeline_error(results, Exception(error_msg), stage_name)
                    return results
                
                # Store stage output and update current data for next stage
                results["stage_outputs"][stage_name] = stage_output
                current_data = self._prepare_next_stage_input(stage_name, stage_output, current_data)
                
                # Update execution metadata
                results["execution_metadata"]["stages"].append({
                    "stage_name": stage_name,
                    "agent_name": agent.agent_name,
                    "start_time": stage_start_time.isoformat(),
                    "end_time": stage_end_time.isoformat(),
                    "execution_time": (stage_end_time - stage_start_time).total_seconds()
                })
                
                # Update pipeline state
                self.state["stages_completed"].append(stage_name)
                self.state["stages_pending"].remove(stage_name)
                
            except Exception as e:
                error_msg = f"Unexpected error in stage {stage_name}: {str(e)}"
                logger.error(error_msg)
                self._handle_pipeline_error(results, e, stage_name)
                return results
        
        # Finalize pipeline
        self.state["status"] = "completed"
        self.state["progress"] = 100.0
        self.state["end_time"] = datetime.now().isoformat()
        self.state["current_stage"] = None
        
        # Set final output (result from last stage)
        last_stage = self.execution_plan[-1]
        results["final_output"] = results["stage_outputs"][last_stage]
        results["execution_metadata"]["end_time"] = self.state["end_time"]
        results["execution_metadata"]["total_execution_time"] = (
            datetime.fromisoformat(self.state["end_time"]) - 
            datetime.fromisoformat(self.state["start_time"])
        ).total_seconds()
        
        logger.info(f"Pipeline execution completed successfully in {results['execution_metadata']['total_execution_time']:.2f} seconds")
        
        return results
    
    def _prepare_next_stage_input(self, 
                                 current_stage: str, 
                                 current_output: Dict[str, Any],
                                 current_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare input for the next pipeline stage.
        
        Args:
            current_stage (str): The current stage name
            current_output (Dict[str, Any]): Output from the current stage
            current_input (Dict[str, Any]): Input to the current stage
            
        Returns:
            Dict[str, Any]: Input for the next stage
        """
        # Default behavior: pass current stage's output as next stage's input
        # Add context from previous stages
        next_input = {
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "data_dir": str(self.data_dir),
            "pipeline_id": self.pipeline_id,
            "previous_stage": current_stage,
            "previous_output": current_output,
            "pipeline_context": current_input.get("pipeline_context", {})
        }
        
        # Add stage-specific context to the pipeline context
        next_input["pipeline_context"][current_stage] = {
            "output_summary": current_output.get("summary", "No summary available"),
            "output_type": current_output.get("output_type", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add any result data from the current stage
        if "result" in current_output:
            next_input["result_from_" + current_stage] = current_output["result"]
        
        return next_input
    
    def _handle_pipeline_error(self, 
                              results: Dict[str, Any], 
                              error: Exception, 
                              stage_name: str) -> None:
        """
        Handle errors that occur during pipeline execution.
        
        Args:
            results (Dict[str, Any]): The pipeline results dict to update
            error (Exception): The exception that occurred
            stage_name (str): The name of the stage where the error occurred
        """
        # Update pipeline state
        self.state["status"] = "error"
        self.state["end_time"] = datetime.now().isoformat()
        
        # Record error information
        error_info = {
            "stage": stage_name,
            "error_type": str(type(error).__name__),
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        self.state["errors"].append(error_info)
        
        # Update pipeline results
        results["status"] = "error"
        results["error"] = error_info
        results["execution_metadata"]["end_time"] = self.state["end_time"]
        results["execution_metadata"]["total_execution_time"] = (
            datetime.fromisoformat(self.state["end_time"]) - 
            datetime.fromisoformat(self.state["start_time"])
        ).total_seconds()
        
        logger.error(f"Pipeline execution failed at stage {stage_name}: {error}")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the pipeline.
        
        Returns:
            Dict[str, Any]: The pipeline state
        """
        return self.state.copy()
    
    def save_results(self, results: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Save pipeline results to a file.
        
        Args:
            results (Dict[str, Any]): The pipeline results
            output_file (Optional[str]): Path to output file, defaults to timestamped file in output_dir
            
        Returns:
            str: Path to the saved results file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"pipeline_results_{timestamp}.json"
        else:
            output_file = Path(output_file)
        
        # Ensure parent directories exist
        output_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Save results
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved pipeline results to {output_file}")
        
        return str(output_file) 