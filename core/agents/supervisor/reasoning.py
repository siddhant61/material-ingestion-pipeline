"""
Supervisor Agent Reasoning Component

This module provides the main reasoning capabilities for the SupervisorAgent,
coordinating quality checks, consistency evaluations, and content refinement.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json

# Import reasoning components
from .quality_reasoning import QualityReasoning
from .consistency_reasoning import ConsistencyReasoning
from .refinement_reasoning import RefinementReasoning
from .pattern_analysis import PatternAnalysis
from .schemas import QualityCheckSchema, ConsistencyCheckSchema, RefinementSchema, GuidelineSchema

# Configure logging
logger = logging.getLogger(__name__)

class SupervisorReasoning:
    """
    Main reasoning component for the SupervisorAgent.
    
    This class orchestrates the quality checks, consistency evaluations,
    and refinement processes, providing a unified interface for the agent.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the SupervisorReasoning component.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        
        # Initialize specialized reasoning components
        logger.info("Initializing specialized reasoning components")
        self.quality_reasoning = QualityReasoning(self.config.get("quality", {}))
        self.consistency_reasoning = ConsistencyReasoning(self.config.get("consistency", {}))
        self.refinement_reasoning = RefinementReasoning(self.config.get("refinement", {}))
        self.pattern_analysis = PatternAnalysis(self.config.get("pattern_analysis", {}))
        
        # Initialize supervision guidelines
        self.supervision_guidelines = self._init_supervision_guidelines()
        
        logger.info("SupervisorReasoning initialized")
    
    def _init_supervision_guidelines(self) -> Dict[str, Any]:
        """
        Initialize default supervision guidelines.
        
        Returns:
            Dict[str, Any]: Default supervision guidelines
        """
        # Load guidelines from config if available
        if "guidelines" in self.config:
            try:
                guidelines = self.config["guidelines"]
                logger.info("Loaded supervision guidelines from config")
                return GuidelineSchema.format(guidelines)
            except Exception as e:
                logger.error(f"Error loading guidelines from config: {str(e)}")
        
        # Default guidelines
        return {
            "quality": {
                "completeness_threshold": 0.7,
                "educational_value_threshold": 0.7,
                "accuracy_threshold": 0.8,
                "clarity_threshold": 0.7,
                "structure_threshold": 0.7
            },
            "consistency": {
                "schema_consistency_threshold": 0.8,
                "terminology_consistency_threshold": 0.7,
                "format_consistency_threshold": 0.7,
                "reference_consistency_threshold": 0.7,
                "value_consistency_threshold": 0.7
            },
            "refinement": {
                "quality_threshold": 0.7,
                "consistency_threshold": 0.7,
                "refinement_strategy": "incremental"
            }
        }
    
    def evaluate_agent_output(
        self, 
        agent_name: str,
        content: Dict[str, Any],
        comparison_data: Optional[Dict[str, Dict[str, Any]]] = None,
        guidelines: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate an agent's output for quality and consistency.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            comparison_data (Dict[str, Dict[str, Any]], optional): Data to compare with
            guidelines (Dict[str, Any], optional): Custom guidelines for this evaluation
            
        Returns:
            Dict[str, Any]: Evaluation results
        """
        try:
            logger.info(f"Evaluating output from agent: {agent_name}")
            
            # Use provided guidelines or defaults
            eval_guidelines = guidelines or self.supervision_guidelines
            
            # Analyze patterns in the content
            patterns = self.pattern_analysis.analyze(agent_name, content)
            
            # Prepare quality evaluation context
            quality_context = {
                "guidelines": eval_guidelines.get("quality", {}),
                "agent_type": agent_name,
                "patterns": patterns
            }
            
            # Evaluate quality
            quality_result = self.quality_reasoning.evaluate(content, quality_context)
            formatted_quality = QualityCheckSchema.format(quality_result)
            
            # Prepare consistency evaluation context
            consistency_context = {
                "guidelines": eval_guidelines.get("consistency", {}),
                "comparison_data": comparison_data or {}
            }
            
            # Evaluate consistency
            consistency_result = self.consistency_reasoning.evaluate(content, consistency_context)
            formatted_consistency = ConsistencyCheckSchema.format(consistency_result)
            
            # Register output for future consistency checks
            self.consistency_reasoning.register_output(agent_name, content)
            
            # Determine if refinement is needed
            needs_refinement = (
                quality_result.get("quality_score", 1.0) < eval_guidelines.get("refinement", {}).get("quality_threshold", 0.7) or
                consistency_result.get("consistency_score", 1.0) < eval_guidelines.get("refinement", {}).get("consistency_threshold", 0.7) or
                len(quality_result.get("issues", [])) > 0 or
                len(consistency_result.get("issues", [])) > 0
            )
            
            # Combine results
            result = {
                "agent_name": agent_name,
                "quality_check": formatted_quality,
                "consistency_check": formatted_consistency,
                "patterns": patterns,
                "needs_refinement": needs_refinement
            }
            
            logger.info(f"Evaluation completed for {agent_name}, needs refinement: {needs_refinement}")
            return result
            
        except Exception as e:
            logger.error(f"Error in agent output evaluation: {str(e)}")
            return {
                "agent_name": agent_name,
                "quality_check": {"quality_score": 0.0, "issues": [{"type": "error", "description": f"Quality evaluation failed: {str(e)}"}]},
                "consistency_check": {"consistency_score": 0.0, "issues": [{"type": "error", "description": f"Consistency evaluation failed: {str(e)}"}]},
                "patterns": {},
                "needs_refinement": True,
                "error": str(e)
            }
    
    def plan_refinement(
        self,
        agent_name: str,
        content: Dict[str, Any],
        evaluation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Plan refinements for agent output based on evaluation.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            evaluation_result (Dict[str, Any]): Evaluation results
            
        Returns:
            Dict[str, Any]: Refinement plan
        """
        try:
            logger.info(f"Planning refinements for {agent_name}")
            
            # Extract quality and consistency checks
            quality_check = evaluation_result.get("quality_check", {})
            consistency_check = evaluation_result.get("consistency_check", {})
            
            # Generate refinement plan
            refinement_plan = self.refinement_reasoning.generate_refinement_plan(
                content,
                quality_check,
                consistency_check,
                agent_name
            )
            
            logger.info(f"Refinement plan generated for {agent_name}")
            return refinement_plan
            
        except Exception as e:
            logger.error(f"Error in refinement planning: {str(e)}")
            return {
                "needs_refinement": True,
                "priority_issues": [],
                "strategies": ["Fix fundamental issues with content"],
                "sections_to_refine": [],
                "estimated_improvement": 0.5,
                "refinement_focus": "general",
                "error": str(e)
            }
    
    def refine_content(
        self,
        agent_name: str,
        content: Dict[str, Any],
        refinement_plan: Dict[str, Any],
        model_refinements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Refine agent output based on refinement plan.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            refinement_plan (Dict[str, Any]): Refinement plan
            model_refinements (Dict[str, Any], optional): Refinements from model
            
        Returns:
            Dict[str, Any]: Refined content
        """
        try:
            logger.info(f"Refining content for {agent_name}")
            
            # Apply refinements
            refined_content = self.refinement_reasoning.apply_refinements(
                content,
                refinement_plan,
                model_refinements
            )
            
            # Format using schema
            result = RefinementSchema.format({
                "original": content,
                "refined": refined_content,
                "refinement_plan": refinement_plan,
                "agent_name": agent_name
            })
            
            logger.info(f"Content refinement completed for {agent_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error in content refinement: {str(e)}")
            # Return original content with error information
            return RefinementSchema.format({
                "original": content,
                "refined": content,  # No refinement due to error
                "refinement_plan": refinement_plan,
                "agent_name": agent_name,
                "error": str(e)
            })
    
    def generate_refinement_prompt(
        self,
        agent_name: str,
        content: Dict[str, Any],
        refinement_plan: Dict[str, Any]
    ) -> str:
        """
        Generate a prompt for model-based refinement.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            refinement_plan (Dict[str, Any]): Refinement plan
            
        Returns:
            str: Refinement prompt
        """
        try:
            logger.info(f"Generating refinement prompt for {agent_name}")
            
            # Generate prompt using refinement reasoning
            prompt = self.refinement_reasoning.generate_refinement_prompt(
                content,
                refinement_plan,
                agent_name
            )
            
            logger.info(f"Generated refinement prompt for {agent_name}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating refinement prompt: {str(e)}")
            
            # Fallback prompt
            return f"""
            # Refinement Request for {agent_name} Output
            
            Please refine the following content to improve its quality and consistency.
            Focus on fixing any obvious issues while maintaining the original structure and intent.
            
            ## Original Content
            ```json
            {json.dumps(content, indent=2)[:500]}...
            ```
            
            ## Requirements
            1. Improve overall quality and clarity
            2. Maintain the original structure and schema
            3. Return the complete refined content in valid JSON format
            """
    
    def update_guidelines(self, new_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update supervision guidelines.
        
        Args:
            new_guidelines (Dict[str, Any]): New guidelines to incorporate
            
        Returns:
            Dict[str, Any]: Updated guidelines
        """
        try:
            # Validate and format guidelines
            formatted_guidelines = GuidelineSchema.format(new_guidelines)
            
            # Update specific sections
            for section in ["quality", "consistency", "refinement"]:
                if section in formatted_guidelines:
                    if section not in self.supervision_guidelines:
                        self.supervision_guidelines[section] = {}
                    
                    self.supervision_guidelines[section].update(formatted_guidelines[section])
            
            logger.info("Supervision guidelines updated")
            return self.supervision_guidelines
            
        except Exception as e:
            logger.error(f"Error updating guidelines: {str(e)}")
            return self.supervision_guidelines
    
    def get_guidelines(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current supervision guidelines.
        
        Args:
            section (str, optional): Specific section to retrieve
            
        Returns:
            Dict[str, Any]: Current guidelines
        """
        if section:
            return self.supervision_guidelines.get(section, {})
        return self.supervision_guidelines 