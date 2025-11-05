"""
Embedding Agent Module

This module provides the EmbeddingAgent class that generates embeddings
from the knowledge graph produced by the knowledge graph generation stage.

The agent wraps the EmbeddingsGenerator tool and integrates it with the
MaterialIngestionPipeline orchestrator.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.pipeline.embeddings import EmbeddingsGenerator
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingAgent(BaseAgent):
    """
    Agent for generating embeddings from knowledge graphs.
    
    This agent receives the knowledge graph from the KnowledgeGraphAgent
    and generates vector embeddings for entities.
    
    The agent performs:
    - Extraction of knowledge graph from pipeline results
    - Embedding generation for entities
    - Saving embeddings to the output directory
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Embedding Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store output directory from settings
        self.output_dir = settings.output_dir / "embeddings"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for embedding generation."""
        # Models are initialized by the EmbeddingsGenerator
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
        """Initialize the EmbeddingsGenerator tool."""
        # Initialize the EmbeddingsGenerator with configuration
        embeddings_config = {
            "embedding_dimension": self.config.get("embedding_dimension", 384),
            "model_name": self.config.get("model_name", "all-MiniLM-L6-v2")
        }
        self.embeddings_generator = EmbeddingsGenerator(embeddings_config)
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for the embedding agent.
        
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
        Validate the output data from the embedding agent.
        
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
        Generate embeddings from the knowledge graph.
        
        Args:
            input_data: Input data dictionary containing:
                - result_from_knowledge_graph: Knowledge graph results with the graph data
                
        Returns:
            Dictionary containing the generated embeddings
        """
        logger.info("Starting embedding generation...")
        
        try:
            # Extract the knowledge graph from pipeline results
            kg_result = input_data["result_from_knowledge_graph"]
            knowledge_graph = kg_result["result"]
            
            logger.info(f"Extracted knowledge graph with {len(knowledge_graph.get('entities', []))} entities")
            
            # Check if knowledge graph has content
            entity_count = len(knowledge_graph.get("entities", []))
            
            if entity_count == 0:
                logger.warning("Knowledge graph is empty, skipping embedding generation")
                return {
                    "status": "skipped",
                    "result": {
                        "entity_embeddings": {},
                        "relationship_embeddings": {},
                        "metadata": {
                            "entity_count": 0,
                            "status": "skipped",
                            "reason": "empty_graph"
                        }
                    },
                    "summary": "Knowledge graph is empty, no embeddings generated",
                    "output_type": "embeddings",
                    "reason": "empty_graph"
                }
            
            logger.info(f"Generating embeddings for {entity_count} entities")
            
            # Generate embeddings using the EmbeddingsGenerator
            embeddings = self.embeddings_generator.generate_embeddings(knowledge_graph)
            
            # Check if embeddings were generated successfully
            if not embeddings or embeddings.get("metadata", {}).get("status") == "failed":
                error_msg = embeddings.get("metadata", {}).get("error", "Unknown error")
                logger.error(f"Embedding generation failed: {error_msg}")
                return {
                    "status": "error",
                    "result": embeddings or {},
                    "summary": f"Embedding generation failed: {error_msg}",
                    "output_type": "embeddings",
                    "error": error_msg
                }
            
            # Save the embeddings to file
            output_file = self.embeddings_generator.save_embeddings(
                embeddings,
                str(self.output_dir)
            )
            
            # Get embedding counts for summary
            embedding_count = len(embeddings.get("entity_embeddings", {}))
            embedding_dimension = embeddings.get("metadata", {}).get("embedding_dimension", 0)
            
            logger.info(f"Generated {embedding_count} embeddings with dimension {embedding_dimension}")
            logger.info(f"Embeddings saved to {output_file}")
            
            # Return the embeddings in the format expected by the pipeline
            return {
                "status": "success",
                "result": embeddings,
                "summary": f"Generated {embedding_count} embeddings with dimension {embedding_dimension}",
                "output_type": "embeddings",
                "embedding_metadata": {
                    "embedding_count": embedding_count,
                    "embedding_dimension": embedding_dimension,
                    "output_file": output_file,
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {
                "status": "error",
                "result": {},
                "summary": f"Embedding generation failed: {str(e)}",
                "output_type": "embeddings",
                "error": str(e)
            }
