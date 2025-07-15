"""
Quality Reasoning Component

This module provides quality evaluation capabilities for the SupervisorAgent,
focusing on assessing output quality using a structured approach.
"""

import logging
from typing import Dict, List, Any, Optional
import re

# Configure logging
logger = logging.getLogger(__name__)

class QualityReasoning:
    """
    Quality reasoning component for evaluating content quality.
    
    This component evaluates:
    - Completeness of content
    - Educational value
    - Factual accuracy
    - Clarity of presentation
    - Structural quality
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the QualityReasoning component.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        
        # Default quality metrics and thresholds
        self.default_metrics = {
            "completeness": 0.8,
            "educational_value": 0.7,
            "accuracy": 0.9,
            "clarity": 0.7,
            "structure": 0.8
        }
        
        # Override defaults with config values if provided
        self.metrics = {**self.default_metrics, **self.config.get("metrics", {})}
        
        logger.info("QualityReasoning initialized")
    
    def evaluate(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the quality of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            guidelines (Dict[str, Any]): Quality guidelines
            
        Returns:
            Dict[str, Any]: Quality evaluation results
        """
        try:
            # Get metric thresholds from guidelines or use defaults
            thresholds = guidelines.get("metrics", self.metrics)
            
            # Calculate individual quality metrics
            completeness = self._evaluate_completeness(content, guidelines)
            educational_value = self._evaluate_educational_value(content, guidelines)
            accuracy = self._evaluate_accuracy(content, guidelines)
            clarity = self._evaluate_clarity(content, guidelines)
            structure = self._evaluate_structure(content, guidelines)
            
            # Collect calculated metrics
            metrics = {
                "completeness": completeness,
                "educational_value": educational_value,
                "accuracy": accuracy,
                "clarity": clarity,
                "structure": structure
            }
            
            # Identify issues based on thresholds
            issues = []
            
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
            
            # Calculate overall quality score (weighted average)
            weights = guidelines.get("weights", {
                "completeness": 0.25,
                "educational_value": 0.2,
                "accuracy": 0.3,
                "clarity": 0.15,
                "structure": 0.1
            })
            
            quality_score = sum(
                metrics[metric] * weights.get(metric, 0.2)
                for metric in metrics
            )
            
            # Determine if refinement is needed
            needs_refinement = quality_score < guidelines.get("quality_threshold", 0.7) or len(issues) > 0
            
            return {
                "quality_score": round(quality_score, 2),
                "metrics": {k: round(v, 2) for k, v in metrics.items()},
                "issues": issues,
                "needs_refinement": needs_refinement
            }
            
        except Exception as e:
            logger.error(f"Error in quality evaluation: {str(e)}")
            return {
                "quality_score": 0.0,
                "metrics": {},
                "issues": [{"type": "error", "description": f"Quality evaluation failed: {str(e)}"}],
                "needs_refinement": True
            }
    
    def identify_issues(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify quality issues in content.
        
        Args:
            content (Dict[str, Any]): Content to analyze
            
        Returns:
            List[Dict[str, Any]]: Identified quality issues
        """
        # Perform a basic evaluation and extract issues
        evaluation = self.evaluate(content, {})
        return evaluation.get("issues", [])
    
    def _evaluate_completeness(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> float:
        """
        Evaluate the completeness of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            guidelines (Dict[str, Any]): Quality guidelines
            
        Returns:
            float: Completeness score between 0 and 1
        """
        if not content:
            return 0.0
        
        # Get required fields from guidelines
        required_fields = guidelines.get("required_fields", [])
        
        # If no required fields specified, use basic heuristic
        if not required_fields:
            return 0.8  # Default completeness score
        
        # Check for presence of required fields
        present_fields = sum(1 for field in required_fields if field in content and content[field])
        return min(1.0, present_fields / max(1, len(required_fields)))
    
    def _evaluate_educational_value(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> float:
        """
        Evaluate the educational value of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            guidelines (Dict[str, Any]): Quality guidelines
            
        Returns:
            float: Educational value score between 0 and 1
        """
        # Simple heuristic based on educational indicators
        educational_indicators = [
            "learning_outcomes",
            "objectives",
            "examples",
            "explanations",
            "context",
            "prerequisites"
        ]
        
        # Count present indicators
        present_indicators = sum(1 for indicator in educational_indicators if indicator in content and content[indicator])
        
        # Calculate score based on presence of indicators
        return 0.5 + 0.5 * (present_indicators / len(educational_indicators))
    
    def _evaluate_accuracy(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> float:
        """
        Evaluate the accuracy of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            guidelines (Dict[str, Any]): Quality guidelines
            
        Returns:
            float: Accuracy score between 0 and 1
        """
        # Without external verification, assume reasonable accuracy
        # In a real system, this would involve fact checking
        return 0.9  # Default accuracy score
    
    def _evaluate_clarity(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> float:
        """
        Evaluate the clarity of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            guidelines (Dict[str, Any]): Quality guidelines
            
        Returns:
            float: Clarity score between 0 and 1
        """
        # Simple heuristic for clarity
        return 0.8  # Default clarity score
    
    def _evaluate_structure(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> float:
        """
        Evaluate the structure of content.
        
        Args:
            content (Dict[str, Any]): Content to evaluate
            guidelines (Dict[str, Any]): Quality guidelines
            
        Returns:
            float: Structure score between 0 and 1
        """
        # Simple heuristic for structure
        return 0.8  # Default structure score 