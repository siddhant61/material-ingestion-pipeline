"""
Context Fusion Reasoning

This module provides reasoning capabilities for the Context Fusion Agent,
ensuring it properly fuses context from different sources without adding
new information.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Type

# Configure logging
logger = logging.getLogger(__name__)

class ContextFusionReasoning:
    """
    Reasoning component for the Context Fusion Agent.
    
    This class implements the reasoning capabilities for fusing context
    from different sources, ensuring information is correctly integrated
    without adding new or hallucinated content.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the ContextFusionReasoning component.
        
        Args:
            config: Configuration for the reasoning component
        """
        self.config = config or {}
        
        # Initialize reasoning strategies
        self.strategies = {
            "strict_provenance": self.config.get("strict_provenance", True),
            "conflict_resolution": self.config.get("conflict_resolution", "conservative"),
            "completeness_threshold": self.config.get("completeness_threshold", 0.8)
        }
        
        logger.info(f"Initialized ContextFusionReasoning with strategies: {self.strategies}")
    
    def plan_fusion(self, course_context: Dict[str, Any], transcript_data: Dict[str, Any], slide_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan the context fusion approach based on available data.
        
        Args:
            course_context: Course context data
            transcript_data: Transcript processing data
            slide_data: Slide processing data
            
        Returns:
            Fusion plan with strategy and prioritization
        """
        # Check data availability
        data_availability = {
            "course_context": self._assess_data_quality(course_context),
            "transcript_data": self._assess_data_quality(transcript_data),
            "slide_data": self._assess_data_quality(slide_data)
        }
        
        # Determine primary and secondary sources
        primary_source = max(data_availability.items(), key=lambda x: x[1]["completeness"])
        
        # Create fusion plan
        fusion_plan = {
            "primary_source": primary_source[0],
            "data_availability": data_availability,
            "approach": "hierarchical" if primary_source[1]["completeness"] > 0.7 else "collaborative",
            "strict_provenance": self.strategies["strict_provenance"],
            "conflict_resolution": self.strategies["conflict_resolution"],
            "alignment_strategy": self._determine_alignment_strategy(data_availability),
            "prioritization": self._create_prioritization(data_availability)
        }
        
        logger.info(f"Created fusion plan with {fusion_plan['approach']} approach "
                   f"and {fusion_plan['primary_source']} as primary source")
        
        return fusion_plan
    
    def validate_fusion_output(self, 
                               fused_context: Dict[str, Any], 
                               source_data: Dict[str, Dict[str, Any]],
                               fusion_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the fused context to ensure it only contains information
        from the source materials.
        
        Args:
            fused_context: The fused context to validate
            source_data: Dictionary of source data used for fusion
            fusion_plan: The fusion plan used
            
        Returns:
            Validation results
        """
        # Initialize validation results
        validation = {
            "is_valid": True,
            "issues": [],
            "hallucinations": [],
            "missing_content": [],
            "conflicts": []
        }
        
        # Check for hallucinations (content not in any source)
        hallucinations = self._detect_hallucinations(fused_context, source_data)
        if hallucinations:
            validation["is_valid"] = False
            validation["hallucinations"] = hallucinations
            validation["issues"].append(f"Found {len(hallucinations)} potential hallucinations")
        
        # Check for missing critical content
        missing_content = self._detect_missing_content(fused_context, source_data, fusion_plan)
        if missing_content:
            validation["missing_content"] = missing_content
            validation["issues"].append(f"Missing {len(missing_content)} critical content elements")
        
        # Check for conflicts
        conflicts = self._detect_conflicts(fused_context, source_data)
        if conflicts:
            validation["conflicts"] = conflicts
            validation["issues"].append(f"Found {len(conflicts)} conflicts in fused content")
        
        logger.info(f"Validated fusion output with result: valid={validation['is_valid']}, "
                   f"issues={len(validation['issues'])}")
        
        return validation
    
    def refine_fusion(self, 
                      fused_context: Dict[str, Any], 
                      validation_results: Dict[str, Any],
                      source_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Refine the fused context based on validation results.
        
        Args:
            fused_context: The fused context to refine
            validation_results: Results from validation
            source_data: Dictionary of source data used for fusion
            
        Returns:
            Refined fused context
        """
        refined_context = fused_context.copy()
        
        # Handle hallucinations
        if validation_results["hallucinations"]:
            refined_context = self._remove_hallucinations(
                refined_context, 
                validation_results["hallucinations"],
                source_data
            )
        
        # Add missing content
        if validation_results["missing_content"]:
            refined_context = self._add_missing_content(
                refined_context,
                validation_results["missing_content"],
                source_data
            )
        
        # Resolve conflicts
        if validation_results["conflicts"]:
            refined_context = self._resolve_conflicts(
                refined_context,
                validation_results["conflicts"],
                source_data
            )
        
        # Add provenance information to track content sources
        refined_context = self._add_provenance(
            refined_context,
            source_data
        )
        
        logger.info(f"Refined fusion output, fixing {len(validation_results.get('issues', []))} issues")
        
        return refined_context
    
    def generate_fusion_metadata(self,
                                fused_context: Dict[str, Any],
                                source_data: Dict[str, Dict[str, Any]],
                                fusion_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata for the fused context.
        
        Args:
            fused_context: The fused context
            source_data: Dictionary of source data used for fusion
            fusion_plan: The fusion plan used
            
        Returns:
            Metadata for the fused context
        """
        # Count information elements from each source
        source_contributions = {}
        for source, data in source_data.items():
            source_contributions[source] = self._count_contributions(fused_context, data)
        
        # Calculate fusion statistics
        total_elements = sum(source_contributions.values())
        source_percentages = {
            source: (count / total_elements) if total_elements > 0 else 0
            for source, count in source_contributions.items()
        }
        
        # Create metadata
        metadata = {
            "fusion_approach": fusion_plan["approach"],
            "primary_source": fusion_plan["primary_source"],
            "source_contributions": source_contributions,
            "source_percentages": source_percentages,
            "alignment_strategy": fusion_plan["alignment_strategy"],
            "prioritization": fusion_plan["prioritization"],
            "strict_provenance": fusion_plan["strict_provenance"]
        }
        
        logger.info(f"Generated fusion metadata with contributions from {len(source_contributions)} sources")
        
        return metadata
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the quality of input data.
        
        Args:
            data: Input data to assess
            
        Returns:
            Data quality assessment
        """
        # Check for empty or None data
        if not data:
            return {
                "completeness": 0.0,
                "structure": 0.0,
                "relevance": 0.0,
                "overall": 0.0
            }
        
        # Check for error status
        if isinstance(data, dict) and data.get("status") == "error":
            return {
                "completeness": 0.0,
                "structure": 0.0,
                "relevance": 0.0,
                "overall": 0.0
            }
        
        # Estimate completeness by checking for expected keys or data volume
        completeness = min(1.0, len(json.dumps(data)) / 10000)
        
        # Estimate structure based on nesting depth
        structure = min(1.0, self._calculate_structure_score(data) / 5)
        
        # For now, assume all data is relevant
        relevance = 0.8
        
        # Calculate overall score
        overall = (completeness * 0.5) + (structure * 0.3) + (relevance * 0.2)
        
        return {
            "completeness": completeness,
            "structure": structure,
            "relevance": relevance,
            "overall": overall
        }
    
    def _calculate_structure_score(self, data: Dict[str, Any], depth: int = 0) -> int:
        """
        Calculate a structure score based on nesting depth.
        
        Args:
            data: Data to calculate structure score for
            depth: Current depth
            
        Returns:
            Structure score
        """
        if depth > 10:  # Prevent infinite recursion
            return 10
        
        if not isinstance(data, (dict, list)):
            return depth
        
        if isinstance(data, dict):
            if not data:
                return depth
            return max(self._calculate_structure_score(v, depth + 1) for v in data.values())
        
        if isinstance(data, list):
            if not data:
                return depth
            return max(self._calculate_structure_score(item, depth + 1) for item in data)
    
    def _determine_alignment_strategy(self, data_availability: Dict[str, Dict[str, float]]) -> str:
        """
        Determine the alignment strategy based on data availability.
        
        Args:
            data_availability: Data availability assessment
            
        Returns:
            Alignment strategy
        """
        # Check if we have good transcript and slide data
        transcript_quality = data_availability.get("transcript_data", {}).get("overall", 0)
        slide_quality = data_availability.get("slide_data", {}).get("overall", 0)
        
        if transcript_quality > 0.7 and slide_quality > 0.7:
            return "temporal_semantic"
        elif transcript_quality > 0.7:
            return "transcript_driven"
        elif slide_quality > 0.7:
            return "slide_driven"
        else:
            return "course_structure_driven"
    
    def _create_prioritization(self, data_availability: Dict[str, Dict[str, float]]) -> Dict[str, int]:
        """
        Create prioritization for different data sources.
        
        Args:
            data_availability: Data availability assessment
            
        Returns:
            Prioritization for data sources
        """
        # Sort sources by overall quality
        sorted_sources = sorted(
            data_availability.items(),
            key=lambda x: x[1]["overall"],
            reverse=True
        )
        
        # Create prioritization
        prioritization = {source: i + 1 for i, (source, _) in enumerate(sorted_sources)}
        
        return prioritization
    
    def _detect_hallucinations(self, 
                              fused_context: Dict[str, Any],
                              source_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect potential hallucinations in the fused context.
        
        Args:
            fused_context: The fused context
            source_data: Dictionary of source data
            
        Returns:
            List of potential hallucinations
        """
        # Simplified implementation: check for key content not in any source
        hallucinations = []
        
        # Check top-level keys
        for key, value in fused_context.items():
            # Skip metadata fields
            if key in ["metadata", "fusion_metadata", "provenance"]:
                continue
            
            # Check if this key exists in any source
            found_in_source = False
            for source_name, source in source_data.items():
                if key in source:
                    found_in_source = True
                    break
            
            if not found_in_source:
                hallucinations.append({
                    "type": "key",
                    "key": key,
                    "value": str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                })
        
        # Advanced implementation would use semantic comparison for deeper analysis
        
        return hallucinations
    
    def _detect_missing_content(self,
                               fused_context: Dict[str, Any],
                               source_data: Dict[str, Dict[str, Any]],
                               fusion_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect critical missing content in the fused context.
        
        Args:
            fused_context: The fused context
            source_data: Dictionary of source data
            fusion_plan: The fusion plan used
            
        Returns:
            List of missing content
        """
        missing_content = []
        
        # Get primary source
        primary_source_name = fusion_plan["primary_source"]
        primary_source = source_data.get(primary_source_name, {})
        
        # Check for critical missing keys from primary source
        for key, value in primary_source.items():
            # Skip metadata and non-critical fields
            if key in ["metadata", "status", "message"] or not value:
                continue
            
            if key not in fused_context:
                missing_content.append({
                    "type": "key",
                    "source": primary_source_name,
                    "key": key,
                    "value": str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                })
        
        return missing_content
    
    def _detect_conflicts(self,
                         fused_context: Dict[str, Any],
                         source_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect conflicts in the fused context.
        
        Args:
            fused_context: The fused context
            source_data: Dictionary of source data
            
        Returns:
            List of conflicts
        """
        # Simplified implementation: look for keys with different values
        conflicts = []
        
        # Check each key in the fused context
        for key, fused_value in fused_context.items():
            # Skip metadata fields
            if key in ["metadata", "fusion_metadata", "provenance"]:
                continue
            
            # Check values across sources
            source_values = {}
            for source_name, source in source_data.items():
                if key in source:
                    source_values[source_name] = source[key]
            
            # Check if we have multiple different values
            if len(source_values) > 1:
                # Convert to string for comparison
                str_values = {s: str(v) for s, v in source_values.items()}
                unique_values = set(str_values.values())
                
                if len(unique_values) > 1:
                    conflicts.append({
                        "key": key,
                        "fused_value": str(fused_value)[:100] + "..." if len(str(fused_value)) > 100 else str(fused_value),
                        "source_values": {s: v[:100] + "..." if len(v) > 100 else v for s, v in str_values.items()}
                    })
        
        return conflicts
    
    def _remove_hallucinations(self,
                              fused_context: Dict[str, Any],
                              hallucinations: List[Dict[str, Any]],
                              source_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Remove hallucinations from the fused context.
        
        Args:
            fused_context: The fused context
            hallucinations: List of hallucinations
            source_data: Dictionary of source data
            
        Returns:
            Refined fused context with hallucinations removed
        """
        refined_context = fused_context.copy()
        
        # Remove hallucinated keys
        for hallucination in hallucinations:
            if hallucination["type"] == "key" and hallucination["key"] in refined_context:
                del refined_context[hallucination["key"]]
        
        return refined_context
    
    def _add_missing_content(self,
                            fused_context: Dict[str, Any],
                            missing_content: List[Dict[str, Any]],
                            source_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add missing content to the fused context.
        
        Args:
            fused_context: The fused context
            missing_content: List of missing content
            source_data: Dictionary of source data
            
        Returns:
            Refined fused context with missing content added
        """
        refined_context = fused_context.copy()
        
        # Add missing keys
        for missing in missing_content:
            if missing["type"] == "key":
                source = source_data.get(missing["source"], {})
                if missing["key"] in source:
                    refined_context[missing["key"]] = source[missing["key"]]
        
        return refined_context
    
    def _resolve_conflicts(self,
                          fused_context: Dict[str, Any],
                          conflicts: List[Dict[str, Any]],
                          source_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts in the fused context.
        
        Args:
            fused_context: The fused context
            conflicts: List of conflicts
            source_data: Dictionary of source data
            
        Returns:
            Refined fused context with conflicts resolved
        """
        refined_context = fused_context.copy()
        
        # Prioritize sources (assuming course_context is most authoritative)
        priority_order = ["course_context", "transcript_data", "slide_data"]
        
        # Resolve each conflict
        for conflict in conflicts:
            key = conflict["key"]
            
            # Find the highest priority source with this key
            for source_name in priority_order:
                if source_name in source_data and key in source_data[source_name]:
                    refined_context[key] = source_data[source_name][key]
                    break
        
        return refined_context
    
    def _add_provenance(self,
                       fused_context: Dict[str, Any],
                       source_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add provenance information to the fused context.
        
        Args:
            fused_context: The fused context
            source_data: Dictionary of source data
            
        Returns:
            Fused context with provenance information
        """
        refined_context = fused_context.copy()
        
        # Initialize provenance tracking
        if "provenance" not in refined_context:
            refined_context["provenance"] = {}
        
        # Track provenance for each key
        for key in refined_context:
            # Skip metadata and provenance itself
            if key in ["metadata", "fusion_metadata", "provenance"]:
                continue
            
            # Find sources that contain this key
            sources_with_key = []
            for source_name, source in source_data.items():
                if key in source:
                    sources_with_key.append(source_name)
            
            # Add provenance information
            refined_context["provenance"][key] = sources_with_key
        
        return refined_context
    
    def _count_contributions(self,
                            fused_context: Dict[str, Any],
                            source_data: Dict[str, Any]) -> int:
        """
        Count the number of elements contributed by a source.
        
        Args:
            fused_context: The fused context
            source_data: Source data
            
        Returns:
            Number of contributed elements
        """
        # Count top-level keys in common
        common_keys = set(fused_context.keys()) & set(source_data.keys())
        
        # Exclude metadata fields
        common_keys = {k for k in common_keys if k not in ["metadata", "fusion_metadata", "provenance"]}
        
        return len(common_keys) 