"""
Knowledge Graph Generator

This module provides functionality for generating hierarchical knowledge graphs from educational content.
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class KnowledgeGraphGenerator:
    """
    Generates hierarchical knowledge graphs from educational content data.
    """
    
    # Entity type classifications
    FOUNDATION_TYPES = ["domain", "field", "subject", "discipline"]  # Roots
    THEORETICAL_TYPES = ["theory", "concept", "principle", "framework", "model", "law", "theorem"]  # Trunk
    METHODOLOGICAL_TYPES = ["method", "technique", "approach", "process", "algorithm", "strategy"]  # Branches
    PRACTICAL_TYPES = ["application", "example", "case_study", "tool", "implementation", "experiment"]  # Fruits/Flowers
    RESOURCE_TYPES = ["reference", "visualization", "definition", "quote", "explanation", "media"]  # Supporting elements
    
    # Information source types
    SOURCE_TYPES = {
        "course": "Information extracted from course materials",
        "transcript": "Information extracted from lecture transcripts",
        "slide": "Information extracted from lecture slides",
        "rag": "Information added through Retrieval-Augmented Generation",
        "visual_rag": "Information added through Visual RAG processing",
        "external": "Information from external knowledge sources"
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the KnowledgeGraphGenerator.
        
        Args:
            config (Dict[str, Any], optional): Configuration for the generator
        """
        self.config = config or {}
        self.default_source = self.config.get("default_source", "course")
        
        # Set up hierarchy level mapping for visualization
        self.hierarchy_levels = {
            "root": 1,
            "trunk": 2,
            "branch": 3,
            "leaf": 4,
            "resource": 5
        }
        
        # Configure temporal periods
        self.time_periods = self.config.get("time_periods", self._default_time_periods())
        
        logger.info("Initialized KnowledgeGraphGenerator with hierarchical structure support")
    
    def _default_time_periods(self) -> List[Dict[str, Any]]:
        """Define default time periods for scientific concepts"""
        return [
            {"name": "Ancient", "start_year": -3000, "end_year": 500, "description": "Ancient scientific knowledge"},
            {"name": "Medieval", "start_year": 500, "end_year": 1500, "description": "Medieval scientific developments"},
            {"name": "Renaissance", "start_year": 1500, "end_year": 1700, "description": "Scientific revolution era"},
            {"name": "Classical", "start_year": 1700, "end_year": 1900, "description": "Classical physics and early modern science"},
            {"name": "Modern", "start_year": 1900, "end_year": 1950, "description": "Early modern scientific discoveries"},
            {"name": "Contemporary", "start_year": 1950, "end_year": 2000, "description": "Later 20th century scientific advancements"},
            {"name": "Recent", "start_year": 2000, "end_year": datetime.now().year, "description": "21st century scientific developments"}
        ]
    
    def generate_knowledge_graph(self, fused_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a hierarchical knowledge graph from the fused context.
        
        Args:
            fused_context (Dict[str, Any]): The fused context data
            
        Returns:
            Dict[str, Any]: The generated hierarchical knowledge graph
        """
        logger.info("Generating hierarchical knowledge graph from fused context")
        
        try:
            # Reset hierarchical relationships
            self._hierarchical_relationships = []
            
            # Extract course structure to build the hierarchy base
            course_structure = self._extract_course_structure(fused_context)
            
            # Extract entities from the fused context
            entities = self._extract_entities(fused_context)
            
            # Extract relationships between entities
            relationships = self._extract_relationships(fused_context, entities)
            
            # Build the hierarchical structure (also creates hierarchical relationships)
            hierarchy = self._build_hierarchy(entities, course_structure)
            
            # Add temporal information to entities
            entities = self._add_temporal_information(entities, fused_context)
            
            # Add definitions and resources
            entities = self._add_definitions_and_resources(entities, fused_context)
            
            # Add temporal connections (progression relationships)
            temporal_relationships = self._add_temporal_connections(entities, fused_context)
            
            # Combine all relationships
            all_relationships = relationships.copy()
            
            # Add hierarchical relationships
            if hasattr(self, "_hierarchical_relationships") and self._hierarchical_relationships:
                all_relationships.extend(self._hierarchical_relationships)
                logger.info(f"Added {len(self._hierarchical_relationships)} hierarchical relationships")
            
            # Add temporal relationships
            if temporal_relationships:
                all_relationships.extend(temporal_relationships)
                logger.info(f"Added {len(temporal_relationships)} temporal progression relationships")
            
            # Normalize relationship types
            all_relationships = self._normalize_relationship_types(all_relationships)
            
            # Calculate hierarchy level counts
            hierarchy_level_counts = {
                "root": len([e for e in entities if e.get("hierarchy_level") == "root"]),
                "trunk": len([e for e in entities if e.get("hierarchy_level") == "trunk"]),
                "branch": len([e for e in entities if e.get("hierarchy_level") == "branch"]),
                "leaf": len([e for e in entities if e.get("hierarchy_level") == "leaf"]),
                "resource": len([e for e in entities if e.get("hierarchy_level") == "resource"])
            }
            
            # Build the complete knowledge graph structure
            knowledge_graph = {
                "entities": entities,
                "relationships": all_relationships,
                "hierarchy": hierarchy,
                "metadata": {
                    "source": "fused_context",
                    "entity_count": len(entities),
                    "relationship_count": len(all_relationships),
                    "hierarchy_levels": self.hierarchy_levels,
                    "hierarchy_counts": hierarchy_level_counts,
                    "source_types": self.SOURCE_TYPES,
                    "time_periods": self.time_periods,
                    "generator_version": "1.1.0",
                    "generated_at": datetime.now().isoformat(),
                    "tree_metaphor": {
                        "roots": "Domain/field level concepts (foundation)",
                        "trunk": "Major theories/principles (theoretical)",
                        "branches": "Methods/techniques (methodological)",
                        "leaves_fruits": "Applications/examples (practical)",
                        "resources": "Supporting resources and definitions"
                    }
                }
            }
            
            logger.info(f"Generated hierarchical knowledge graph with {len(entities)} entities and {len(all_relationships)} relationships")
            logger.info(f"Hierarchy distribution: {hierarchy_level_counts}")
            return knowledge_graph
            
        except Exception as e:
            logger.error(f"Error generating knowledge graph: {str(e)}")
            # Return a minimal knowledge graph on error
            return {
                "entities": [],
                "relationships": [],
                "hierarchy": {"root": [], "trunk": [], "branch": [], "leaf": [], "resource": []},
                "metadata": {
                    "error": str(e),
                    "status": "failed",
                    "source_types": self.SOURCE_TYPES,
                    "generated_at": datetime.now().isoformat()
                }
            }
    
    def save_knowledge_graph(self, knowledge_graph: Dict[str, Any], output_dir: str) -> str:
        """
        Save the knowledge graph to a file.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph to save
            output_dir (str): Directory to save the graph
            
        Returns:
            str: Path to the saved file
        """
        os.makedirs(output_dir, exist_ok=True)
        output_file = Path(output_dir) / "knowledge_graph.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_graph, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Saved hierarchical knowledge graph to {output_file}")
        return str(output_file)
    
    def _extract_course_structure(self, fused_context: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract the course structure to serve as the base for the hierarchy.
        
        Args:
            fused_context (Dict[str, Any]): The fused context
            
        Returns:
            Dict[str, List[str]]: Hierarchical course structure
        """
        structure = {
            "root": [],      # Domain/field level
            "trunk": [],     # Major theories/concepts
            "branch": [],    # Supporting concepts/methods
            "leaf": [],      # Examples/applications
            "resource": []   # Resources and definitions
        }
        
        # Extract course title/domain as root
        if "course_info" in fused_context and isinstance(fused_context["course_info"], dict):
            title = fused_context["course_info"].get("title", "")
            if title:
                structure["root"].append(title)
        
        # Extract modules/topics as trunk
        if "module_structure" in fused_context and isinstance(fused_context["module_structure"], list):
            for module in fused_context["module_structure"]:
                if isinstance(module, dict) and "title" in module:
                    structure["trunk"].append(module.get("title", ""))
        
        return structure
    
    def _categorize_entity_type(self, entity_type: str) -> str:
        """
        Categorize an entity type into one of the five hierarchy levels.
        
        Args:
            entity_type (str): The entity type to categorize
            
        Returns:
            str: The hierarchy level ("root", "trunk", "branch", "leaf", or "resource")
        """
        entity_type = entity_type.lower()
        
        if any(t in entity_type for t in self.FOUNDATION_TYPES):
            return "root"
        elif any(t in entity_type for t in self.THEORETICAL_TYPES):
            return "trunk"
        elif any(t in entity_type for t in self.METHODOLOGICAL_TYPES):
            return "branch"
        elif any(t in entity_type for t in self.PRACTICAL_TYPES):
            return "leaf"
        elif any(t in entity_type for t in self.RESOURCE_TYPES):
            return "resource"
        
        # Use more nuanced categorization for common entity types
        if entity_type in ["topic", "module", "unit", "course", "subject"]:
            return "root"
        elif entity_type in ["concept", "theory", "principle", "framework", "idea", "model", "equation"]:
            return "trunk"
        elif entity_type in ["method", "technique", "approach", "process", "procedure", "algorithm"]:
            return "branch"
        elif entity_type in ["example", "application", "case_study", "implementation", "tool", "exercise"]:
            return "leaf"
        elif entity_type in ["reference", "resource", "image", "figure", "definition", "quote"]:
            return "resource"
        
        # Default categorization based on intuitive guesses
        if "theor" in entity_type or "concept" in entity_type or "principle" in entity_type:
            return "trunk"
        elif "method" in entity_type or "technique" in entity_type:
            return "branch"
        elif "example" in entity_type or "app" in entity_type or "case" in entity_type:
            return "leaf"
        elif "resource" in entity_type or "reference" in entity_type or "definition" in entity_type:
            return "resource"
        
        # Default to trunk for most general concepts
        return "trunk"
    
    def _identify_source_type(self, sources: List[str]) -> str:
        """
        Identify the primary source type for an entity.
        
        Args:
            sources (List[str]): List of source references
            
        Returns:
            str: Source type (course, transcript, slide, rag, visual_rag, external)
        """
        if not sources:
            return self.default_source
        
        # Check for explicit source tags in the sources list
        for source in sources:
            source_lower = source.lower() if isinstance(source, str) else ""
            for source_type in self.SOURCE_TYPES:
                if source_type in source_lower:
                    return source_type
        
        # Use pattern matching to guess the source type
        source_str = " ".join(str(s) for s in sources)
        if "slide" in source_str or "presentation" in source_str:
            return "slide"
        elif "transcript" in source_str or "lecture" in source_str:
            return "transcript"
        elif "rag" in source_str:
            return "rag"
        elif "visual" in source_str or "image" in source_str:
            return "visual_rag"
        elif "external" in source_str or "reference" in source_str:
            return "external"
        else:
            return self.default_source
    
    def _extract_entities(self, fused_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract entities from the fused context.
        
        Args:
            fused_context (Dict[str, Any]): The fused context data
            
        Returns:
            List[Dict[str, Any]]: List of extracted entities
        """
        # Debug logging to understand fused context structure
        logger.info("Fused context top-level keys: %s", list(fused_context.keys()))
        
        # Continue with the existing entity extraction
        entities = []
        entity_ids = set()  # Track entity IDs to avoid duplicates
        
        # Add course as a root entity
        course_entity = {
            "id": "domain_0",
            "type": "domain",
            "name": "Course Domain",
            "description": "Course domain encompassing all content",
            "hierarchy_level": "root",
            "properties": {
                "importance": 10,
                "keywords": [],
                "category": "domain",
                "sources": ["course"],
                "source_type": "course",
                "objectives": [],
                "learning_outcomes": [],
                "temporal": {
                    "year": 1900,
                    "period": "Classical"
                },
                "enrichment_status": "source", # Indicates this data came from source material, not RAG
                "resources": {
                    "visualizations": [],
                    "references": [],
                    "examples": []
                }
            }
        }
        entities.append(course_entity)
        entity_ids.add("domain_0")
        
        # Extract course information
        course_info = fused_context.get("course_info", {})
        if course_info:
            course_id = "course_0"
            if course_id not in entity_ids:
                course_name = course_info.get("title", "Course")
                course_entity = {
                    "id": course_id,
                    "type": "course",
                    "name": course_name,
                    "description": course_info.get("description", ""),
                    "hierarchy_level": "root",
                    "properties": {
                        "importance": 9,
                        "keywords": course_info.get("keywords", []),
                        "category": "course",
                        "sources": ["course_info"],
                        "source_type": "course",
                        "enrichment_status": "source",
                        "resources": {
                            "visualizations": [],
                            "references": [],
                            "examples": []
                        }
                    }
                }
                entities.append(course_entity)
                entity_ids.add(course_id)
        
        # Extract modules from module_structure
        module_structure = fused_context.get("module_structure", {})
        if isinstance(module_structure, dict):
            for module_key, module in module_structure.items():
                if isinstance(module, dict):
                    module_id = f"module_{module_key.replace(' ', '_').lower()}"
                    
                    if module_id not in entity_ids:
                        module_entity = {
                            "id": module_id,
                            "type": "module",
                            "name": module.get("title", module_key),
                            "description": module.get("description", ""),
                            "hierarchy_level": "trunk",
                            "properties": {
                                "importance": 8,
                                "keywords": [],
                                "category": "module",
                                "sources": ["module_structure"],
                                "source_type": "course",
                                "enrichment_status": "source",
                                "resources": {
                                    "visualizations": [],
                                    "references": [],
                                    "examples": []
                                }
                            }
                        }
                        entities.append(module_entity)
                        entity_ids.add(module_id)
                elif isinstance(module, list):
                    for i, lesson in enumerate(module):
                        if isinstance(lesson, dict):
                            lesson_id = f"module_{module_key.replace(' ', '_').lower()}_lesson_{i}"
                            lesson_title = lesson.get("title", f"Lesson {i+1}")
                            
                            if lesson_id not in entity_ids:
                                lesson_entity = {
                                    "id": lesson_id,
                                    "type": "lesson",
                                    "name": lesson_title,
                                    "description": lesson.get("content", ""),
                                    "hierarchy_level": "branch",
                                    "properties": {
                                        "importance": 7,
                                        "keywords": lesson.get("keywords", []),
                                        "category": "lesson",
                                        "sources": ["module_structure"],
                                        "source_type": "course",
                                        "parent_module": module_key,
                                        "enrichment_status": "source",
                                        "resources": {
                                            "visualizations": [],
                                            "references": [],
                                            "examples": []
                                        }
                                    }
                                }
                                entities.append(lesson_entity)
                                entity_ids.add(lesson_id)
        
        # Extract concepts from top-level concepts
        concepts = fused_context.get("concepts", [])
        if isinstance(concepts, list):
            for i, concept in enumerate(concepts):
                if isinstance(concept, dict):
                    concept_id = f"concept_{i}"
                    concept_name = concept.get("name", f"Concept {i+1}")
                    
                    if concept_id not in entity_ids and concept_name:
                        concept_entity = {
                            "id": concept_id,
                            "type": "concept",
                            "name": concept_name,
                            "description": concept.get("description", ""),
                            "hierarchy_level": "branch",
                            "properties": {
                                "importance": 7,
                                "keywords": [concept_name],
                                "category": "concept",
                                "sources": ["concepts"],
                                "source_type": "content",
                                "enrichment_status": "source",
                                "resources": {
                                    "visualizations": [],
                                    "references": [],
                                    "examples": []
                                }
                            }
                        }
                        entities.append(concept_entity)
                        entity_ids.add(concept_id)
                elif isinstance(concept, str):
                    concept_id = f"concept_{i}"
                    
                    if concept_id not in entity_ids and concept:
                        concept_entity = {
                            "id": concept_id,
                            "type": "concept",
                            "name": concept,
                            "description": f"Concept: {concept}",
                            "hierarchy_level": "branch",
                            "properties": {
                                "importance": 6,
                                "keywords": [concept],
                                "category": "concept",
                                "sources": ["concepts"],
                                "source_type": "content",
                                "enrichment_status": "source",
                                "resources": {
                                    "visualizations": [],
                                    "references": [],
                                    "examples": []
                                }
                            }
                        }
                        entities.append(concept_entity)
                        entity_ids.add(concept_id)
        elif isinstance(concepts, dict):
            for concept_key, concept_value in concepts.items():
                concept_id = f"concept_{concept_key.replace(' ', '_').lower()}"
                
                if concept_id not in entity_ids and concept_key:
                    if isinstance(concept_value, dict):
                        concept_desc = concept_value.get("description", "")
                    else:
                        concept_desc = str(concept_value) if concept_value else ""
                    
                    concept_entity = {
                        "id": concept_id,
                        "type": "concept",
                        "name": concept_key,
                        "description": concept_desc,
                        "hierarchy_level": "branch",
                        "properties": {
                            "importance": 7,
                            "keywords": [concept_key],
                            "category": "concept",
                            "sources": ["concepts"],
                            "source_type": "content",
                            "enrichment_status": "source",
                            "resources": {
                                "visualizations": [],
                                "references": [],
                                "examples": []
                            }
                        }
                    }
                    entities.append(concept_entity)
                    entity_ids.add(concept_id)
        
        # Extract relationships as reference entities
        relationships = fused_context.get("relationships", [])
        if isinstance(relationships, list):
            for i, relation in enumerate(relationships):
                if isinstance(relation, dict):
                    source = relation.get("source", "")
                    target = relation.get("target", "")
                    rel_type = relation.get("relationship_type", "related_to")
                    
                    if source and target:
                        # Add source and target as entities if they don't exist
                        source_id = f"entity_{source.replace(' ', '_').lower()}"
                        if source_id not in entity_ids:
                            source_entity = {
                                "id": source_id,
                                "type": "concept",
                                "name": source,
                                "description": f"Entity: {source}",
                                "hierarchy_level": "branch",
                                "properties": {
                                    "importance": 6,
                                    "keywords": [source],
                                    "category": "concept",
                                    "sources": ["relationships"],
                                    "source_type": "relationship",
                                    "enrichment_status": "source",
                                    "resources": {
                                        "visualizations": [],
                                        "references": [],
                                        "examples": []
                                    }
                                }
                            }
                            entities.append(source_entity)
                            entity_ids.add(source_id)
                        
                        target_id = f"entity_{target.replace(' ', '_').lower()}"
                        if target_id not in entity_ids:
                            target_entity = {
                                "id": target_id,
                                "type": "concept",
                                "name": target,
                                "description": f"Entity: {target}",
                                "hierarchy_level": "branch",
                                "properties": {
                                    "importance": 6,
                                    "keywords": [target],
                                    "category": "concept",
                                    "sources": ["relationships"],
                                    "source_type": "relationship",
                                    "enrichment_status": "source",
                                    "resources": {
                                        "visualizations": [],
                                        "references": [],
                                        "examples": []
                                    }
                                }
                            }
                            entities.append(target_entity)
                            entity_ids.add(target_id)
        
        logger.info("Extracted %s entities from fused context", len(entities))
        return entities
    
    def _extract_relationships(self, fused_context: Dict[str, Any], entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities from the fused context.
        
        Args:
            fused_context (Dict[str, Any]): The fused context data
            entities (List[Dict[str, Any]]): The extracted entities
            
        Returns:
            List[Dict[str, Any]]: List of relationships between entities
        """
        relationships = []
        entity_map = {entity["id"]: entity for entity in entities}
        entity_name_to_id = {}
        
        # Build a map from entity names to IDs
        for entity in entities:
            entity_name = entity["name"].lower()
            if entity_name not in entity_name_to_id:
                entity_name_to_id[entity_name] = []
            entity_name_to_id[entity_name].append(entity["id"])
        
        # Connect the domain to all module entities
        domain_id = "domain_0"
        for entity in entities:
            if entity["type"] == "module" and domain_id in entity_map:
                relationships.append({
                    "source": domain_id,
                    "target": entity["id"],
                    "type": "contains",
                    "properties": {
                        "description": f"Course domain contains module: {entity['name']}",
                        "strength": 0.9,
                        "hierarchical": True,
                        "sources": ["module_structure"],
                        "source_type": "course",
                        "bidirectional": False
                    }
                })
        
        # Process relationships from the fused context
        fused_relationships = fused_context.get("relationships", [])
        if isinstance(fused_relationships, list):
            for relation in fused_relationships:
                if isinstance(relation, dict):
                    source_name = relation.get("source", "").lower()
                    target_name = relation.get("target", "").lower()
                    rel_type = relation.get("relationship_type", "related_to")
                    sources = relation.get("sources", ["relationships"])
                    confidence = relation.get("confidence", 0.8)
                    
                    # Find source and target entities by name
                    source_ids = entity_name_to_id.get(source_name, [])
                    target_ids = entity_name_to_id.get(target_name, [])
                    
                    if not source_ids:
                        # Check for entity_name pattern
                        source_ids = entity_name_to_id.get(f"entity_{source_name.replace(' ', '_')}", [])
                    if not target_ids:
                        # Check for entity_name pattern
                        target_ids = entity_name_to_id.get(f"entity_{target_name.replace(' ', '_')}", [])
                    
                    # Use the first found entity for source and target
                    if source_ids and target_ids:
                        source_id = source_ids[0]
                        target_id = target_ids[0]
                        
                        # Create the relationship
                        relationships.append({
                            "source": source_id,
                            "target": target_id,
                            "type": rel_type,
                            "properties": {
                                "description": f"Relationship from {source_name} to {target_name}: {rel_type}",
                                "strength": confidence,
                                "hierarchical": rel_type in ["contains", "is_part_of", "has_part"],
                                "sources": sources,
                                "source_type": "relationship",
                                "bidirectional": rel_type in ["same_as", "similar_to", "related_to"]
                            }
                        })
        
        # Create relationships between modules and lessons
        for entity in entities:
            if entity["type"] == "lesson":
                parent_module_name = entity["properties"].get("parent_module", "")
                if parent_module_name:
                    module_id = f"module_{parent_module_name.replace(' ', '_').lower()}"
                    if module_id in entity_map:
                        relationships.append({
                            "source": module_id,
                            "target": entity["id"],
                            "type": "contains",
                            "properties": {
                                "description": f"Module {parent_module_name} contains lesson: {entity['name']}",
                                "strength": 0.8,
                                "hierarchical": True,
                                "sources": ["module_structure"],
                                "source_type": "course",
                                "bidirectional": False
                            }
                        })
        
        # Create relationships between concepts with the same name or similar names
        concept_entities = [e for e in entities if e["type"] == "concept"]
        for i in range(len(concept_entities)):
            for j in range(i + 1, len(concept_entities)):
                concept1 = concept_entities[i]
                concept2 = concept_entities[j]
                name1 = concept1["name"].lower()
                name2 = concept2["name"].lower()
                
                # Check for exact name match
                if name1 == name2:
                    relationships.append({
                        "source": concept1["id"],
                        "target": concept2["id"],
                        "type": "same_as",
                        "properties": {
                            "description": f"Same concept with different sources: {name1}",
                            "strength": 1.0,
                            "hierarchical": False,
                            "sources": ["analysis"],
                            "source_type": "system",
                            "bidirectional": True
                        }
                    })
                # Check for similar names or one being substring of the other
                elif name1 in name2 or name2 in name1:
                    relationships.append({
                        "source": concept1["id"],
                        "target": concept2["id"],
                        "type": "similar_to",
                        "properties": {
                            "description": f"Similar concepts: {concept1['name']} and {concept2['name']}",
                            "strength": 0.8,
                            "hierarchical": False,
                            "sources": ["analysis"],
                            "source_type": "system",
                            "bidirectional": True
                        }
                    })
        
        logger.info("Extracted %s relationships from fused context", len(relationships))
        return relationships
    
    def _build_hierarchy(self, entities: List[Dict[str, Any]], course_structure: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Build a hierarchical structure from the entities and course structure.
        
        Args:
            entities (List[Dict[str, Any]]): List of entities
            course_structure (Dict[str, List[str]]): Base course structure
            
        Returns:
            Dict[str, List[str]]: Completed hierarchical structure with explicit hierarchical relationships
        """
        hierarchy = course_structure.copy()
        
        # Add entities to the hierarchy based on their level
        for entity in entities:
            entity_id = entity.get("id", "")
            hierarchy_level = entity.get("hierarchy_level", "")
            
            if entity_id and hierarchy_level in hierarchy and entity_id not in hierarchy[hierarchy_level]:
                hierarchy[hierarchy_level].append(entity_id)
        
        # Collect entities by hierarchy level
        root_entities = [e for e in entities if e.get("hierarchy_level") == "root"]
        trunk_entities = [e for e in entities if e.get("hierarchy_level") == "trunk"]
        branch_entities = [e for e in entities if e.get("hierarchy_level") == "branch"]
        leaf_entities = [e for e in entities if e.get("hierarchy_level") == "leaf"]
        resource_entities = [e for e in entities if e.get("hierarchy_level") == "resource"]
        
        # Track explicitly created relationships to avoid duplicates
        created_relationships = set()
        
        # Ensure we have root entities
        if not root_entities:
            # Create a default root if none exists
            root_name = "Course Domain"
            root_id = f"domain_{hash(root_name) % 10000}"
            root_entity = {
                "id": root_id,
                "name": root_name,
                "type": "domain",
                "description": "The domain encompassing all course content",
                "hierarchy_level": "root",
                "properties": {
                    "importance": 10,
                    "keywords": ["course", "domain", "overview"],
                    "category": "domain",
                    "enrichment_status": "generated"
                },
                "sources": ["generated"],
                "source_type": "system"
            }
            entities.append(root_entity)
            root_entities = [root_entity]
            hierarchy["root"].append(root_id)
        
        # Ensure proper hierarchy with guaranteed connections
        
        # 1. Every root node connects to trunk nodes
        for root in root_entities:
            root_id = root.get("id", "")
            connected = False
            
            # Try to find trunk nodes related to this root
            for trunk in trunk_entities:
                trunk_id = trunk.get("id", "")
                trunk_name = trunk.get("name", "").lower()
                trunk_desc = trunk.get("description", "").lower()
                root_name = root.get("name", "").lower()
                
                # Check if trunk node is related to this root node
                is_related = (
                    root_name in trunk_name or 
                    root_name in trunk_desc or
                    self._are_semantically_related(root, trunk)
                )
                
                if is_related and (root_id, trunk_id) not in created_relationships:
                    created_relationships.add((root_id, trunk_id))
                    
                    # Create "contains" relationship
                    self._add_hierarchical_relationship(
                        root_id, trunk_id, 
                        "contains", 
                        f"{root.get('name')} contains {trunk.get('name')}", 
                        0.9
                    )
                    connected = True
            
            # If no connections were found, connect to some trunk nodes
            if not connected and trunk_entities:
                # Get a sample of trunk entities to connect to (up to 5)
                sample_size = min(5, len(trunk_entities))
                sample_trunk_entities = trunk_entities[:sample_size]
                
                for trunk in sample_trunk_entities:
                    trunk_id = trunk.get("id", "")
                    
                    if (root_id, trunk_id) not in created_relationships:
                        created_relationships.add((root_id, trunk_id))
                        
                        # Create "contains" relationship
                        self._add_hierarchical_relationship(
                            root_id, trunk_id, 
                            "contains", 
                            f"{root.get('name')} encompasses {trunk.get('name')}", 
                            0.8
                        )
        
        # 2. Every trunk node connects to branch nodes
        for trunk in trunk_entities:
            trunk_id = trunk.get("id", "")
            connected = False
            
            # Try to find branch nodes related to this trunk
            for branch in branch_entities:
                branch_id = branch.get("id", "")
                branch_name = branch.get("name", "").lower()
                branch_desc = branch.get("description", "").lower()
                trunk_name = trunk.get("name", "").lower()
                
                # Check if branch node is related to this trunk node
                is_related = (
                    trunk_name in branch_name or 
                    trunk_name in branch_desc or
                    self._are_semantically_related(trunk, branch)
                )
                
                if is_related and (trunk_id, branch_id) not in created_relationships:
                    created_relationships.add((trunk_id, branch_id))
                    
                    # Create "implements" relationship
                    self._add_hierarchical_relationship(
                        trunk_id, branch_id, 
                        "implements", 
                        f"{branch.get('name')} implements concepts from {trunk.get('name')}", 
                        0.85
                    )
                    connected = True
            
            # If no connections were found, connect to some branch nodes
            if not connected and branch_entities:
                # Get a sample of branch entities to connect to (up to 3)
                sample_size = min(3, len(branch_entities))
                sample_branch_entities = branch_entities[:sample_size]
                
                for branch in sample_branch_entities:
                    branch_id = branch.get("id", "")
                    
                    if (trunk_id, branch_id) not in created_relationships:
                        created_relationships.add((trunk_id, branch_id))
                        
                        # Create "implements" relationship
                        self._add_hierarchical_relationship(
                            trunk_id, branch_id, 
                            "implements", 
                            f"{branch.get('name')} is derived from {trunk.get('name')}", 
                            0.8
                        )
            
            # If still no branch nodes, create direct connections to leaf nodes
            if not connected and not branch_entities and leaf_entities:
                # Get a sample of leaf entities to connect to (up to 3)
                sample_size = min(3, len(leaf_entities))
                sample_leaf_entities = leaf_entities[:sample_size]
                
                for leaf in sample_leaf_entities:
                    leaf_id = leaf.get("id", "")
                    
                    if (trunk_id, leaf_id) not in created_relationships:
                        created_relationships.add((trunk_id, leaf_id))
                        
                        # Create "applies" relationship
                        self._add_hierarchical_relationship(
                            trunk_id, leaf_id, 
                            "applies", 
                            f"{leaf.get('name')} applies concepts from {trunk.get('name')}", 
                            0.75
                        )
        
        # 3. Every branch node connects to leaf nodes
        for branch in branch_entities:
            branch_id = branch.get("id", "")
            connected = False
            
            # Try to find leaf nodes related to this branch
            for leaf in leaf_entities:
                leaf_id = leaf.get("id", "")
                leaf_name = leaf.get("name", "").lower()
                leaf_desc = leaf.get("description", "").lower()
                branch_name = branch.get("name", "").lower()
                
                # Check if leaf node is related to this branch node
                is_related = (
                    branch_name in leaf_name or 
                    branch_name in leaf_desc or
                    self._are_semantically_related(branch, leaf)
                )
                
                if is_related and (branch_id, leaf_id) not in created_relationships:
                    created_relationships.add((branch_id, leaf_id))
                    
                    # Create "applies" relationship
                    self._add_hierarchical_relationship(
                        branch_id, leaf_id, 
                        "applies", 
                        f"{leaf.get('name')} applies {branch.get('name')}", 
                        0.8
                    )
                    connected = True
            
            # If no connections were found, connect to some leaf nodes
            if not connected and leaf_entities:
                # Get a sample of leaf entities to connect to (up to 3)
                sample_size = min(3, len(leaf_entities))
                sample_leaf_entities = leaf_entities[:sample_size]
                
                for leaf in sample_leaf_entities:
                    leaf_id = leaf.get("id", "")
                    
                    if (branch_id, leaf_id) not in created_relationships:
                        created_relationships.add((branch_id, leaf_id))
                        
                        # Create "applies" relationship
                        self._add_hierarchical_relationship(
                            branch_id, leaf_id, 
                            "applies", 
                            f"{leaf.get('name')} applies concepts from {branch.get('name')}", 
                            0.8
                        )
        
        # 4. Connect resource entities to relevant other entities
        for resource in resource_entities:
            resource_id = resource.get("id", "")
            resource_name = resource.get("name", "").lower()
            resource_desc = resource.get("description", "").lower()
            resource_type = resource.get("type", "").lower()
            connected = False
            
            # Connect based on resource type
            if "definition" in resource_type:
                # Connect definitions to concepts (prefer trunk)
                for trunk in trunk_entities:
                    trunk_id = trunk.get("id", "")
                    trunk_name = trunk.get("name", "").lower()
                    
                    if resource_name in trunk_name or trunk_name in resource_name:
                        connected = True
                        if (trunk_id, resource_id) not in created_relationships:
                            created_relationships.add((trunk_id, resource_id))
                            
                            # Create "defines" relationship
                            self._add_hierarchical_relationship(
                                trunk_id, resource_id, 
                                "defines", 
                                f"Definition of {resource.get('name')} clarifies {trunk.get('name')}", 
                                0.9
                            )
            
            elif "visualization" in resource_type:
                # Connect visualizations to concepts or methods
                target_entities = trunk_entities + branch_entities
                
                for entity in target_entities:
                    entity_id = entity.get("id", "")
                    entity_name = entity.get("name", "").lower()
                    entity_desc = entity.get("description", "").lower()
                    
                    if (resource_name in entity_name or 
                        resource_name in entity_desc or 
                        entity_name in resource_name or
                        entity_name in resource_desc):
                        
                        connected = True
                        if (entity_id, resource_id) not in created_relationships:
                            created_relationships.add((entity_id, resource_id))
                            
                            # Create "visualizes" relationship
                            self._add_hierarchical_relationship(
                                entity_id, resource_id, 
                                "visualizes", 
                                f"Visualization illustrates {entity.get('name')}", 
                                0.85
                            )
            
            elif "reference" in resource_type:
                # Connect references to concepts or methods
                target_entities = trunk_entities + branch_entities
                
                for entity in target_entities:
                    entity_id = entity.get("id", "")
                    entity_desc = entity.get("description", "").lower()
                    
                    if resource_name in entity_desc:
                        connected = True
                        if (entity_id, resource_id) not in created_relationships:
                            created_relationships.add((entity_id, resource_id))
                            
                            # Create "references" relationship
                            self._add_hierarchical_relationship(
                                entity_id, resource_id, 
                                "references", 
                                f"{entity.get('name')} is supported by reference: {resource.get('name')}", 
                                0.7
                            )
            
            # If still not connected, try to connect to any relevant entity
            if not connected:
                # Try first with leaf nodes (examples)
                for leaf in leaf_entities:
                    leaf_id = leaf.get("id", "")
                    leaf_name = leaf.get("name", "").lower()
                    
                    if resource_name in leaf_name or leaf_name in resource_name:
                        connected = True
                        if (leaf_id, resource_id) not in created_relationships:
                            created_relationships.add((leaf_id, resource_id))
                            
                            # Create relationship
                            self._add_hierarchical_relationship(
                                leaf_id, resource_id, 
                                "related_to", 
                                f"{resource.get('name')} relates to {leaf.get('name')}", 
                                0.7
                            )
                            break
                
                # If still not connected, connect to a trunk node
                if not connected and trunk_entities:
                    trunk = trunk_entities[0]  # Connect to the first trunk node
                    trunk_id = trunk.get("id", "")
                    
                    if (trunk_id, resource_id) not in created_relationships:
                        created_relationships.add((trunk_id, resource_id))
                        
                        # Create relationship
                        self._add_hierarchical_relationship(
                            trunk_id, resource_id, 
                            "related_to", 
                            f"{resource.get('name')} supports course concepts", 
                            0.6
                        )
        
        # 5. Add horizontal connections between nodes at the same level for a richer graph
        
        # Connect related trunk nodes (concepts)
        self._add_horizontal_connections(trunk_entities, created_relationships, "related_to", 0.7)
        
        # Connect related branch nodes (methods)
        self._add_horizontal_connections(branch_entities, created_relationships, "related_to", 0.65)
        
        # Connect related leaf nodes (examples)
        self._add_horizontal_connections(leaf_entities, created_relationships, "related_to", 0.6)
        
        return hierarchy
    
    def _add_horizontal_connections(self, entities: List[Dict[str, Any]], created_relationships: Set[Tuple[str, str]], 
                                   rel_type: str = "related_to", strength: float = 0.7) -> None:
        """
        Add horizontal connections between entities at the same hierarchy level.
        
        Args:
            entities (List[Dict[str, Any]]): List of entities at the same level
            created_relationships (Set[Tuple[str, str]]): Set of already created relationships
            rel_type (str): Type of relationship to create
            strength (float): Strength of the relationship
        """
        # Only process if we have enough entities
        if len(entities) <= 1:
            return
            
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get("type", "")
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # Connect entities of the same type
        for entity_type, type_entities in entities_by_type.items():
            # Skip if not enough entities of this type
            if len(type_entities) <= 1:
                continue
                
            # Connect similar entities
            for i, entity1 in enumerate(type_entities):
                entity1_id = entity1.get("id", "")
                entity1_name = entity1.get("name", "").lower()
                entity1_desc = entity1.get("description", "").lower()
                entity1_keywords = entity1.get("properties", {}).get("keywords", [])
                
                # Limit connections to avoid overwhelming the graph
                max_connections = 3
                connections_made = 0
                
                for j in range(i+1, len(type_entities)):
                    entity2 = type_entities[j]
                    entity2_id = entity2.get("id", "")
                    entity2_name = entity2.get("name", "").lower()
                    entity2_desc = entity2.get("description", "").lower()
                    entity2_keywords = entity2.get("properties", {}).get("keywords", [])
                    
                    # Skip if already connected
                    if (entity1_id, entity2_id) in created_relationships or (entity2_id, entity1_id) in created_relationships:
                        continue
                    
                    # Check for similarity
                    is_related = (
                        entity1_name in entity2_name or 
                        entity2_name in entity1_name or
                        entity1_name in entity2_desc or
                        entity2_name in entity1_desc or
                        self._are_semantically_related(entity1, entity2) or
                        any(kw.lower() in entity2_name or kw.lower() in entity2_desc for kw in entity1_keywords) or
                        any(kw.lower() in entity1_name or kw.lower() in entity1_desc for kw in entity2_keywords)
                    )
                    
                    if is_related:
                        created_relationships.add((entity1_id, entity2_id))
                        
                        # Create relationship
                        self._add_hierarchical_relationship(
                            entity1_id, entity2_id, 
                            rel_type, 
                            f"{entity1.get('name')} relates to {entity2.get('name')}", 
                            strength
                        )
                        
                        connections_made += 1
                        if connections_made >= max_connections:
                            break
    
    def _are_semantically_related(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
        """
        Check if two entities are semantically related based on keywords or categories.
        
        Args:
            entity1 (Dict[str, Any]): First entity
            entity2 (Dict[str, Any]): Second entity
        
        Returns:
            bool: True if entities are related, False otherwise
        """
        # Get keywords and categories
        keywords1 = entity1.get("properties", {}).get("keywords", [])
        keywords2 = entity2.get("properties", {}).get("keywords", [])
        category1 = entity1.get("properties", {}).get("category", "").lower()
        category2 = entity2.get("properties", {}).get("category", "").lower()
        
        # Check for matching keywords
        if any(kw1.lower() == kw2.lower() for kw1 in keywords1 for kw2 in keywords2):
            return True
        
        # Check for matching categories
        if category1 and category2 and category1 == category2:
            return True
        
        # Check entity descriptions for overlap
        desc1 = entity1.get("description", "").lower()
        desc2 = entity2.get("description", "").lower()
        
        # Simple heuristic: if there's significant word overlap, consider them related
        words1 = set(desc1.split())
        words2 = set(desc2.split())
        overlap = len(words1.intersection(words2))
        
        # If more than 30% of the words overlap, consider them related
        if overlap > 0 and (overlap / len(words1) > 0.3 or overlap / len(words2) > 0.3):
            return True
        
        return False
    
    def _add_hierarchical_relationship(self, source_id: str, target_id: str, rel_type: str, description: str, strength: float) -> None:
        """
        Add a hierarchical relationship to the relationships list.
        
        Args:
            source_id (str): Source entity ID
            target_id (str): Target entity ID
            rel_type (str): Relationship type
            description (str): Relationship description
            strength (float): Relationship strength
        """
        if not hasattr(self, "_hierarchical_relationships"):
            self._hierarchical_relationships = []
        
        self._hierarchical_relationships.append({
            "id": f"hier_{len(self._hierarchical_relationships)}",
            "source": source_id,
            "target": target_id,
            "type": rel_type,
            "properties": {
                "strength": strength,
                "description": description,
                "sources": ["hierarchical_analysis"],
                "source_type": "course",
                "hierarchical": True,
                "bidirectional": False
            }
        })
    
    def _add_temporal_information(self, entities: List[Dict[str, Any]], fused_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Add temporal information to entities based on when concepts originated.
        
        Args:
            entities (List[Dict[str, Any]]): List of entities
            fused_context (Dict[str, Any]): The fused context
            
        Returns:
            List[Dict[str, Any]]: Entities with temporal information
        """
        # Extract timeline information from fused context
        timeline = {}
        if "timeline" in fused_context and isinstance(fused_context["timeline"], dict):
            timeline = fused_context["timeline"]
        
        for i, entity in enumerate(entities):
            entity_name = entity.get("name", "").lower()
            
            # Check if we have direct timeline information for this entity
            entity_year = None
            
            # Look for the entity in the timeline
            for event in timeline.get("events", []):
                if isinstance(event, dict) and entity_name in event.get("description", "").lower():
                    entity_year = event.get("year")
                    break
            
            # If no direct information, use heuristics to assign a time period
            if entity_year is None:
                # For now, assign a default period based on the entity type
                if entity.get("type") in self.FOUNDATION_TYPES:
                    entity_year = 1900  # Default for fundamental concepts
                elif entity.get("type") in self.THEORETICAL_TYPES:
                    entity_year = 1950  # Default for theoretical concepts
                elif entity.get("type") in self.METHODOLOGICAL_TYPES:
                    entity_year = 1980  # Default for methodological concepts
                elif entity.get("type") in self.PRACTICAL_TYPES:
                    entity_year = 2000  # Default for practical applications
            
            # Assign time period based on the year
            time_period = None
            if entity_year is not None:
                for period in self.time_periods:
                    if period["start_year"] <= entity_year <= period["end_year"]:
                        time_period = period["name"]
                        break
            
            # Update the entity with temporal information
            if time_period or entity_year:
                if "properties" not in entity:
                    entity["properties"] = {}
                
                entity["properties"]["temporal"] = {
                    "year": entity_year,
                    "period": time_period
                }
            
            entities[i] = entity
        
        return entities
    
    def _add_definitions_and_resources(self, entities: List[Dict[str, Any]], fused_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Add definitions and resources to entities.
        
        Args:
            entities (List[Dict[str, Any]]): List of entities
            fused_context (Dict[str, Any]): The fused context
            
        Returns:
            List[Dict[str, Any]]: Entities with added definitions and resources
        """
        # Extract definitions and resources from fused context
        definitions = {}
        resources = {}
        
        # Look for definitions in the concepts section
        if "concepts" in fused_context and isinstance(fused_context["concepts"], list):
            for concept in fused_context["concepts"]:
                if isinstance(concept, dict) and "name" in concept:
                    concept_name = concept.get("name", "").lower()
                    
                    if "definition" in concept:
                        definitions[concept_name] = concept["definition"]
                    
                    if "resources" in concept:
                        resources[concept_name] = concept["resources"]
        
        # Add definitions and resources to entities
        for i, entity in enumerate(entities):
            entity_name = entity.get("name", "").lower()
            
            if "properties" not in entity:
                entity["properties"] = {}
            
            # Add definition if available
            if entity_name in definitions:
                entity["properties"]["definition"] = definitions[entity_name]
            
            # Add resources if available
            if entity_name in resources:
                entity["properties"]["resources"] = resources[entity_name]
            elif "resources" not in entity["properties"]:
                # Create empty resources structure
                entity["properties"]["resources"] = {
                    "visualizations": [],
                    "references": [],
                    "examples": []
                }
            
            entities[i] = entity
        
        return entities
    
    def _normalize_relationship_types(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize relationship types for consistent visualization.
        
        Args:
            relationships (List[Dict[str, Any]]): List of relationships
            
        Returns:
            List[Dict[str, Any]]: Normalized relationships
        """
        # Define standard relationship types
        standard_types = {
            "contains": "contains",
            "is_part_of": "is_part_of",
            "implements": "implements",
            "applies": "applies",
            "uses": "applies",
            "utilizes": "applies",
            "related_to": "related_to",
            "connected_to": "related_to",
            "influences": "influences",
            "affects": "influences",
            "precedes": "progression",
            "follows": "progression",
            "progresses_to": "progression"
        }
        
        normalized = []
        for rel in relationships:
            rel_copy = rel.copy()
            rel_type = rel.get("type", "related_to").lower()
            
            # Normalize to standard type
            rel_copy["type"] = standard_types.get(rel_type, rel_type)
            
            normalized.append(rel_copy)
        
        return normalized
    
    def _add_temporal_connections(self, entities: List[Dict[str, Any]], fused_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Add progression relationships based on temporal information.
        
        Args:
            entities (List[Dict[str, Any]]): List of entities
            fused_context (Dict[str, Any]): The fused context
            
        Returns:
            List[Dict[str, Any]]: Entities with temporal connections
        """
        temporal_relationships = []
        
        # Create a dictionary of entities with temporal information
        temporal_entities = {}
        for entity in entities:
            entity_id = entity.get("id", "")
            temporal_info = entity.get("properties", {}).get("temporal", {})
            
            if entity_id and temporal_info.get("year"):
                temporal_entities[entity_id] = {
                    "id": entity_id,
                    "name": entity.get("name", ""),
                    "year": temporal_info.get("year"),
                    "period": temporal_info.get("period")
                }
        
        # Sort entities by year
        sorted_entities = sorted(temporal_entities.values(), key=lambda x: x["year"])
        
        # Create progression relationships between sequential entities in the same hierarchy level
        entity_dict = {e.get("id", ""): e for e in entities}
        for i in range(len(sorted_entities) - 1):
            current = sorted_entities[i]
            next_entity = sorted_entities[i + 1]
            
            # Only create progression relationships between entities of the same hierarchy level
            # or between theoretical concepts that build on each other
            current_hierarchy = entity_dict.get(current["id"], {}).get("hierarchy_level", "")
            next_hierarchy = entity_dict.get(next_entity["id"], {}).get("hierarchy_level", "")
            
            if (current_hierarchy == next_hierarchy) or (current_hierarchy == "trunk" and next_hierarchy == "trunk"):
                # Create progression relationship
                temporal_relationships.append({
                    "id": f"temp_{len(temporal_relationships)}",
                    "source": current["id"],
                    "target": next_entity["id"],
                    "type": "progression",
                    "properties": {
                        "strength": 0.7,
                        "description": f"{current['name']} chronologically precedes {next_entity['name']}",
                        "sources": ["temporal_analysis"],
                        "source_type": "course",
                        "temporal": True,
                        "bidirectional": False,
                        "year_diff": next_entity["year"] - current["year"]
                    }
                })
        
        return temporal_relationships 