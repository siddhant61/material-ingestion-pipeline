"""
Embeddings Generator

This module provides functionality for generating embeddings from knowledge graphs.
"""

import os
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingsGenerator:
    """
    Generates vector embeddings from knowledge graph entities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the EmbeddingsGenerator.
        
        Args:
            config (Dict[str, Any], optional): Configuration for the generator
        """
        self.config = config or {}
        self.embedding_dimension = self.config.get("embedding_dimension", 384)
        logger.info(f"Initialized EmbeddingsGenerator with dimension: {self.embedding_dimension}")
        
    def generate_embeddings(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings from a knowledge graph.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph data
            
        Returns:
            Dict[str, Any]: The generated embeddings
        """
        logger.info("Generating embeddings from knowledge graph")
        
        try:
            # Extract entities to generate embeddings for
            entities = knowledge_graph.get("entities", [])
            entity_count = len(entities)
            logger.info(f"Generating embeddings for {entity_count} entities")
            
            # Generate embeddings for entities
            entity_embeddings = self._generate_entity_embeddings(entities)
            
            # Generate embeddings for relationships if needed
            relationships = knowledge_graph.get("relationships", [])
            relationship_embeddings = {}
            
            # Build the embeddings structure
            embeddings = {
                "entity_embeddings": entity_embeddings,
                "relationship_embeddings": relationship_embeddings,
                "metadata": {
                    "source": "knowledge_graph",
                    "entity_count": entity_count,
                    "relationship_count": len(relationships),
                    "embedding_dimension": self.embedding_dimension,
                    "generator_version": "0.1.0"
                }
            }
            
            logger.info(f"Generated embeddings for {len(entity_embeddings)} entities")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return minimal embeddings on error
            return {
                "entity_embeddings": {},
                "relationship_embeddings": {},
                "metadata": {
                    "error": str(e),
                    "status": "failed"
                }
            }
    
    def save_embeddings(self, embeddings: Dict[str, Any], output_dir: str) -> str:
        """
        Save the embeddings to a file.
        
        Args:
            embeddings (Dict[str, Any]): The embeddings to save
            output_dir (str): Directory to save the embeddings
            
        Returns:
            str: Path to the saved file
        """
        os.makedirs(output_dir, exist_ok=True)
        output_file = Path(output_dir) / "embeddings.json"
        
        # For JSON serialization, we need to convert numpy arrays to lists
        serializable_embeddings = self._make_serializable(embeddings)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_embeddings, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved embeddings to {output_file}")
        return str(output_file)
    
    def _generate_entity_embeddings(self, entities: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Generate embeddings for entities.
        
        Args:
            entities (List[Dict[str, Any]]): List of entities
            
        Returns:
            Dict[str, List[float]]: Dictionary mapping entity IDs to embeddings
        """
        entity_embeddings = {}
        
        try:
            # Try to import sentence-transformers for embedding generation
            from sentence_transformers import SentenceTransformer
            
            # Initialize the model
            model_name = self.config.get("model_name", "all-MiniLM-L6-v2")
            model = SentenceTransformer(model_name)
            
            # Collect entity texts for batch encoding
            entity_texts = []
            entity_ids = []
            
            for entity in entities:
                entity_id = entity.get("id", "")
                if not entity_id:
                    continue
                
                # Combine name and description for better embeddings
                entity_text = f"{entity.get('name', '')} - {entity.get('description', '')}"
                entity_texts.append(entity_text)
                entity_ids.append(entity_id)
            
            # Generate embeddings in batches
            if entity_texts:
                logger.info(f"Generating embeddings using {model_name}")
                embeddings = model.encode(entity_texts)
                
                # Convert embeddings to list and store by entity ID
                for i, entity_id in enumerate(entity_ids):
                    entity_embeddings[entity_id] = embeddings[i].tolist()
            
        except ImportError:
            logger.warning("sentence-transformers not available, using placeholder embeddings")
            # Use placeholder random embeddings if sentence-transformers not available
            for entity in entities:
                entity_id = entity.get("id", "")
                if not entity_id:
                    continue
                
                # Generate a random embedding vector with the configured dimension
                placeholder_embedding = np.random.randn(self.embedding_dimension).tolist()
                entity_embeddings[entity_id] = placeholder_embedding
        
        return entity_embeddings
    
    def _make_serializable(self, data: Any) -> Any:
        """
        Convert data to JSON serializable format.
        
        Args:
            data: Data to convert
            
        Returns:
            JSON serializable data
        """
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, dict):
            return {k: self._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        else:
            return data 