"""
Visualization Agent Module

This module provides the VisualizationAgent class that generates visualizations
from the knowledge graph produced by the knowledge graph generation stage.

The agent wraps the KnowledgeGraphVisualizer tool and integrates it with the
MaterialIngestionPipeline orchestrator.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.pipeline.visualization import KnowledgeGraphVisualizer
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class VisualizationAgent(BaseAgent):
    """
    Agent for generating visualizations from knowledge graphs.
    
    This agent receives the knowledge graph from the KnowledgeGraphAgent
    and generates both interactive and static visualizations.
    
    The agent performs:
    - Extraction of knowledge graph from pipeline results
    - Interactive HTML visualization generation
    - Static PNG visualization generation
    - Saving visualizations to the output directory
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Visualization Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store output directory from settings
        self.output_dir = settings.output_dir / "visualizations"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for visualization."""
        # Models are not needed for visualization
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
        """Initialize the KnowledgeGraphVisualizer tool."""
        # Initialize the KnowledgeGraphVisualizer with configuration
        visualizer_config = {
            "height": self.config.get("height", "800px"),
            "width": self.config.get("width", "100%"),
            "bgcolor": self.config.get("bgcolor", "#ffffff"),
            "node_scaling": self.config.get("node_scaling", 1.5)
        }
        self.visualizer = KnowledgeGraphVisualizer(visualizer_config)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for the visualization agent.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if the input is valid, False otherwise
        """
        # Input must be a dictionary (checked by base class)
        if not super().validate_input(input_data):
            return False
        
        # Must have knowledge graph results
        if "result_from_knowledge_graph" not in input_data:
            logger.error("Missing required key: result_from_knowledge_graph")
            return False
        
        kg_result = input_data["result_from_knowledge_graph"]
        
        # Check if knowledge graph result has the expected structure
        if not isinstance(kg_result, dict):
            logger.error("result_from_knowledge_graph is not a dictionary")
            return False
        
        # Need the 'result' key with knowledge graph data
        if "result" not in kg_result:
            logger.error("Missing 'result' in knowledge_graph results")
            return False
        
        knowledge_graph = kg_result["result"]
        
        # Validate that knowledge graph has entities
        if not isinstance(knowledge_graph, dict):
            logger.error("Knowledge graph result is not a dictionary")
            return False
        
        if "entities" not in knowledge_graph:
            logger.error("Knowledge graph missing 'entities' key")
            return False
        
        return True
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate the output data from the visualization agent.
        
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
        Generate visualizations from the knowledge graph.
        
        Args:
            input_data: Input data dictionary containing:
                - result_from_knowledge_graph: Knowledge graph results with the graph data
                
        Returns:
            Dictionary containing the paths to generated visualizations
        """
        logger.info("Starting knowledge graph visualization...")
        
        try:
            # Extract the knowledge graph from pipeline results
            kg_result = input_data["result_from_knowledge_graph"]
            knowledge_graph = kg_result["result"]
            
            logger.info(f"Extracted knowledge graph with {len(knowledge_graph.get('entities', []))} entities")
            
            # Check if knowledge graph has content
            entity_count = len(knowledge_graph.get("entities", []))
            relationship_count = len(knowledge_graph.get("relationships", []))
            
            if entity_count == 0:
                logger.warning("Knowledge graph is empty, skipping visualization")
                return {
                    "status": "skipped",
                    "result": {},
                    "summary": "Knowledge graph is empty, no visualizations generated",
                    "output_type": "visualization",
                    "reason": "empty_graph"
                }
            
            logger.info(f"Generating visualizations for {entity_count} entities and {relationship_count} relationships")
            
            # Generate interactive visualization
            interactive_path = self.visualizer.create_interactive_visualization(
                knowledge_graph,
                str(self.output_dir),
                "knowledge_graph_interactive.html"
            )
            
            # Generate static visualization
            static_path = self.visualizer.create_static_visualization(
                knowledge_graph,
                str(self.output_dir),
                "knowledge_graph_static.png"
            )
            
            logger.info(f"Interactive visualization saved to: {interactive_path}")
            logger.info(f"Static visualization saved to: {static_path}")
            
            # Return the visualization paths in the format expected by the pipeline
            return {
                "status": "success",
                "result": {
                    "interactive_visualization": interactive_path,
                    "static_visualization": static_path
                },
                "summary": f"Generated interactive and static visualizations for knowledge graph with {entity_count} entities",
                "output_type": "visualization",
                "visualization_metadata": {
                    "entity_count": entity_count,
                    "relationship_count": relationship_count,
                    "interactive_path": interactive_path,
                    "static_path": static_path,
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {str(e)}")
            return {
                "status": "error",
                "result": {},
                "summary": f"Visualization generation failed: {str(e)}",
                "output_type": "visualization",
                "error": str(e)
            }
