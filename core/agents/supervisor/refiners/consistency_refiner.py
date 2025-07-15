"""
Consistency Refiner

This module provides functionality for improving the consistency of agent outputs
based on consistency check results.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional, Set

# Configure logging
logger = logging.getLogger(__name__)

class ConsistencyRefiner:
    """
    Refiner for improving output consistency.
    
    This refiner addresses issues related to:
    - Schema consistency
    - Terminology consistency
    - Format consistency
    - Reference consistency
    - Value consistency
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the ConsistencyRefiner.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        logger.info("ConsistencyRefiner initialized")
    
    def refine(self, 
              content: Dict[str, Any], 
              issues: List[Dict[str, Any]], 
              guidelines: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refine content to address consistency issues.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issues (List[Dict[str, Any]]): Consistency issues to address
            guidelines (Dict[str, Any]): Refinement guidelines
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: Refined content and list of refinements made
        """
        if not issues:
            return content, []
        
        # Make a working copy to avoid modifying the original
        refined = content.copy()
        refinements = []
        
        # Process each issue by type
        for issue in issues:
            issue_type = issue.get("type", "")
            
            # Skip issues without a type
            if not issue_type:
                continue
            
            # Apply appropriate refinement based on issue type
            if issue_type == "schema_consistency":
                refined, new_refinements = self._refine_schema_consistency(refined, issue, guidelines)
                refinements.extend(new_refinements)
                
            elif issue_type == "terminology_consistency":
                refined, new_refinements = self._refine_terminology_consistency(refined, issue, guidelines)
                refinements.extend(new_refinements)
                
            elif issue_type == "format_consistency":
                refined, new_refinements = self._refine_format_consistency(refined, issue, guidelines)
                refinements.extend(new_refinements)
                
            elif issue_type == "reference_consistency":
                refined, new_refinements = self._refine_reference_consistency(refined, issue, guidelines)
                refinements.extend(new_refinements)
                
            elif issue_type == "value_consistency":
                refined, new_refinements = self._refine_value_consistency(refined, issue, guidelines)
                refinements.extend(new_refinements)
        
        logger.info(f"Consistency refinement completed with {len(refinements)} refinements")
        return refined, refinements
    
    def generate_suggestions(self, content: Dict[str, Any], issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate suggestions for improving content consistency.
        
        Args:
            content (Dict[str, Any]): Content to improve
            issues (List[Dict[str, Any]]): Consistency issues
            
        Returns:
            List[Dict[str, Any]]: Improvement suggestions
        """
        suggestions = []
        
        for issue in issues:
            issue_type = issue.get("type", "")
            
            if issue_type == "schema_consistency":
                suggestions.append({
                    "type": "consistency_improvement",
                    "category": "schema",
                    "description": "Make schema consistent with other outputs",
                    "details": issue.get("details", "")
                })
                
            elif issue_type == "terminology_consistency":
                suggestions.append({
                    "type": "consistency_improvement",
                    "category": "terminology",
                    "description": "Standardize terminology across outputs",
                    "details": issue.get("details", "")
                })
                
            elif issue_type == "format_consistency":
                suggestions.append({
                    "type": "consistency_improvement",
                    "category": "format",
                    "description": "Standardize data formats",
                    "details": issue.get("details", "")
                })
                
            elif issue_type == "reference_consistency":
                suggestions.append({
                    "type": "consistency_improvement",
                    "category": "references",
                    "description": "Make references consistent across outputs",
                    "details": issue.get("details", "")
                })
                
            elif issue_type == "value_consistency":
                suggestions.append({
                    "type": "consistency_improvement",
                    "category": "values",
                    "description": "Make values consistent across outputs",
                    "details": issue.get("details", "")
                })
        
        return suggestions
    
    def summarize(self, original_content: Dict[str, Any], refined_content: Dict[str, Any]) -> List[str]:
        """
        Generate a summary of consistency refinements made.
        
        Args:
            original_content (Dict[str, Any]): Original content
            refined_content (Dict[str, Any]): Refined content
            
        Returns:
            List[str]: Summary of consistency refinements
        """
        summaries = []
        
        # Look for schema consistency improvements
        schema_changes = self._detect_schema_changes(original_content, refined_content)
        if schema_changes:
            summaries.append(f"Improved schema consistency: {schema_changes}")
        
        # Look for terminology consistency improvements
        terminology_changes = self._detect_terminology_changes(original_content, refined_content)
        if terminology_changes:
            summaries.append(f"Standardized terminology: {terminology_changes}")
        
        # Look for format consistency improvements
        format_changes = self._detect_format_changes(original_content, refined_content)
        if format_changes:
            summaries.append(f"Standardized formats: {format_changes}")
        
        # Look for value consistency improvements
        value_changes = self._detect_value_changes(original_content, refined_content)
        if value_changes:
            summaries.append(f"Made values consistent: {value_changes}")
        
        return summaries
    
    def _refine_schema_consistency(self, 
                                 content: Dict[str, Any], 
                                 issue: Dict[str, Any], 
                                 guidelines: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refine content to address schema consistency issues.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issue (Dict[str, Any]): Schema consistency issue
            guidelines (Dict[str, Any]): Refinement guidelines
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: Refined content and list of refinements made
        """
        refinements = []
        
        # For schema consistency issues, we need a target schema to align with
        target_schema = guidelines.get("target_schema")
        
        if not target_schema:
            # No target schema specified, just flag the issue
            if "metadata" not in content:
                content["metadata"] = {}
                
            if "consistency_flags" not in content["metadata"]:
                content["metadata"]["consistency_flags"] = []
                
            content["metadata"]["consistency_flags"].append({
                "type": "schema_consistency_needed",
                "description": "Schema needs to be aligned with other outputs"
            })
            
            refinements.append({
                "category": "schema_consistency",
                "field": "metadata.consistency_flags",
                "description": "Added schema consistency flag",
                "change": "added_flag"
            })
            
            return content, refinements
        
        # For actual schema refinement, we would need to transform the content
        # to match the target schema, but this is a complex operation that
        # would typically require AI assistance or domain-specific knowledge
        
        # Here we implement a simplified version that only adds missing fields
        for field, field_type in target_schema.items():
            if field not in content:
                # Add missing field with appropriate default value
                if field_type == "object":
                    content[field] = {}
                elif field_type == "array" or field_type.startswith("array<"):
                    content[field] = []
                elif field_type == "string":
                    content[field] = "TBD"
                elif field_type == "number" or field_type == "float":
                    content[field] = 0.0
                elif field_type == "integer" or field_type == "int":
                    content[field] = 0
                elif field_type == "boolean" or field_type == "bool":
                    content[field] = False
                else:
                    content[field] = None
                
                refinements.append({
                    "category": "schema_consistency",
                    "field": field,
                    "description": f"Added missing field '{field}' to match schema",
                    "change": "added_field"
                })
        
        return content, refinements
    
    def _refine_terminology_consistency(self, 
                                      content: Dict[str, Any], 
                                      issue: Dict[str, Any], 
                                      guidelines: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refine content to address terminology consistency issues.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issue (Dict[str, Any]): Terminology consistency issue
            guidelines (Dict[str, Any]): Refinement guidelines
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: Refined content and list of refinements made
        """
        # For terminology refinement, we'd need a terminology mapping
        # which is complex and would typically require AI assistance
        # Here we just flag the issue
        refinements = []
        
        if "metadata" not in content:
            content["metadata"] = {}
            
        if "consistency_flags" not in content["metadata"]:
            content["metadata"]["consistency_flags"] = []
            
        content["metadata"]["consistency_flags"].append({
            "type": "terminology_consistency_needed",
            "description": "Terminology needs to be standardized"
        })
        
        refinements.append({
            "category": "terminology_consistency",
            "field": "metadata.consistency_flags",
            "description": "Added terminology consistency flag",
            "change": "added_flag"
        })
        
        return content, refinements
    
    def _refine_format_consistency(self, 
                                 content: Dict[str, Any], 
                                 issue: Dict[str, Any], 
                                 guidelines: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refine content to address format consistency issues.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issue (Dict[str, Any]): Format consistency issue
            guidelines (Dict[str, Any]): Refinement guidelines
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: Refined content and list of refinements made
        """
        # For format consistency, we'd need to know specific format requirements
        # Here we just flag the issue
        refinements = []
        
        if "metadata" not in content:
            content["metadata"] = {}
            
        if "consistency_flags" not in content["metadata"]:
            content["metadata"]["consistency_flags"] = []
            
        content["metadata"]["consistency_flags"].append({
            "type": "format_consistency_needed",
            "description": "Data formats need to be standardized"
        })
        
        refinements.append({
            "category": "format_consistency",
            "field": "metadata.consistency_flags",
            "description": "Added format consistency flag",
            "change": "added_flag"
        })
        
        return content, refinements
    
    def _refine_reference_consistency(self, 
                                    content: Dict[str, Any], 
                                    issue: Dict[str, Any], 
                                    guidelines: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refine content to address reference consistency issues.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issue (Dict[str, Any]): Reference consistency issue
            guidelines (Dict[str, Any]): Refinement guidelines
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: Refined content and list of refinements made
        """
        # For reference consistency, we'd need to match references across outputs
        # Here we just flag the issue
        refinements = []
        
        if "metadata" not in content:
            content["metadata"] = {}
            
        if "consistency_flags" not in content["metadata"]:
            content["metadata"]["consistency_flags"] = []
            
        content["metadata"]["consistency_flags"].append({
            "type": "reference_consistency_needed",
            "description": "References need to be made consistent"
        })
        
        refinements.append({
            "category": "reference_consistency",
            "field": "metadata.consistency_flags",
            "description": "Added reference consistency flag",
            "change": "added_flag"
        })
        
        return content, refinements
    
    def _refine_value_consistency(self, 
                                content: Dict[str, Any], 
                                issue: Dict[str, Any], 
                                guidelines: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Refine content to address value consistency issues.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issue (Dict[str, Any]): Value consistency issue
            guidelines (Dict[str, Any]): Refinement guidelines
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: Refined content and list of refinements made
        """
        # For value consistency, we'd need to standardize values across outputs
        # Here we just flag the issue
        refinements = []
        
        if "metadata" not in content:
            content["metadata"] = {}
            
        if "consistency_flags" not in content["metadata"]:
            content["metadata"]["consistency_flags"] = []
            
        content["metadata"]["consistency_flags"].append({
            "type": "value_consistency_needed",
            "description": "Values need to be made consistent across outputs"
        })
        
        refinements.append({
            "category": "value_consistency",
            "field": "metadata.consistency_flags",
            "description": "Added value consistency flag",
            "change": "added_flag"
        })
        
        return content, refinements
    
    def _detect_schema_changes(self, original: Dict[str, Any], refined: Dict[str, Any]) -> str:
        """
        Detect schema consistency improvements between original and refined content.
        
        Args:
            original (Dict[str, Any]): Original content
            refined (Dict[str, Any]): Refined content
            
        Returns:
            str: Description of schema changes
        """
        # Check for added fields (schema alignment)
        original_keys = set(original.keys())
        refined_keys = set(refined.keys())
        
        new_keys = refined_keys - original_keys
        
        if new_keys:
            return f"Added fields to align schema: {', '.join(new_keys)}"
        
        # Check for consistency flags
        if ("metadata" in refined and "consistency_flags" in refined.get("metadata", {}) and
            any(flag.get("type") == "schema_consistency_needed" for flag in refined["metadata"]["consistency_flags"])):
            return "Schema flagged for consistency improvements"
        
        return ""
    
    def _detect_terminology_changes(self, original: Dict[str, Any], refined: Dict[str, Any]) -> str:
        """
        Detect terminology consistency improvements between original and refined content.
        
        Args:
            original (Dict[str, Any]): Original content
            refined (Dict[str, Any]): Refined content
            
        Returns:
            str: Description of terminology changes
        """
        # For now, just check for consistency flags
        if ("metadata" in refined and "consistency_flags" in refined.get("metadata", {}) and
            any(flag.get("type") == "terminology_consistency_needed" for flag in refined["metadata"]["consistency_flags"])):
            return "Terminology flagged for consistency improvements"
        
        return ""
    
    def _detect_format_changes(self, original: Dict[str, Any], refined: Dict[str, Any]) -> str:
        """
        Detect format consistency improvements between original and refined content.
        
        Args:
            original (Dict[str, Any]): Original content
            refined (Dict[str, Any]): Refined content
            
        Returns:
            str: Description of format changes
        """
        # For now, just check for consistency flags
        if ("metadata" in refined and "consistency_flags" in refined.get("metadata", {}) and
            any(flag.get("type") == "format_consistency_needed" for flag in refined["metadata"]["consistency_flags"])):
            return "Data formats flagged for consistency improvements"
        
        return ""
    
    def _detect_value_changes(self, original: Dict[str, Any], refined: Dict[str, Any]) -> str:
        """
        Detect value consistency improvements between original and refined content.
        
        Args:
            original (Dict[str, Any]): Original content
            refined (Dict[str, Any]): Refined content
            
        Returns:
            str: Description of value changes
        """
        # For now, just check for consistency flags
        if ("metadata" in refined and "consistency_flags" in refined.get("metadata", {}) and
            any(flag.get("type") == "value_consistency_needed" for flag in refined["metadata"]["consistency_flags"])):
            return "Values flagged for consistency improvements"
        
        return "" 