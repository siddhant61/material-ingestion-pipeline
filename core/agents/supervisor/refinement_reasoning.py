"""
Refinement Reasoning Component

This module provides content refinement capabilities for the SupervisorAgent,
focusing on improving agent outputs based on quality and consistency evaluations.
"""

import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class RefinementReasoning:
    """
    Refinement reasoning component for improving content quality and consistency.
    
    This component:
    - Analyzes quality and consistency issues
    - Prioritizes issues for refinement
    - Generates refinement strategies
    - Provides specific refinement guidance
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the RefinementReasoning component.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        
        # Refinement priority thresholds
        self.priority_thresholds = {
            "high": 0.5,    # High priority if score below 0.5
            "medium": 0.7,  # Medium priority if score below 0.7
            "low": 0.9      # Low priority if score below 0.9
        }
        
        # Override defaults with config values if provided
        if "priority_thresholds" in self.config:
            self.priority_thresholds.update(self.config["priority_thresholds"])
        
        logger.info("RefinementReasoning initialized")
    
    def generate_refinement_plan(
        self, 
        content: Dict[str, Any], 
        quality_evaluation: Dict[str, Any], 
        consistency_evaluation: Dict[str, Any],
        agent_type: str
    ) -> Dict[str, Any]:
        """
        Generate a refinement plan based on quality and consistency evaluations.
        
        Args:
            content (Dict[str, Any]): Content to refine
            quality_evaluation (Dict[str, Any]): Quality evaluation results
            consistency_evaluation (Dict[str, Any]): Consistency evaluation results
            agent_type (str): Type of agent that generated the content
            
        Returns:
            Dict[str, Any]: Refinement plan
        """
        try:
            # Extract issues from evaluations
            quality_issues = quality_evaluation.get("issues", [])
            consistency_issues = consistency_evaluation.get("issues", [])
            
            # Combine and prioritize issues
            all_issues = self._prioritize_issues(quality_issues, consistency_issues)
            
            # Generate refinement strategies for issues
            refinement_strategies = self._generate_strategies(all_issues, agent_type)
            
            # Determine sections to refine
            sections_to_refine = self._identify_sections_to_refine(content, all_issues)
            
            # Create refinement plan
            refinement_plan = {
                "needs_refinement": len(all_issues) > 0,
                "priority_issues": all_issues[:3],  # Top 3 issues to address
                "strategies": refinement_strategies,
                "sections_to_refine": sections_to_refine,
                "estimated_improvement": self._estimate_improvement(all_issues, content),
                "refinement_focus": self._determine_refinement_focus(quality_evaluation, consistency_evaluation)
            }
            
            logger.info(f"Generated refinement plan with {len(all_issues)} issues")
            return refinement_plan
            
        except Exception as e:
            logger.error(f"Error generating refinement plan: {str(e)}")
            return {
                "needs_refinement": True,
                "priority_issues": [],
                "strategies": ["Fix fundamental issues with content structure"],
                "sections_to_refine": [],
                "estimated_improvement": 0.5,
                "refinement_focus": "structure",
                "error": str(e)
            }
    
    def apply_refinements(
        self,
        content: Dict[str, Any],
        refinement_plan: Dict[str, Any],
        model_refinements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply refinements to content based on refinement plan.
        
        Args:
            content (Dict[str, Any]): Original content to refine
            refinement_plan (Dict[str, Any]): Refinement plan
            model_refinements (Dict[str, Any], optional): Refinements from model
            
        Returns:
            Dict[str, Any]: Refined content
        """
        try:
            # If no refinement needed, return original content
            if not refinement_plan.get("needs_refinement", False):
                logger.info("No refinement needed, returning original content")
                return content
            
            # If model refinements provided, incorporate them
            if model_refinements:
                logger.info("Applying model-generated refinements")
                return self._merge_refinements(content, model_refinements)
            
            # Otherwise, apply basic structural refinements
            logger.info("Applying basic structural refinements")
            refined_content = self._apply_basic_refinements(content, refinement_plan)
            
            # Add refinement metadata
            if isinstance(refined_content, dict):
                refined_content["_refinement_applied"] = True
                refined_content["_refinement_timestamp"] = self._get_timestamp()
                refined_content["_refinement_source"] = "supervisor_agent"
            
            return refined_content
            
        except Exception as e:
            logger.error(f"Error applying refinements: {str(e)}")
            # Return original content with error metadata
            if isinstance(content, dict):
                content["_refinement_error"] = str(e)
            return content
    
    def generate_refinement_prompt(
        self,
        content: Dict[str, Any],
        refinement_plan: Dict[str, Any],
        agent_type: str
    ) -> str:
        """
        Generate a prompt for model-based refinement.
        
        Args:
            content (Dict[str, Any]): Content to refine
            refinement_plan (Dict[str, Any]): Refinement plan
            agent_type (str): Type of agent that generated the content
            
        Returns:
            str: Refinement prompt
        """
        # Extract key information from refinement plan
        priority_issues = refinement_plan.get("priority_issues", [])
        strategies = refinement_plan.get("strategies", [])
        focus = refinement_plan.get("refinement_focus", "general")
        
        # Build the prompt
        prompt = [
            f"# Content Refinement for {agent_type.replace('_', ' ').title()} Output",
            "",
            "## Original Content",
            f"```json\n{str(content)[:500]}...\n```",
            "",
            "## Refinement Requirements",
            "Please refine the above content to address the following issues:",
            ""
        ]
        
        # Add issues
        for i, issue in enumerate(priority_issues[:5]):  # Limit to top 5 issues
            issue_type = issue.get("type", "unknown")
            description = issue.get("description", "No description")
            severity = issue.get("severity", "medium")
            
            prompt.append(f"{i+1}. **{issue_type.replace('_', ' ').title()}** ({severity} severity): {description}")
        
        prompt.extend([
            "",
            "## Refinement Focus",
            f"Primary focus: {focus.replace('_', ' ').title()}",
            "",
            "## Refinement Strategies"
        ])
        
        # Add strategies
        for i, strategy in enumerate(strategies[:5]):  # Limit to top 5 strategies
            prompt.append(f"{i+1}. {strategy}")
        
        prompt.extend([
            "",
            "## Output Requirements",
            "1. Maintain the original structure and schema of the content",
            "2. Preserve all key information while improving quality and consistency",
            "3. Do not introduce new facts or information not present in the original",
            "4. Return the complete refined content in valid JSON format",
            "5. Focus on addressing the identified issues while preserving the original intent"
        ])
        
        return "\n".join(prompt)
    
    def _prioritize_issues(
        self, 
        quality_issues: List[Dict[str, Any]], 
        consistency_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Combine and prioritize quality and consistency issues.
        
        Args:
            quality_issues (List[Dict[str, Any]]): Quality issues
            consistency_issues (List[Dict[str, Any]]): Consistency issues
            
        Returns:
            List[Dict[str, Any]]: Prioritized issues
        """
        # Add source to each issue
        for issue in quality_issues:
            issue["source"] = "quality"
        
        for issue in consistency_issues:
            issue["source"] = "consistency"
        
        # Combine all issues
        all_issues = quality_issues + consistency_issues
        
        # Sort by severity first, then by source (quality before consistency)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        source_order = {"quality": 0, "consistency": 1}
        
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (
                severity_order.get(x.get("severity", "low"), 3),
                source_order.get(x.get("source", "consistency"), 2)
            )
        )
        
        return sorted_issues
    
    def _generate_strategies(
        self,
        issues: List[Dict[str, Any]],
        agent_type: str
    ) -> List[str]:
        """
        Generate refinement strategies based on issues.
        
        Args:
            issues (List[Dict[str, Any]]): Prioritized issues
            agent_type (str): Type of agent that generated the content
            
        Returns:
            List[str]: Refinement strategies
        """
        strategies = []
        
        # Map issue types to strategies
        strategy_map = {
            # Quality issue strategies
            "completeness": [
                "Add missing required information",
                "Expand sections that lack detail",
                "Include all necessary components"
            ],
            "educational_value": [
                "Enhance explanations with examples",
                "Add learning objectives or outcomes",
                "Improve pedagogical structure"
            ],
            "accuracy": [
                "Correct factual errors",
                "Verify and correct technical information",
                "Ensure mathematical/scientific accuracy"
            ],
            "clarity": [
                "Simplify complex explanations",
                "Improve sentence structure and readability",
                "Use consistent terminology"
            ],
            "structure": [
                "Reorganize content for logical flow",
                "Add appropriate headers and sections",
                "Ensure hierarchical organization"
            ],
            
            # Consistency issue strategies
            "schema_consistency": [
                "Standardize the data structure",
                "Ensure all required fields are present",
                "Match schema with other outputs"
            ],
            "terminology_consistency": [
                "Use consistent terminology throughout",
                "Align terms with glossary definitions",
                "Standardize technical terms"
            ],
            "format_consistency": [
                "Standardize data formats",
                "Use consistent date/number formats",
                "Apply consistent formatting"
            ],
            "reference_consistency": [
                "Ensure consistent references",
                "Standardize citation format",
                "Fix broken cross-references"
            ],
            "value_consistency": [
                "Ensure consistent values across sections",
                "Reconcile contradictory information",
                "Make quantitative information consistent"
            ]
        }
        
        # Agent-specific strategies
        agent_strategies = {
            "document_loader": [
                "Ensure all document sections are properly extracted",
                "Verify document metadata is accurate",
                "Check for parsing errors in complex sections"
            ],
            "course_context": [
                "Ensure course objectives are clearly defined",
                "Verify course structure is properly represented",
                "Check for consistency in course terminology"
            ],
            "transcript": [
                "Improve speech-to-text accuracy",
                "Ensure speaker attribution is consistent",
                "Add proper punctuation and formatting"
            ],
            "slide": [
                "Ensure visual elements are properly described",
                "Verify slide transitions are logical",
                "Check for consistent slide formatting"
            ],
            "context_fusion": [
                "Ensure data from all sources is properly integrated",
                "Verify no information is lost in fusion",
                "Check for consistency across fused elements"
            ],
            "knowledge_graph": [
                "Ensure entities are properly connected",
                "Verify relationship types are accurate",
                "Check for orphaned nodes or connections"
            ]
        }
        
        # Add strategies based on issues
        for issue in issues:
            issue_type = issue.get("type", "")
            if issue_type in strategy_map:
                # Add strategy if not already present
                for strategy in strategy_map[issue_type]:
                    if strategy not in strategies:
                        strategies.append(strategy)
        
        # Add agent-specific strategies
        if agent_type in agent_strategies:
            for strategy in agent_strategies[agent_type]:
                if strategy not in strategies:
                    strategies.append(strategy)
        
        # Add general strategies if no specific ones found
        if not strategies:
            strategies = [
                "Improve overall content quality",
                "Ensure consistency with other outputs",
                "Fix structural issues in content"
            ]
        
        return strategies[:7]  # Limit to top 7 strategies
    
    def _identify_sections_to_refine(
        self,
        content: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Identify sections of content that need refinement.
        
        Args:
            content (Dict[str, Any]): Content to refine
            issues (List[Dict[str, Any]]): Prioritized issues
            
        Returns:
            List[str]: Sections to refine
        """
        sections = []
        
        # Simple implementation - extract top-level keys as sections
        if isinstance(content, dict):
            sections = list(content.keys())
        
        # Filter sections based on specific issues
        # This is a simplified approach - a more advanced implementation would
        # analyze issues to determine which sections they relate to
        filtered_sections = []
        
        for issue in issues:
            issue_type = issue.get("type", "")
            details = issue.get("details", "")
            
            for section in sections:
                # Simple heuristic: if section name appears in issue details
                # or if issue type relates to section name
                if (
                    section in details or 
                    any(word in section.lower() for word in issue_type.lower().split("_"))
                ):
                    if section not in filtered_sections:
                        filtered_sections.append(section)
        
        # If no specific sections identified, include all
        if not filtered_sections:
            return sections
        
        return filtered_sections
    
    def _estimate_improvement(
        self, 
        issues: List[Dict[str, Any]], 
        content: Dict[str, Any]
    ) -> float:
        """
        Estimate potential improvement from refinements.
        
        Args:
            issues (List[Dict[str, Any]]): Prioritized issues
            content (Dict[str, Any]): Content to refine
            
        Returns:
            float: Estimated improvement (0-1)
        """
        if not issues:
            return 0.0
        
        # Calculate weighted score based on issue severity
        severity_weights = {
            "high": 0.3,
            "medium": 0.2,
            "low": 0.1
        }
        
        total_weight = 0.0
        for issue in issues:
            severity = issue.get("severity", "medium")
            total_weight += severity_weights.get(severity, 0.2)
        
        # Cap at 0.8 - we can't guarantee perfect improvement
        return min(0.8, total_weight)
    
    def _determine_refinement_focus(
        self,
        quality_evaluation: Dict[str, Any],
        consistency_evaluation: Dict[str, Any]
    ) -> str:
        """
        Determine the primary focus for refinement.
        
        Args:
            quality_evaluation (Dict[str, Any]): Quality evaluation results
            consistency_evaluation (Dict[str, Any]): Consistency evaluation results
            
        Returns:
            str: Refinement focus area
        """
        quality_score = quality_evaluation.get("quality_score", 0.8)
        consistency_score = consistency_evaluation.get("consistency_score", 0.8)
        
        # Quality metrics
        quality_metrics = quality_evaluation.get("metrics", {})
        
        # Find lowest quality metric
        lowest_quality_metric = None
        lowest_quality_score = 1.0
        
        for metric, score in quality_metrics.items():
            if score < lowest_quality_score:
                lowest_quality_score = score
                lowest_quality_metric = metric
        
        # Consistency metrics
        consistency_metrics = consistency_evaluation.get("metrics", {})
        
        # Find lowest consistency metric
        lowest_consistency_metric = None
        lowest_consistency_score = 1.0
        
        for metric, score in consistency_metrics.items():
            if score < lowest_consistency_score:
                lowest_consistency_score = score
                lowest_consistency_metric = metric
        
        # Determine primary focus
        if quality_score < consistency_score - 0.2:
            # Quality is much worse than consistency
            return lowest_quality_metric or "quality"
        elif consistency_score < quality_score - 0.2:
            # Consistency is much worse than quality
            return lowest_consistency_metric or "consistency"
        elif lowest_quality_score < lowest_consistency_score:
            # The worst quality metric is worse than the worst consistency metric
            return lowest_quality_metric or "quality"
        else:
            # The worst consistency metric is worse than the worst quality metric
            return lowest_consistency_metric or "consistency"
    
    def _apply_basic_refinements(
        self,
        content: Dict[str, Any],
        refinement_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply basic refinements based on the refinement plan.
        
        Args:
            content (Dict[str, Any]): Content to refine
            refinement_plan (Dict[str, Any]): Refinement plan
            
        Returns:
            Dict[str, Any]: Refined content
        """
        # This is a placeholder for basic refinements
        # In a real implementation, this would apply simple fixes
        # For now, we just return the original content
        return content
    
    def _merge_refinements(
        self,
        original_content: Dict[str, Any],
        model_refinements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge model refinements with original content.
        
        Args:
            original_content (Dict[str, Any]): Original content
            model_refinements (Dict[str, Any]): Model refinements
            
        Returns:
            Dict[str, Any]: Merged content
        """
        # Simple implementation - just return model refinements
        # In a real implementation, this would intelligently merge
        # changes while preserving structure
        return model_refinements
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat() 