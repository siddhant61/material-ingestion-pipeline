"""
Knowledge Graph Agent Module

This module provides the KnowledgeGraphAgent class that generates a knowledge graph
from the refined fused context produced by the supervision stage.

The agent wraps the KnowledgeGraphGenerator tool and integrates it with the
MaterialIngestionPipeline orchestrator.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.pipeline.knowledge_graph import KnowledgeGraphGenerator
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class KnowledgeGraphAgent(BaseAgent):
    """
    Agent for generating knowledge graphs from refined fused context.
    
    This agent receives the supervised/refined outputs from the SupervisionOrchestratorAgent
    and extracts the context_fusion data to generate a comprehensive knowledge graph.
    
    The agent performs:
    - Extraction of refined fused context from supervision results
    - Knowledge graph generation using the KnowledgeGraphGenerator tool
    - Saving the knowledge graph to the output directory
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Knowledge Graph Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store output directory from settings
        self.output_dir = settings.output_dir / "knowledge_graph"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for knowledge graph generation."""
        # Models are initialized by the KnowledgeGraphGenerator
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
        """Initialize the KnowledgeGraphGenerator tool."""
        # Initialize the KnowledgeGraphGenerator
        self.kg_generator = KnowledgeGraphGenerator()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for the knowledge graph agent.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if the input is valid, False otherwise
        """
        # Input must be a dictionary (checked by base class)
        if not super().validate_input(input_data):
            return False
        
        # Must have supervision results with context_fusion data
        if "result_from_supervision" not in input_data:
            logger.error("Missing required key: result_from_supervision")
            return False
        
        supervision_result = input_data["result_from_supervision"]
        
        # Check if supervision result has the expected structure
        if not isinstance(supervision_result, dict):
            logger.error("result_from_supervision is not a dictionary")
            return False
        
        # Need either 'result' key (new format) or direct 'context_fusion' key (fallback)
        has_context_fusion = (
            ("result" in supervision_result and 
             isinstance(supervision_result["result"], dict) and 
             "context_fusion" in supervision_result["result"]) or
            "context_fusion" in supervision_result
        )
        
        if not has_context_fusion:
            logger.error("Missing context_fusion in supervision results")
            return False
        
        return True
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate the output data from the knowledge graph agent.
        
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
        Generate a knowledge graph from the refined fused context.
        
        Args:
            input_data: Input data dictionary containing:
                - result_from_supervision: Supervision results with refined context_fusion
                
        Returns:
            Dictionary containing the generated knowledge graph
        """
        logger.info("Starting knowledge graph generation...")
        
        try:
            # Extract the supervision results
            supervision_result = input_data["result_from_supervision"]
            
            # Extract the refined fused context
            # The supervision agent returns refined_outputs in the 'result' key
            if "result" in supervision_result and isinstance(supervision_result["result"], dict):
                refined_outputs = supervision_result["result"]
                fused_context_for_kg = refined_outputs.get("context_fusion")
            else:
                # Fallback: try direct access
                fused_context_for_kg = supervision_result.get("context_fusion")
            
            if not fused_context_for_kg:
                logger.error("Could not extract context_fusion from supervision results")
                return {
                    "status": "error",
                    "result": {},
                    "summary": "Failed to extract context_fusion from supervision results",
                    "output_type": "knowledge_graph",
                    "error": "Missing context_fusion data"
                }
            
            logger.info("Successfully extracted refined fused context for knowledge graph generation")
            
            # Generate the knowledge graph using the KnowledgeGraphGenerator
            knowledge_graph = self.kg_generator.generate_knowledge_graph(fused_context_for_kg)
            
            # Check if knowledge graph was generated successfully
            if not knowledge_graph or knowledge_graph.get("metadata", {}).get("status") == "failed":
                error_msg = knowledge_graph.get("metadata", {}).get("error", "Unknown error")
                logger.error(f"Knowledge graph generation failed: {error_msg}")
                return {
                    "status": "error",
                    "result": knowledge_graph or {},
                    "summary": f"Knowledge graph generation failed: {error_msg}",
                    "output_type": "knowledge_graph",
                    "error": error_msg
                }
            
            # Save the knowledge graph to file
            output_file = self.kg_generator.save_knowledge_graph(
                knowledge_graph,
                str(self.output_dir)
            )
            
            # Get entity and relationship counts for summary
            entity_count = len(knowledge_graph.get("entities", []))
            relationship_count = len(knowledge_graph.get("relationships", []))
            
            logger.info(f"Knowledge graph generated successfully: {entity_count} entities, {relationship_count} relationships")
            logger.info(f"Knowledge graph saved to {output_file}")
            
            # Return the knowledge graph in the format expected by the pipeline
            return {
                "status": "success",
                "result": knowledge_graph,
                "summary": f"Generated knowledge graph with {entity_count} entities and {relationship_count} relationships",
                "output_type": "knowledge_graph",
                "kg_metadata": {
                    "entity_count": entity_count,
                    "relationship_count": relationship_count,
                    "output_file": output_file,
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating knowledge graph: {str(e)}")
            return {
                "status": "error",
                "result": {},
                "summary": f"Knowledge graph generation failed: {str(e)}",
                "output_type": "knowledge_graph",
                "error": str(e)
            }
