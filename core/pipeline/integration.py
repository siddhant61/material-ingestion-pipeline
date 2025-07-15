#!/usr/bin/env python3
"""
Pipeline Integration Module

This module facilitates the integration between the material ingestion pipeline
and subsequent pipelines (like Vision & Mood-Board Creation) by providing:
1. Resource pooling
2. Data transformation
3. Interface standardization
4. Metadata enrichment
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class PipelineIntegrator:
    """
    Facilitates integration between the material ingestion pipeline and subsequent
    processing pipelines by transforming knowledge graph data into optimized formats.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the PipelineIntegrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        logger.info("Initialized PipelineIntegrator")
    
    def create_resource_pool(
        self,
        knowledge_graph_path: str,
        embeddings_path: str,
        output_path: str,
        include_raw_data: bool = True
    ) -> str:
        """Create a standardized resource pool for the next pipeline to consume.
        
        Args:
            knowledge_graph_path: Path to the knowledge graph JSON file
            embeddings_path: Path to the embeddings JSON file
            output_path: Path to save the integrated resource pool
            include_raw_data: Whether to include the complete raw data
            
        Returns:
            Path to the created resource pool file
        """
        try:
            with open(knowledge_graph_path, 'r') as kg_file:
                kg_data = json.load(kg_file)
            
            with open(embeddings_path, 'r') as emb_file:
                embeddings_data = json.load(emb_file)
            
            # Create an optimized structure for the next pipeline
            resource_pool = {
                "metadata": {
                    "creation_timestamp": datetime.now().isoformat(),
                    "source_pipeline": "material_ingestion",
                    "entity_count": len(kg_data.get("entities", [])),
                    "relationship_count": len(kg_data.get("relationships", [])),
                    "embedding_dimensions": len(embeddings_data.get("embeddings", [{}])[0].get("vector", [])) 
                                           if embeddings_data.get("embeddings") else 0,
                },
                "knowledge_structure": self._extract_hierarchical_summary(kg_data),
                "key_entities": self._identify_key_entities(kg_data),
                "visual_resource_index": self._build_visual_resource_index(kg_data),
                "conceptual_map": self._create_conceptual_map(kg_data),
                "temporal_progression": self._extract_temporal_progression(kg_data)
            }
            
            # Optionally include the complete raw data
            if include_raw_data:
                resource_pool["knowledge_graph"] = kg_data
                resource_pool["embeddings"] = embeddings_data
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the resource pool
            with open(output_path, 'w') as out_file:
                json.dump(resource_pool, out_file, indent=2)
            
            logger.info(f"Created resource pool at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to create resource pool: {str(e)}")
            raise
    
    def _extract_hierarchical_summary(self, kg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a hierarchical summary of the knowledge graph structure.
        
        Args:
            kg_data: Knowledge graph data
            
        Returns:
            Hierarchical summary of the knowledge structure
        """
        hierarchy = {
            "domains": [],
            "theories": [],
            "methods": [],
            "applications": []
        }
        
        # Entity types from the KnowledgeGraphGenerator class
        foundation_types = ["domain", "field", "subject", "discipline"]
        theoretical_types = ["theory", "concept", "principle", "framework", "model", "law", "theorem"]
        methodological_types = ["method", "technique", "approach", "process", "algorithm", "strategy"]
        practical_types = ["application", "example", "case_study", "tool", "implementation", "experiment"]
        
        for entity in kg_data.get("entities", []):
            entity_type = entity.get("type", "").lower()
            name = entity.get("name", "")
            id = entity.get("id", "")
            
            if entity_type in foundation_types:
                hierarchy["domains"].append({"id": id, "name": name, "type": entity_type})
            elif entity_type in theoretical_types:
                hierarchy["theories"].append({"id": id, "name": name, "type": entity_type})
            elif entity_type in methodological_types:
                hierarchy["methods"].append({"id": id, "name": name, "type": entity_type})
            elif entity_type in practical_types:
                hierarchy["applications"].append({"id": id, "name": name, "type": entity_type})
        
        return hierarchy
    
    def _identify_key_entities(self, kg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify key entities from the knowledge graph.
        
        Args:
            kg_data: Knowledge graph data
            
        Returns:
            List of key entities with essential metadata
        """
        # Count relationships for each entity
        relationship_counts = {}
        for relationship in kg_data.get("relationships", []):
            source = relationship.get("source", "")
            target = relationship.get("target", "")
            
            relationship_counts[source] = relationship_counts.get(source, 0) + 1
            relationship_counts[target] = relationship_counts.get(target, 0) + 1
        
        # Identify entities with the most relationships (top 20%)
        sorted_entities = sorted(relationship_counts.items(), key=lambda x: x[1], reverse=True)
        top_entity_count = max(1, len(sorted_entities) // 5)  # Top 20%
        key_entity_ids = [entity_id for entity_id, _ in sorted_entities[:top_entity_count]]
        
        # Extract details for key entities
        key_entities = []
        for entity in kg_data.get("entities", []):
            if entity.get("id", "") in key_entity_ids:
                key_entities.append({
                    "id": entity.get("id", ""),
                    "name": entity.get("name", ""),
                    "type": entity.get("type", ""),
                    "description": entity.get("description", ""),
                    "importance": relationship_counts.get(entity.get("id", ""), 0),
                    "source": entity.get("source", ""),
                    "temporal_info": entity.get("temporal_info", {}),
                    "resources": entity.get("resources", {})
                })
        
        return key_entities
    
    def _build_visual_resource_index(self, kg_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Build an index of visual resources from the knowledge graph.
        
        Args:
            kg_data: Knowledge graph data
            
        Returns:
            Dictionary mapping entity types to their visual resources
        """
        visual_resources = {}
        
        for entity in kg_data.get("entities", []):
            entity_type = entity.get("type", "unknown")
            resources = entity.get("resources", {})
            visual_urls = resources.get("visual_resources", [])
            
            if visual_urls:
                if entity_type not in visual_resources:
                    visual_resources[entity_type] = []
                
                visual_resources[entity_type].append({
                    "entity_id": entity.get("id", ""),
                    "entity_name": entity.get("name", ""),
                    "visual_urls": visual_urls,
                    "description": entity.get("description", "")
                })
        
        return visual_resources
    
    def _create_conceptual_map(self, kg_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Create a conceptual map showing relationships between concepts.
        
        Args:
            kg_data: Knowledge graph data
            
        Returns:
            Dictionary mapping concept IDs to related concept IDs
        """
        conceptual_map = {}
        
        # Build entity lookup for quick access
        entity_lookup = {entity.get("id", ""): entity for entity in kg_data.get("entities", [])}
        
        # Create concept relationship map
        for relationship in kg_data.get("relationships", []):
            source_id = relationship.get("source", "")
            target_id = relationship.get("target", "")
            
            # Skip if either entity doesn't exist
            if source_id not in entity_lookup or target_id not in entity_lookup:
                continue
                
            # Add to conceptual map
            if source_id not in conceptual_map:
                conceptual_map[source_id] = []
            
            if target_id not in conceptual_map[source_id]:
                conceptual_map[source_id].append(target_id)
        
        return conceptual_map
    
    def _extract_temporal_progression(self, kg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract temporal progression of concepts from the knowledge graph.
        
        Args:
            kg_data: Knowledge graph data
            
        Returns:
            List of concepts ordered by their temporal information
        """
        entities_with_time = []
        
        for entity in kg_data.get("entities", []):
            temporal_info = entity.get("temporal_info", {})
            
            if temporal_info:
                entities_with_time.append({
                    "id": entity.get("id", ""),
                    "name": entity.get("name", ""),
                    "type": entity.get("type", ""),
                    "year": temporal_info.get("year"),
                    "period": temporal_info.get("period", "Unknown"),
                    "description": entity.get("description", "")
                })
        
        # Sort by year if available
        entities_with_time.sort(
            key=lambda x: (
                x["year"] if x["year"] is not None else float('inf'),
                x["name"]
            )
        )
        
        return entities_with_time


# Utility functions for direct use
def create_vision_board_input(
    knowledge_graph_path: str,
    embeddings_path: str,
    output_dir: str
) -> str:
    """Create input specifically formatted for the Vision & Mood-Board Creation pipeline.
    
    Args:
        knowledge_graph_path: Path to the knowledge graph JSON
        embeddings_path: Path to the embeddings JSON
        output_dir: Directory to save the output
        
    Returns:
        Path to the created input file
    """
    integrator = PipelineIntegrator()
    output_path = os.path.join(output_dir, "vision_board_input.json")
    
    return integrator.create_resource_pool(
        knowledge_graph_path=knowledge_graph_path,
        embeddings_path=embeddings_path,
        output_path=output_path
    ) 