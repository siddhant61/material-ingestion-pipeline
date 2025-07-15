"""
Supervisor Agent Schemas

This module defines the schemas used by the SupervisorAgent for
quality checks, consistency checks, and refinements.
"""

import json
from typing import Dict, List, Any, Optional, Union, Type

class BaseSchema:
    """Base class for all schemas in the supervisor agent."""
    
    @classmethod
    def format(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format data according to the schema.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted data
        """
        return data

class QualityCheckSchema(BaseSchema):
    """Schema for quality check results."""
    
    @classmethod
    def format(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format quality check data according to the schema.
        
        Args:
            data: Quality check data to format
            
        Returns:
            Formatted quality check data
        """
        # Ensure all required fields are present
        formatted_data = {
            "needs_refinement": data.get("needs_refinement", False),
            "score": data.get("score", 0.0),
            "issues": data.get("issues", []),
            "strengths": data.get("strengths", []),
            "recommendations": data.get("recommendations", [])
        }
        
        return formatted_data

class ConsistencyCheckSchema(BaseSchema):
    """Schema for consistency check results."""
    
    @classmethod
    def format(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format consistency check data according to the schema.
        
        Args:
            data: Consistency check data to format
            
        Returns:
            Formatted consistency check data
        """
        # Ensure all required fields are present
        formatted_data = {
            "needs_refinement": data.get("needs_refinement", False),
            "score": data.get("score", 0.0),
            "issues": data.get("issues", []),
            "consistent_elements": data.get("consistent_elements", []),
            "recommendations": data.get("recommendations", [])
        }
        
        return formatted_data

class RefinementSchema(BaseSchema):
    """Schema for refinement results."""
    
    @classmethod
    def format(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format refinement data according to the schema.
        
        Args:
            data: Refinement data to format
            
        Returns:
            Formatted refinement data
        """
        # Handle case where data is already in correct format
        if not isinstance(data, dict):
            data = {"content": data}
        
        # Ensure all required fields are present
        if "metadata" not in data:
            data["metadata"] = {}
        
        # Add refinement metadata
        data["metadata"]["was_refined"] = True
        data["metadata"]["refinement_timestamp"] = data["metadata"].get(
            "refinement_timestamp", 
            None
        )
        
        return data

class GuidelineSchema(BaseSchema):
    """Schema for supervision guidelines."""
    
    QUALITY_GUIDELINES = {
        "general": {
            "accuracy": {
                "description": "Information should be accurate and factually correct",
                "threshold": 0.9
            },
            "completeness": {
                "description": "All required information should be present",
                "threshold": 0.8
            },
            "relevance": {
                "description": "Information should be relevant to the educational context",
                "threshold": 0.85
            },
            "clarity": {
                "description": "Information should be clear and understandable",
                "threshold": 0.75
            },
            "educational_value": {
                "description": "Content should have clear educational value",
                "threshold": 0.8
            }
        },
        "course_context": {
            "completeness": {
                "description": "All schema fields should be populated",
                "threshold": 0.9
            },
            "structure": {
                "description": "Course structure should be clearly defined",
                "threshold": 0.85
            }
        },
        "document_loader": {
            "extraction_quality": {
                "description": "Text and image extraction should be high quality",
                "threshold": 0.8
            },
            "metadata_extraction": {
                "description": "Metadata should be comprehensive",
                "threshold": 0.75
            }
        },
        "transcript_processor": {
            "segmentation_quality": {
                "description": "Transcript segmentation should be semantically meaningful",
                "threshold": 0.85
            },
            "speaker_identification": {
                "description": "Speakers should be correctly identified",
                "threshold": 0.7
            }
        },
        "slide_processor": {
            "content_extraction": {
                "description": "Slide content should be fully extracted",
                "threshold": 0.8
            },
            "structure_preservation": {
                "description": "Slide structure should be preserved",
                "threshold": 0.75
            }
        },
        "context_fusion": {
            "integration_quality": {
                "description": "Content sources should be well integrated",
                "threshold": 0.85
            },
            "fact_verification": {
                "description": "No new information should be added",
                "threshold": 0.95
            }
        }
    }
    
    CONSISTENCY_GUIDELINES = {
        "general": {
            "schema_consistency": {
                "description": "Output schemas should be consistent across agents",
                "threshold": 0.95
            },
            "terminology_consistency": {
                "description": "Terminology should be consistent across all outputs",
                "threshold": 0.9
            },
            "format_consistency": {
                "description": "Data formats should be consistent",
                "threshold": 0.95
            }
        }
    }
    
    REFINEMENT_GUIDELINES = {
        "general": {
            "preserve_original": {
                "description": "Preserve original content where possible",
                "threshold": 0.9
            },
            "improve_clarity": {
                "description": "Improve clarity without changing meaning",
                "threshold": 0.8
            },
            "enhance_structure": {
                "description": "Enhance structural elements for better organization",
                "threshold": 0.85
            }
        },
        "context_fusion": {
            "source_attribution": {
                "description": "Ensure all content has clear source attribution",
                "threshold": 0.95
            },
            "no_hallucination": {
                "description": "Remove any hallucinated content not in source materials",
                "threshold": 0.99
            }
        }
    }
    
    @classmethod
    def get_default_guidelines(cls) -> Dict[str, Any]:
        """
        Get the default supervision guidelines.
        
        Returns:
            Default supervision guidelines
        """
        return {
            "quality": cls.QUALITY_GUIDELINES,
            "consistency": cls.CONSISTENCY_GUIDELINES,
            "refinement": cls.REFINEMENT_GUIDELINES
        } 