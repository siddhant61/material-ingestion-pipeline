"""
Structure Refiner

This module provides functionality for improving the structural quality of agent outputs.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

class StructureRefiner:
    """
    Refiner for improving output structure.
    
    This refiner addresses issues related to:
    - Nesting level (overly nested or flat structures)
    - Structural organization
    - Content grouping
    - Hierarchical relationships
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the StructureRefiner.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        self.max_allowed_depth = self.config.get("max_depth", 5)
        logger.info(f"StructureRefiner initialized with max_depth: {self.max_allowed_depth}")
    
    def refine(self, 
              content: Dict[str, Any], 
              issues: List[Dict[str, Any]], 
              guidelines: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refine content to improve structure.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issues (List[Dict[str, Any]]): Structure issues to address
            guidelines (Dict[str, Any]): Refinement guidelines
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: Refined content and list of refinements made
        """
        # Make a working copy to avoid modifying the original
        refined = content.copy()
        refinements = []
        
        # Check if structure needs improvement regardless of specific issues
        max_depth = self._calculate_max_depth(refined)
        
        # If nesting is too deep, flag it for manual review
        if max_depth > self.max_allowed_depth:
            if "metadata" not in refined:
                refined["metadata"] = {}
                
            if "quality_flags" not in refined["metadata"]:
                refined["metadata"]["quality_flags"] = []
                
            refined["metadata"]["quality_flags"].append({
                "type": "excessive_nesting",
                "description": f"Structure has excessive nesting (depth: {max_depth}, max recommended: {self.max_allowed_depth})",
                "details": "Deep nesting makes content harder to understand and process"
            })
            
            refinements.append({
                "category": "structure",
                "field": "metadata.quality_flags",
                "description": "Added excessive nesting flag",
                "change": "added_flag"
            })
        
        # Process specific issues if provided
        if issues:
            for issue in issues:
                issue_type = issue.get("type", "")
                
                # Skip issues without a type
                if not issue_type:
                    continue
                
                # Add flags for structural issues
                if issue_type == "structure":
                    if "metadata" not in refined:
                        refined["metadata"] = {}
                        
                    if "quality_flags" not in refined["metadata"]:
                        refined["metadata"]["quality_flags"] = []
                        
                    refined["metadata"]["quality_flags"].append({
                        "type": "structure_improvement_needed",
                        "description": "Content structure needs improvement",
                        "details": issue.get("details", "Structure could be improved for better comprehension")
                    })
                    
                    refinements.append({
                        "category": "structure",
                        "field": "metadata.quality_flags",
                        "description": "Added structure improvement flag",
                        "change": "added_flag"
                    })
        
        logger.info(f"Structure refinement completed with {len(refinements)} refinements")
        return refined, refinements
    
    def generate_suggestions(self, content: Dict[str, Any], issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate suggestions for improving content structure.
        
        Args:
            content (Dict[str, Any]): Content to improve
            issues (List[Dict[str, Any]]): Structure issues
            
        Returns:
            List[Dict[str, Any]]: Improvement suggestions
        """
        suggestions = []
        
        # Check overall structure regardless of specific issues
        max_depth = self._calculate_max_depth(content)
        
        if max_depth > self.max_allowed_depth:
            suggestions.append({
                "type": "structure_improvement",
                "category": "nesting",
                "description": f"Reduce nesting depth (currently {max_depth} levels, max recommended is {self.max_allowed_depth})",
                "details": "Deep nesting makes content harder to understand and process"
            })
        elif max_depth <= 1 and len(content) > 5:
            suggestions.append({
                "type": "structure_improvement",
                "category": "organization",
                "description": "Consider grouping related content into nested structures",
                "details": "Flat structures with many fields can be harder to navigate"
            })
        
        # Process specific issues
        for issue in issues:
            issue_type = issue.get("type", "")
            
            if issue_type == "structure":
                suggestions.append({
                    "type": "structure_improvement",
                    "category": "organization",
                    "description": "Improve structural organization for better comprehension",
                    "details": issue.get("details", "")
                })
        
        return suggestions
    
    def summarize(self, original_content: Dict[str, Any], refined_content: Dict[str, Any]) -> List[str]:
        """
        Generate a summary of structural refinements made.
        
        Args:
            original_content (Dict[str, Any]): Original content
            refined_content (Dict[str, Any]): Refined content
            
        Returns:
            List[str]: Summary of structural refinements
        """
        summaries = []
        
        # Check for structure flags
        if ("metadata" in refined_content and 
            "quality_flags" in refined_content.get("metadata", {}) and 
            any(flag.get("type") == "excessive_nesting" for flag in refined_content["metadata"]["quality_flags"])):
            
            max_depth = self._calculate_max_depth(original_content)
            summaries.append(f"Flagged excessive nesting (depth: {max_depth}, max recommended: {self.max_allowed_depth})")
        
        if ("metadata" in refined_content and 
            "quality_flags" in refined_content.get("metadata", {}) and 
            any(flag.get("type") == "structure_improvement_needed" for flag in refined_content["metadata"]["quality_flags"])):
            
            summaries.append("Content flagged for structural improvements")
        
        return summaries
    
    def _calculate_max_depth(self, obj: Any, current_depth: int = 0) -> int:
        """
        Calculate the maximum nesting depth of an object.
        
        Args:
            obj (Any): Object to analyze
            current_depth (int): Current depth in recursion
            
        Returns:
            int: Maximum nesting depth
        """
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_max_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_max_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth 