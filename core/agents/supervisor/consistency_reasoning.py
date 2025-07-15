"""
Consistency Reasoning Component

This module provides consistency evaluation capabilities for the SupervisorAgent,
focusing on assessing consistency across agent outputs.
"""

import logging
from typing import Dict, List, Any, Optional, Set

# Configure logging
logger = logging.getLogger(__name__)

class ConsistencyReasoning:
    """
    Consistency reasoning component for evaluating output consistency.
    
    This component evaluates:
    - Schema consistency
    - Terminology consistency
    - Format consistency
    - Reference consistency
    - Value consistency
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the ConsistencyReasoning component.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        
        # Default consistency metrics and thresholds
        self.default_metrics = {
            "schema_consistency": 0.9,
            "terminology_consistency": 0.8,
            "format_consistency": 0.9,
            "reference_consistency": 0.85,
            "value_consistency": 0.8
        }
        
        # Override defaults with config values if provided
        self.metrics = {**self.default_metrics, **self.config.get("metrics", {})}
        
        # Store previously seen outputs for comparison
        self.previous_outputs = {}
        
        logger.info("ConsistencyReasoning initialized")
    
    def evaluate(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the consistency of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            guidelines (Dict[str, Any]): Consistency guidelines
            
        Returns:
            Dict[str, Any]: Consistency evaluation results
        """
        try:
            # Get comparison data from guidelines
            comparison_data = guidelines.get("comparison_data", {})
            
            # Calculate individual consistency metrics
            # If no comparison data, we can only do limited consistency checks
            metrics = {}
            
            # Schema consistency
            metrics["schema_consistency"] = self._evaluate_schema_consistency(content, comparison_data, guidelines)
            
            # Terminology consistency
            metrics["terminology_consistency"] = self._evaluate_terminology_consistency(content, comparison_data, guidelines)
            
            # Format consistency
            metrics["format_consistency"] = self._evaluate_format_consistency(content, comparison_data, guidelines)
            
            # Reference consistency
            metrics["reference_consistency"] = self._evaluate_reference_consistency(content, comparison_data, guidelines)
            
            # Value consistency
            metrics["value_consistency"] = self._evaluate_value_consistency(content, comparison_data, guidelines)
            
            # Identify issues based on metrics
            issues = []
            thresholds = guidelines.get("metrics", self.metrics)
            
            # Check each metric against its threshold
            for metric_name, metric_value in metrics.items():
                threshold = thresholds.get(metric_name, 0.7)
                if metric_value < threshold:
                    issues.append({
                        "type": metric_name,
                        "severity": "high" if metric_value < threshold - 0.2 else "medium",
                        "description": f"{metric_name.replace('_', ' ').title()} is below acceptable threshold",
                        "details": f"Score: {metric_value:.2f}, threshold: {threshold:.2f}"
                    })
            
            # Calculate overall consistency score (weighted average)
            weights = guidelines.get("weights", {
                "schema_consistency": 0.3,
                "terminology_consistency": 0.25,
                "format_consistency": 0.15,
                "reference_consistency": 0.15,
                "value_consistency": 0.15
            })
            
            consistency_score = sum(
                metrics[metric] * weights.get(metric, 0.2)
                for metric in metrics
            )
            
            # Determine if refinement is needed
            needs_refinement = consistency_score < guidelines.get("consistency_threshold", 0.7) or len(issues) > 0
            
            # Generate comparisons with previous outputs
            comparisons = []
            if comparison_data:
                # Generate basic comparison details
                for name, data in comparison_data.items():
                    diff_count = self._count_differences(content, data)
                    comparisons.append({
                        "compared_with": name,
                        "differences_count": diff_count,
                        "similarity_score": max(0, 1.0 - (diff_count / 10.0))  # Simple heuristic
                    })
            
            return {
                "consistency_score": round(consistency_score, 2),
                "metrics": {k: round(v, 2) for k, v in metrics.items()},
                "issues": issues,
                "comparisons": comparisons,
                "needs_refinement": needs_refinement
            }
            
        except Exception as e:
            logger.error(f"Error in consistency evaluation: {str(e)}")
            return {
                "consistency_score": 0.0,
                "metrics": {},
                "issues": [{"type": "error", "description": f"Consistency evaluation failed: {str(e)}"}],
                "comparisons": [],
                "needs_refinement": True
            }
    
    def identify_issues(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify consistency issues in content.
        
        Args:
            content (Dict[str, Any]): Content to analyze
            
        Returns:
            List[Dict[str, Any]]: Identified consistency issues
        """
        # Perform a basic evaluation and extract issues
        evaluation = self.evaluate(content, {})
        return evaluation.get("issues", [])
    
    def register_output(self, agent_name: str, output: Dict[str, Any]) -> None:
        """
        Register an agent output for future consistency comparisons.
        
        Args:
            agent_name (str): Name of the agent
            output (Dict[str, Any]): Agent output
        """
        if agent_name not in self.previous_outputs:
            self.previous_outputs[agent_name] = []
        
        self.previous_outputs[agent_name].append(output)
        logger.info(f"Registered output for {agent_name}")
    
    def _evaluate_schema_consistency(
        self, 
        content: Dict[str, Any], 
        comparison_data: Dict[str, Any], 
        guidelines: Dict[str, Any]
    ) -> float:
        """
        Evaluate schema consistency with other outputs.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            comparison_data (Dict[str, Any]): Data to compare against
            guidelines (Dict[str, Any]): Consistency guidelines
            
        Returns:
            float: Schema consistency score between 0 and 1
        """
        if not content:
            return 0.0
        
        # If no comparison data, return default score
        if not comparison_data:
            return 0.8  # Default score
        
        # Simple schema comparison with top-level keys
        content_keys = set(content.keys())
        
        # Calculate average schema consistency across comparison data
        consistency_scores = []
        
        for name, data in comparison_data.items():
            if not isinstance(data, dict):
                continue
                
            comp_keys = set(data.keys())
            
            # Calculate Jaccard similarity of keys
            intersection = len(content_keys & comp_keys)
            union = len(content_keys | comp_keys)
            
            if union == 0:
                similarity = 1.0  # Both empty
            else:
                similarity = intersection / union
            
            consistency_scores.append(similarity)
        
        # Return average consistency score
        if not consistency_scores:
            return 0.8  # Default score
            
        return sum(consistency_scores) / len(consistency_scores)
    
    def _evaluate_terminology_consistency(
        self, 
        content: Dict[str, Any], 
        comparison_data: Dict[str, Any], 
        guidelines: Dict[str, Any]
    ) -> float:
        """
        Evaluate terminology consistency across outputs.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            comparison_data (Dict[str, Any]): Data to compare against
            guidelines (Dict[str, Any]): Consistency guidelines
            
        Returns:
            float: Terminology consistency score between 0 and 1
        """
        # If no comparison data, return default score
        if not comparison_data:
            return 0.8  # Default score
        
        # Extract terminology from guidelines
        terminology = guidelines.get("terminology", {})
        
        # If no terminology specified, use simple heuristic
        if not terminology:
            return 0.8  # Default score
        
        # Check for terminology usage
        score = 0.0
        for term, expected_usage in terminology.items():
            if self._check_term_usage(content, term) == expected_usage:
                score += 1.0
                
        return min(1.0, score / max(1, len(terminology)))
    
    def _check_term_usage(self, content: Dict[str, Any], term: str) -> bool:
        """
        Check if a term is used in content.
        
        Args:
            content (Dict[str, Any]): Content to check
            term (str): Term to look for
            
        Returns:
            bool: Whether the term is used
        """
        # Convert content to string for simple checking
        content_str = str(content).lower()
        return term.lower() in content_str
    
    def _evaluate_format_consistency(
        self, 
        content: Dict[str, Any], 
        comparison_data: Dict[str, Any], 
        guidelines: Dict[str, Any]
    ) -> float:
        """
        Evaluate format consistency of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            comparison_data (Dict[str, Any]): Data to compare against
            guidelines (Dict[str, Any]): Consistency guidelines
            
        Returns:
            float: Format consistency score between 0 and 1
        """
        # If no comparison data, return default score
        if not comparison_data:
            return 0.8  # Default score
        
        # Simple format checks - types consistency
        format_scores = []
        
        for name, data in comparison_data.items():
            if not isinstance(data, dict):
                continue
                
            # Check common keys for type consistency
            common_keys = set(content.keys()) & set(data.keys())
            if not common_keys:
                continue
                
            # Count keys with same type
            type_matches = 0
            for key in common_keys:
                if type(content[key]) == type(data[key]):
                    type_matches += 1
            
            format_scores.append(type_matches / len(common_keys))
        
        # Return average format consistency score
        if not format_scores:
            return 0.8  # Default score
            
        return sum(format_scores) / len(format_scores)
    
    def _evaluate_reference_consistency(
        self, 
        content: Dict[str, Any], 
        comparison_data: Dict[str, Any], 
        guidelines: Dict[str, Any]
    ) -> float:
        """
        Evaluate reference consistency across outputs.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            comparison_data (Dict[str, Any]): Data to compare against
            guidelines (Dict[str, Any]): Consistency guidelines
            
        Returns:
            float: Reference consistency score between 0 and 1
        """
        # Simple implementation - return default score
        return 0.8  # Default score
    
    def _evaluate_value_consistency(
        self, 
        content: Dict[str, Any], 
        comparison_data: Dict[str, Any], 
        guidelines: Dict[str, Any]
    ) -> float:
        """
        Evaluate value consistency across outputs.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            comparison_data (Dict[str, Any]): Data to compare against
            guidelines (Dict[str, Any]): Consistency guidelines
            
        Returns:
            float: Value consistency score between 0 and 1
        """
        # If no comparison data, return default score
        if not comparison_data:
            return 0.8  # Default score
        
        # Simple value checks - common values consistency
        value_scores = []
        
        for name, data in comparison_data.items():
            if not isinstance(data, dict):
                continue
                
            # Check common keys for value consistency
            common_keys = set(content.keys()) & set(data.keys())
            if not common_keys:
                continue
                
            # Count keys with same value
            value_matches = 0
            for key in common_keys:
                if content[key] == data[key]:
                    value_matches += 1
            
            value_scores.append(value_matches / len(common_keys))
        
        # Return average value consistency score
        if not value_scores:
            return 0.8  # Default score
            
        return sum(value_scores) / len(value_scores)
    
    def _count_differences(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> int:
        """
        Count the number of differences between two objects.
        
        Args:
            obj1 (Dict[str, Any]): First object
            obj2 (Dict[str, Any]): Second object
            
        Returns:
            int: Number of differences
        """
        if not isinstance(obj1, dict) or not isinstance(obj2, dict):
            return 1 if obj1 != obj2 else 0
        
        diff_count = 0
        
        # Check keys only in obj1
        for key in set(obj1.keys()) - set(obj2.keys()):
            diff_count += 1
        
        # Check keys only in obj2
        for key in set(obj2.keys()) - set(obj1.keys()):
            diff_count += 1
        
        # Check common keys
        for key in set(obj1.keys()) & set(obj2.keys()):
            if isinstance(obj1[key], dict) and isinstance(obj2[key], dict):
                diff_count += self._count_differences(obj1[key], obj2[key])
            elif obj1[key] != obj2[key]:
                diff_count += 1
        
        return diff_count 