"""
Context Fusion

This module provides functionality for fusing multiple content sources (course context, transcripts, slides)
into a unified context representation for educational materials.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

# Constants
VISUAL_CONTEXT_SNIPPET_LENGTH = 200  # Maximum characters to store from visual descriptions

# Common words to exclude from concept extraction (lowercase)
COMMON_WORDS_TO_EXCLUDE = {
    'the', 'this', 'that', 'these', 'those', 'with', 'from', 'and', 'for',
    'are', 'was', 'were', 'has', 'have', 'but', 'however', 'also', 'can',
    'will', 'would', 'should', 'could', 'may', 'might', 'must', 'when',
    'where', 'which', 'who', 'how', 'what', 'why', 'all', 'each', 'every',
    'some', 'any', 'many', 'few', 'more', 'most', 'less', 'such', 'very'
}

class ContextFusion:
    """
    Processor that fuses multiple content sources into a unified context representation.
    
    Features:
    1. Integrates course context, transcript data, and slide data
    2. Establishes cross-source relationships between concepts
    3. Creates a unified timeline of educational content
    4. Constructs a complete concept hierarchy
    5. Builds a dependency graph of learning material
    """
    
    def __init__(self):
        """
        Initialize the context fusion processor.
        """
        self.course_context = {}
        self.transcript_data = {}
        self.slide_data = {}
        self.vision_data = {}
        
    def load_data(self, course_context_path: str, transcript_results_path: str, slide_results_path: str, vision_results_path: str = None) -> bool:
        """
        Load data from all sources.
        
        Args:
            course_context_path (str): Path to course context JSON file
            transcript_results_path (str): Path to transcript results JSON file
            slide_results_path (str): Path to slide results JSON file
            vision_results_path (str, optional): Path to vision results JSON file
            
        Returns:
            bool: True if all data loaded successfully
        """
        try:
            # Load course context
            with open(course_context_path, 'r', encoding='utf-8') as f:
                self.course_context = json.load(f)
            logger.info(f"Loaded course context from {course_context_path}")
            
            # Load transcript data
            with open(transcript_results_path, 'r', encoding='utf-8') as f:
                self.transcript_data = json.load(f)
            logger.info(f"Loaded transcript data from {transcript_results_path}")
            
            # Load slide data
            with open(slide_results_path, 'r', encoding='utf-8') as f:
                self.slide_data = json.load(f)
            logger.info(f"Loaded slide data from {slide_results_path}")
            
            # Load vision data if provided
            if vision_results_path:
                with open(vision_results_path, 'r', encoding='utf-8') as f:
                    self.vision_data = json.load(f)
                logger.info(f"Loaded vision data from {vision_results_path}")
            else:
                self.vision_data = {}
                logger.info("No vision data provided")
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
    
    def load_transcript_files(self, transcript_dir: str) -> List[Dict[str, Any]]:
        """
        Load all processed transcript files from a directory.
        
        Args:
            transcript_dir (str): Directory containing processed transcript files
            
        Returns:
            List[Dict[str, Any]]: List of transcript data objects
        """
        transcript_dir = Path(transcript_dir)
        transcripts = []
        
        try:
            for file_path in transcript_dir.glob("*_processed.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    transcript = json.load(f)
                    transcripts.append(transcript)
            
            logger.info(f"Loaded {len(transcripts)} transcript files from {transcript_dir}")
            return transcripts
        
        except Exception as e:
            logger.error(f"Error loading transcript files: {str(e)}")
            return []
    
    def load_slide_files(self, slide_dir: str) -> List[Dict[str, Any]]:
        """
        Load all processed slide files from a directory.
        
        Args:
            slide_dir (str): Directory containing processed slide files
            
        Returns:
            List[Dict[str, Any]]: List of slide data objects
        """
        slide_dir = Path(slide_dir)
        slides = []
        
        try:
            for file_path in slide_dir.glob("*_processed.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    slide = json.load(f)
                    slides.append(slide)
            
            logger.info(f"Loaded {len(slides)} slide files from {slide_dir}")
            return slides
        
        except Exception as e:
            logger.error(f"Error loading slide files: {str(e)}")
            return []
    
    def _extract_all_concepts(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract all concepts from all data sources.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of concepts with metadata
        """
        concepts = {}
        
        # Extract concepts from course context
        if "keywords" in self.course_context:
            for keyword in self.course_context["keywords"]:
                concepts[keyword] = {
                    "name": keyword,
                    "sources": ["course_context"],
                    "importance": 5,  # High importance for course-level concepts
                    "references": 1
                }
        
        if "relationships" in self.course_context:
            for relation in self.course_context["relationships"]:
                source = relation.get("source", "")
                target = relation.get("target", "")
                rel_type = relation.get("relationship_type", "")
                
                if source and source not in concepts:
                    concepts[source] = {
                        "name": source,
                        "sources": ["course_context"],
                        "importance": 4,
                        "references": 1
                    }
                elif source:
                    concepts[source]["references"] += 1
                
                if target and target not in concepts:
                    concepts[target] = {
                        "name": target,
                        "sources": ["course_context"],
                        "importance": 4,
                        "references": 1
                    }
                elif target:
                    concepts[target]["references"] += 1
        
        # Extract concepts from transcript data
        if "transcripts" in self.transcript_data:
            for transcript_info in self.transcript_data["transcripts"]:
                if "output_file" in transcript_info:
                    try:
                        with open(transcript_info["output_file"], 'r', encoding='utf-8') as f:
                            transcript = json.load(f)
                            
                            # Process segments
                            for segment in transcript.get("segments", []):
                                for concept in segment.get("concepts", []):
                                    if concept not in concepts:
                                        concepts[concept] = {
                                            "name": concept,
                                            "sources": ["transcript"],
                                            "importance": 3,
                                            "references": 1
                                        }
                                    else:
                                        if "transcript" not in concepts[concept]["sources"]:
                                            concepts[concept]["sources"].append("transcript")
                                        concepts[concept]["references"] += 1
                                
                                for keyword in segment.get("keywords", []):
                                    if keyword not in concepts:
                                        concepts[keyword] = {
                                            "name": keyword,
                                            "sources": ["transcript"],
                                            "importance": 2,
                                            "references": 1
                                        }
                                    else:
                                        if "transcript" not in concepts[keyword]["sources"]:
                                            concepts[keyword]["sources"].append("transcript")
                                        concepts[keyword]["references"] += 1
                    except Exception as e:
                        logger.warning(f"Error extracting concepts from transcript {transcript_info.get('filename')}: {str(e)}")
        
        # Extract concepts from slide data
        if "slides" in self.slide_data:
            for slide_info in self.slide_data["slides"]:
                if "output_file" in slide_info:
                    try:
                        with open(slide_info["output_file"], 'r', encoding='utf-8') as f:
                            slide = json.load(f)
                            
                            # Process slides
                            for slide_item in slide.get("slides", []):
                                for concept in slide_item.get("concepts", []):
                                    if concept not in concepts:
                                        concepts[concept] = {
                                            "name": concept,
                                            "sources": ["slide"],
                                            "importance": 3,
                                            "references": 1
                                        }
                                    else:
                                        if "slide" not in concepts[concept]["sources"]:
                                            concepts[concept]["sources"].append("slide")
                                        concepts[concept]["references"] += 1
                                
                                for keyword in slide_item.get("keywords", []):
                                    if keyword not in concepts:
                                        concepts[keyword] = {
                                            "name": keyword,
                                            "sources": ["slide"],
                                            "importance": 2,
                                            "references": 1
                                        }
                                    else:
                                        if "slide" not in concepts[keyword]["sources"]:
                                            concepts[keyword]["sources"].append("slide")
                                        concepts[keyword]["references"] += 1
                    except Exception as e:
                        logger.warning(f"Error extracting concepts from slide {slide_info.get('filename')}: {str(e)}")
        
        # Extract concepts from vision data (Visual RAG)
        if self.vision_data and "result" in self.vision_data:
            vision_results = self.vision_data["result"]
            
            # Process each image description
            for image_path, description in vision_results.items():
                if not description or not isinstance(description, str) or "error" in description.lower():
                    continue
                
                # Extract key terms from the description as concepts
                # Simple approach: look for capitalized words and technical terms
                words = description.split()
                for i, word in enumerate(words):
                    # Look for capitalized words (potential concepts) excluding common words
                    cleaned_word = word.strip('.,!?:;()[]"\'')
                    
                    # Skip empty strings, very short words, and common articles
                    if not cleaned_word or len(cleaned_word) < 3:
                        continue
                    
                    # Skip common words using the module-level constant
                    if cleaned_word.lower() in COMMON_WORDS_TO_EXCLUDE:
                        continue
                    
                    # Only consider as concept if:
                    # 1. Contains digits (like "H2O", "1st", etc.), OR
                    # 2. Is capitalized AND not at sentence start
                    # Sentence start detection: first word OR previous word ends with sentence-ending punctuation
                    is_sentence_start = (i == 0 or (words[i-1] and words[i-1][-1] in '.!?'))
                    has_digits = any(char.isdigit() for char in cleaned_word)
                    is_capitalized = cleaned_word[0].isupper()
                    
                    # Accept if has digits, or if capitalized and not at sentence start
                    if has_digits or (is_capitalized and not is_sentence_start):
                        concept_name = cleaned_word
                        
                        if concept_name not in concepts:
                            concepts[concept_name] = {
                                "name": concept_name,
                                "sources": ["visual_rag"],
                                "importance": 3,
                                "references": 1,
                                "visual_context": description[:VISUAL_CONTEXT_SNIPPET_LENGTH]
                            }
                        else:
                            if "visual_rag" not in concepts[concept_name]["sources"]:
                                concepts[concept_name]["sources"].append("visual_rag")
                                # Add visual_context if not already present
                                if "visual_context" not in concepts[concept_name]:
                                    concepts[concept_name]["visual_context"] = description[:VISUAL_CONTEXT_SNIPPET_LENGTH]
                            concepts[concept_name]["references"] += 1
            
            logger.info(f"Extracted concepts from {len(vision_results)} image descriptions (Visual RAG)")
        
        # Calculate a weighted importance score based on references and sources
        for concept_name, concept_data in concepts.items():
            source_weight = len(concept_data["sources"])
            reference_weight = min(5, concept_data["references"])
            
            # Adjust importance based on frequency and source diversity
            concept_data["importance"] = (
                concept_data["importance"] * 0.5 +  # Base importance
                source_weight * 1.0 +               # More sources = more important
                reference_weight * 0.5              # More references = more important
            )
        
        return concepts
    
    def _extract_all_relationships(self, concepts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract all relationships between concepts from all data sources.
        
        Args:
            concepts (Dict[str, Dict[str, Any]]): Dictionary of all concepts
            
        Returns:
            List[Dict[str, Any]]: List of concept relationships
        """
        relationships = []
        relationship_keys = set()  # Track unique relationships
        
        # Extract relationships from course context
        if "relationships" in self.course_context:
            for relation in self.course_context["relationships"]:
                source = relation.get("source", "")
                target = relation.get("target", "")
                rel_type = relation.get("relationship_type", "")
                
                if source and target:
                    rel_key = f"{source}|{target}|{rel_type}"
                    if rel_key not in relationship_keys:
                        relationship_keys.add(rel_key)
                        relationships.append({
                            "source": source,
                            "target": target,
                            "relationship_type": rel_type,
                            "sources": ["course_context"],
                            "confidence": 0.9
                        })
        
        # Extract relationships from transcript data
        if "transcripts" in self.transcript_data:
            for transcript_info in self.transcript_data["transcripts"]:
                if "output_file" in transcript_info:
                    try:
                        with open(transcript_info["output_file"], 'r', encoding='utf-8') as f:
                            transcript = json.load(f)
                            
                            # Process segments
                            for segment in transcript.get("segments", []):
                                for relationship in segment.get("relationships", []):
                                    # Parse relationship text (format: "concept1 -> concept2" or "concept1 is related to concept2")
                                    parts = self._parse_relationship_text(relationship)
                                    if parts:
                                        source, target, rel_type = parts
                                        
                                        rel_key = f"{source}|{target}|{rel_type}"
                                        if rel_key not in relationship_keys:
                                            relationship_keys.add(rel_key)
                                            relationships.append({
                                                "source": source,
                                                "target": target,
                                                "relationship_type": rel_type,
                                                "sources": ["transcript"],
                                                "confidence": 0.7
                                            })
                                        else:
                                            # Update existing relationship
                                            for rel in relationships:
                                                if rel["source"] == source and rel["target"] == target:
                                                    if "transcript" not in rel["sources"]:
                                                        rel["sources"].append("transcript")
                                                        rel["confidence"] = min(0.95, rel["confidence"] + 0.1)
                    except Exception as e:
                        logger.warning(f"Error extracting relationships from transcript {transcript_info.get('filename')}: {str(e)}")
        
        # Extract relationships from slide data
        if "slides" in self.slide_data:
            for slide_info in self.slide_data["slides"]:
                if "output_file" in slide_info:
                    try:
                        with open(slide_info["output_file"], 'r', encoding='utf-8') as f:
                            slide = json.load(f)
                            
                            # Process cross-slide relationships
                            for rel in slide.get("cross_slide_relationships", []):
                                source = rel.get("source_concept", "")
                                target = rel.get("target_concept", "")
                                rel_type = rel.get("relationship_type", "")
                                
                                if source and target:
                                    rel_key = f"{source}|{target}|{rel_type}"
                                    if rel_key not in relationship_keys:
                                        relationship_keys.add(rel_key)
                                        relationships.append({
                                            "source": source,
                                            "target": target,
                                            "relationship_type": rel_type,
                                            "sources": ["slide"],
                                            "confidence": 0.8
                                        })
                                    else:
                                        # Update existing relationship
                                        for r in relationships:
                                            if r["source"] == source and r["target"] == target:
                                                if "slide" not in r["sources"]:
                                                    r["sources"].append("slide")
                                                    r["confidence"] = min(0.95, r["confidence"] + 0.1)
                            
                            # Process slides
                            for slide_item in slide.get("slides", []):
                                for relationship in slide_item.get("relationships", []):
                                    # Parse relationship text
                                    parts = self._parse_relationship_text(relationship)
                                    if parts:
                                        source, target, rel_type = parts
                                        
                                        rel_key = f"{source}|{target}|{rel_type}"
                                        if rel_key not in relationship_keys:
                                            relationship_keys.add(rel_key)
                                            relationships.append({
                                                "source": source,
                                                "target": target,
                                                "relationship_type": rel_type,
                                                "sources": ["slide"],
                                                "confidence": 0.7
                                            })
                                        else:
                                            # Update existing relationship
                                            for rel in relationships:
                                                if rel["source"] == source and rel["target"] == target:
                                                    if "slide" not in rel["sources"]:
                                                        rel["sources"].append("slide")
                                                        rel["confidence"] = min(0.95, rel["confidence"] + 0.1)
                    except Exception as e:
                        logger.warning(f"Error extracting relationships from slide {slide_info.get('filename')}: {str(e)}")
        
        # Sort relationships by confidence
        relationships.sort(key=lambda x: x["confidence"], reverse=True)
        
        return relationships
    
    def _parse_relationship_text(self, relationship_text: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse relationship text to extract source, target, and type.
        
        Args:
            relationship_text (str): Relationship text to parse
            
        Returns:
            Optional[Tuple[str, str, str]]: Tuple of (source, target, relationship_type) or None
        """
        # Handle relationships in various formats
        
        # Format: "concept1 -> concept2"
        if "->" in relationship_text:
            parts = relationship_text.split("->")
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip(), "builds_on"
        
        # Format: "concept1 is related to concept2"
        rel_patterns = [
            ("is related to", "related_to"),
            ("builds on", "builds_on"),
            ("is part of", "part_of"),
            ("depends on", "depends_on"),
            ("extends", "extends"),
            ("includes", "includes")
        ]
        
        for pattern, rel_type in rel_patterns:
            if pattern in relationship_text.lower():
                parts = relationship_text.lower().split(pattern)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip(), rel_type
        
        # If no known pattern is found, try a simple split on common words
        for split_word in ["and", "with", "to", "from"]:
            if f" {split_word} " in relationship_text:
                parts = relationship_text.split(f" {split_word} ")
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip(), "related_to"
        
        return None
    
    def _create_timeline(self, transcripts: List[Dict[str, Any]], slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create a unified timeline of course content.
        
        Args:
            transcripts (List[Dict[str, Any]]): List of transcript data
            slides (List[Dict[str, Any]]): List of slide data
            
        Returns:
            List[Dict[str, Any]]: Unified timeline entries
        """
        timeline = []
        
        # Add transcript segments to timeline
        for transcript in transcripts:
            transcript_title = transcript.get("transcript_info", {}).get("title", "Unknown")
            
            for segment in transcript.get("segments", []):
                start_time = segment.get("start_seconds", 0)
                
                # Extract numerical part from title for sorting
                title_parts = transcript_title.split()
                sequence_num = 0
                for part in title_parts:
                    if part[0].isdigit():
                        try:
                            sequence_num = float(part.replace(',', '.'))
                            break
                        except ValueError:
                            pass
                
                timeline.append({
                    "type": "transcript",
                    "title": transcript_title,
                    "source": "transcript",
                    "segment_id": segment.get("id", ""),
                    "content": segment.get("text", ""),
                    "start_time": start_time,
                    "concepts": segment.get("concepts", []),
                    "sequence_num": sequence_num
                })
        
        # Add slides to timeline (match with transcripts where possible)
        for slide_deck in slides:
            deck_title = slide_deck.get("slide_deck_info", {}).get("title", "Unknown")
            
            # Extract numerical part from title for sorting
            title_parts = deck_title.split()
            sequence_num = 0
            for part in title_parts:
                if part[0].isdigit():
                    try:
                        sequence_num = float(part.replace(',', '.'))
                        break
                    except ValueError:
                        pass
            
            for slide in slide_deck.get("slides", []):
                # Find potential transcript segment matches
                matching_segments = slide.get("matching_transcript_segments", [])
                
                # If we have segment matches, estimate time from there
                estimated_time = 0
                for entry in timeline:
                    if entry["type"] == "transcript" and entry["segment_id"] in matching_segments:
                        estimated_time = entry["start_time"]
                        break
                
                slide_entry = {
                    "type": "slide",
                    "title": deck_title,
                    "source": "slide",
                    "slide_number": slide.get("slide_number", 0),
                    "content": slide.get("content", ""),
                    "start_time": estimated_time,
                    "concepts": slide.get("concepts", []),
                    "sequence_num": sequence_num
                }
                
                # Add visual descriptions if available
                if self.vision_data and "result" in self.vision_data:
                    vision_results = self.vision_data["result"]
                    visual_descriptions = []
                    
                    # Check if any images are associated with this slide
                    # Images typically have naming pattern: deckname_slideN_imgM.ext
                    slide_number = slide.get('slide_number')
                    
                    for image_path, description in vision_results.items():
                        # Skip if slide_number is None or less than 1
                        # Assumption: Slide decks use 1-based indexing (slides numbered 1, 2, 3, ...)
                        # This excludes None, 0, and negative values
                        # Note: If your slide deck uses 0-based indexing, adjust this to `< 0`
                        if slide_number is None or slide_number < 1:
                            continue
                        
                        # Match using multiple patterns to be robust
                        image_path_lower = image_path.lower()
                        matches = (
                            f"slide{slide_number}" in image_path_lower or
                            f"slide_{slide_number}" in image_path_lower or
                            f"slide-{slide_number}" in image_path_lower
                        )
                        
                        if matches:
                            visual_descriptions.append({
                                "image_path": image_path,
                                "description": description,
                                "source": "Visual RAG"
                            })
                    
                    if visual_descriptions:
                        slide_entry["visual_descriptions"] = visual_descriptions
                        # Mark that this entry has visual RAG content
                        # Design Note: Timeline entries use both "source" (string) and "sources" (list)
                        # - "source" indicates the primary source type (e.g., "slide", "transcript")
                        # - "sources" lists all contributing sources including enrichments like "Visual RAG"
                        # This dual approach maintains backward compatibility while supporting multi-source tracking
                        if "sources" not in slide_entry:
                            slide_entry["sources"] = [slide_entry["source"]]
                        if "Visual RAG" not in slide_entry["sources"]:
                            slide_entry["sources"].append("Visual RAG")
                
                timeline.append(slide_entry)
        
        # Sort timeline by sequence number and then by start time
        timeline.sort(key=lambda x: (x["sequence_num"], x["start_time"]))
        
        return timeline
    
    def _build_module_structure(self) -> Dict[str, Any]:
        """
        Build a structured representation of course modules.
        
        Returns:
            Dict[str, Any]: Structured course modules
        """
        module_structure = {}
        
        # Extract basic structure from course context
        if "course_structure" in self.course_context and "modules" in self.course_context["course_structure"]:
            for module in self.course_context["course_structure"]["modules"]:
                module_title = module.get("title", "Unknown")
                
                module_structure[module_title] = {
                    "title": module_title,
                    "description": module.get("description", ""),
                    "lessons": [],
                    "concepts": set(),
                    "materials": {
                        "transcripts": [],
                        "slides": []
                    }
                }
                
                # Add lessons if available
                if "lessons" in module:
                    for lesson in module["lessons"]:
                        lesson_title = lesson.get("title", "")
                        module_structure[module_title]["lessons"].append({
                            "title": lesson_title,
                            "topics": lesson.get("topics", []),
                            "learning_objectives": lesson.get("learning_objectives", []),
                            "concepts": set(),
                            "materials": {
                                "transcripts": [],
                                "slides": []
                            }
                        })
        
        # Associate transcripts with modules
        if "transcripts" in self.transcript_data:
            for transcript_info in self.transcript_data["transcripts"]:
                if "output_file" in transcript_info:
                    try:
                        # Load detailed transcript data
                        with open(transcript_info["output_file"], 'r', encoding='utf-8') as f:
                            transcript = json.load(f)
                            
                            module_name = transcript.get("alignment", {}).get("course_module", "Unknown")
                            
                            # If the module doesn't exist in our structure, add it
                            if module_name not in module_structure:
                                module_structure[module_name] = {
                                    "title": module_name,
                                    "description": "",
                                    "lessons": [],
                                    "concepts": set(),
                                    "materials": {
                                        "transcripts": [],
                                        "slides": []
                                    }
                                }
                            
                            # Add transcript to module materials
                            module_structure[module_name]["materials"]["transcripts"].append({
                                "title": transcript.get("transcript_info", {}).get("title", "Unknown"),
                                "file": transcript_info.get("output_file", ""),
                                "duration": transcript.get("transcript_info", {}).get("duration", "Unknown")
                            })
                            
                            # Extract concepts for the module
                            for segment in transcript.get("segments", []):
                                module_structure[module_name]["concepts"].update(segment.get("concepts", []))
                                
                    except Exception as e:
                        logger.warning(f"Error processing transcript for module structure: {str(e)}")
        
        # Associate slides with modules
        if "slides" in self.slide_data:
            for slide_info in self.slide_data["slides"]:
                if "output_file" in slide_info:
                    try:
                        # Load detailed slide data
                        with open(slide_info["output_file"], 'r', encoding='utf-8') as f:
                            slide = json.load(f)
                            
                            module_name = slide.get("alignment", {}).get("course_module", "Unknown")
                            
                            # If the module doesn't exist in our structure, add it
                            if module_name not in module_structure:
                                module_structure[module_name] = {
                                    "title": module_name,
                                    "description": "",
                                    "lessons": [],
                                    "concepts": set(),
                                    "materials": {
                                        "transcripts": [],
                                        "slides": []
                                    }
                                }
                            
                            # Add slide deck to module materials
                            module_structure[module_name]["materials"]["slides"].append({
                                "title": slide.get("slide_deck_info", {}).get("title", "Unknown"),
                                "file": slide_info.get("output_file", ""),
                                "slide_count": slide.get("slide_deck_info", {}).get("slide_count", 0)
                            })
                            
                            # Extract concepts for the module
                            for slide_item in slide.get("slides", []):
                                module_structure[module_name]["concepts"].update(slide_item.get("concepts", []))
                                
                    except Exception as e:
                        logger.warning(f"Error processing slide for module structure: {str(e)}")
        
        # Convert sets to lists for JSON serialization
        for module_name, module in module_structure.items():
            module["concepts"] = list(module["concepts"])
            
            for lesson in module["lessons"]:
                lesson["concepts"] = list(lesson["concepts"])
        
        return module_structure
    
    def generate_fused_context(self, output_dir: str = None) -> Dict[str, Any]:
        """
        Generate a fused context from all data sources.
        
        Args:
            output_dir (str, optional): Directory to save the fused context. Defaults to None.
            
        Returns:
            Dict[str, Any]: The fused context
        """
        logger.info("Generating fused context from all data sources...")
        
        # Load detailed transcript files if needed
        transcripts = []
        if self.transcript_data and "transcripts" in self.transcript_data:
            for transcript_info in self.transcript_data["transcripts"]:
                if "output_file" in transcript_info:
                    try:
                        with open(transcript_info["output_file"], 'r', encoding='utf-8') as f:
                            transcript = json.load(f)
                            transcripts.append(transcript)
                    except Exception as e:
                        logger.warning(f"Error loading transcript {transcript_info.get('output_file')}: {str(e)}")
        
        # Load detailed slide files if needed
        slides = []
        if self.slide_data and "slides" in self.slide_data:
            for slide_info in self.slide_data["slides"]:
                if "output_file" in slide_info:
                    try:
                        with open(slide_info["output_file"], 'r', encoding='utf-8') as f:
                            slide = json.load(f)
                            slides.append(slide)
                    except Exception as e:
                        logger.warning(f"Error loading slide {slide_info.get('output_file')}: {str(e)}")
        
        # Generate the fused context components
        concepts = self._extract_all_concepts()
        relationships = self._extract_all_relationships(concepts)
        timeline = self._create_timeline(transcripts, slides)
        module_structure = self._build_module_structure()
        
        # Count visual RAG concepts
        visual_rag_concept_count = sum(1 for c in concepts.values() if "visual_rag" in c.get("sources", []))
        vision_image_count = len(self.vision_data.get("result", {})) if self.vision_data else 0
        
        # Prepare sources list
        sources = ["course_context", "transcripts", "slides"]
        if self.vision_data and vision_image_count > 0:
            sources.append("visual_rag")
        
        # Construct the final fused context
        fused_context = {
            "course_info": self.course_context.get("course_info", {}),
            "module_structure": module_structure,
            "concepts": list(concepts.values()),
            "relationships": relationships,
            "timeline": timeline,
            "statistics": {
                "concept_count": len(concepts),
                "relationship_count": len(relationships),
                "timeline_entry_count": len(timeline),
                "module_count": len(module_structure),
                "transcript_count": len(transcripts),
                "slide_count": len(slides),
                "vision_image_count": vision_image_count,
                "visual_rag_concept_count": visual_rag_concept_count
            },
            "metadata": {
                "fusion_version": "1.1",
                "sources": sources,
                "visual_rag_enabled": bool(self.vision_data and vision_image_count > 0)
            }
        }
        
        # Save the fused context if output directory is provided
        if output_dir:
            output_dir = Path(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = output_dir / "fused_context.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(fused_context, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved fused context to {output_file}")
        
        return fused_context 