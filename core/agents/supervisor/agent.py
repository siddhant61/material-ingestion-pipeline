"""
Supervisor Agent

This module provides the main SupervisorAgent class that oversees the output quality
and consistency of other agents in the educational content pipeline.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json

# Import SupervisorAgent components
from .models import SupervisorModels
from .reasoning import SupervisorReasoning
from .schemas import QualityCheckSchema, ConsistencyCheckSchema, RefinementSchema, GuidelineSchema

# Configure logging
logger = logging.getLogger(__name__)

class SupervisorAgent:
    """
    Supervisor Agent for quality control, consistency enforcement, and refinement.
    
    This agent monitors and improves the output of other agents in the educational
    content pipeline, ensuring high quality, consistent, and educationally valuable content.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the SupervisorAgent.
        
        Args:
            config (Dict[str, Any], optional): Configuration options
        """
        self.config = config or {}
        
        # Initialize core components
        logger.info("Initializing SupervisorAgent")
        self.models = SupervisorModels(self.config.get("models", {}))
        self.reasoning = SupervisorReasoning(self.config.get("reasoning", {}))
        
        # Output storage
        self.output_dir = Path(self.config.get("output_dir", "output/supervisor"))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Track agent outputs for comparison
        self.agent_outputs = {}
        
        logger.info("SupervisorAgent initialized")
    
    def supervise(
        self, 
        agent_name: str,
        content: Dict[str, Any],
        comparison_data: Optional[Dict[str, Dict[str, Any]]] = None,
        guidelines: Optional[Dict[str, Any]] = None,
        auto_refine: bool = True
    ) -> Dict[str, Any]:
        """
        Supervise agent output for quality and consistency, refining if needed.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            comparison_data (Dict[str, Dict[str, Any]], optional): Data to compare with
            guidelines (Dict[str, Any], optional): Custom guidelines for this supervision
            auto_refine (bool): Whether to automatically refine output if needed
            
        Returns:
            Dict[str, Any]: Supervision results
        """
        try:
            logger.info(f"Supervising output from agent: {agent_name}")
            
            # Store content for future comparisons
            self._store_agent_output(agent_name, content)
            
            # If comparison data not provided, use stored outputs
            if not comparison_data:
                comparison_data = self._get_comparison_data(agent_name)
            
            # Evaluate output quality and consistency
            evaluation = self.reasoning.evaluate_agent_output(
                agent_name,
                content,
                comparison_data,
                guidelines
            )
            
            # Determine if refinement is needed
            if evaluation.get("needs_refinement", False) and auto_refine:
                # Generate refinement plan
                refinement_plan = self.reasoning.plan_refinement(
                    agent_name,
                    content,
                    evaluation
                )
                
                # Generate refinement prompt
                refinement_prompt = self.reasoning.generate_refinement_prompt(
                    agent_name,
                    content,
                    refinement_plan
                )
                
                # Get model refinements
                model_refinements = self.models.refine_content(
                    content=content,
                    quality_check=evaluation["quality_check"],
                    consistency_check=evaluation["consistency_check"],
                    guidelines=self.reasoning.get_guidelines()
                )
                
                # Apply refinements
                refinement = self.reasoning.refine_content(
                    agent_name,
                    content,
                    refinement_plan,
                    model_refinements
                )
                
                # Save refinement
                self._save_refinement(agent_name, refinement)
                
                # Add refinement to result
                result = {
                    "agent_name": agent_name,
                    "original_content": content,
                    "evaluation": evaluation,
                    "refinement_plan": refinement_plan,
                    "refinement": refinement,
                    "refined_content": refinement.get("refined", content)
                }
            else:
                # No refinement needed or auto_refine is False
                result = {
                    "agent_name": agent_name,
                    "original_content": content,
                    "evaluation": evaluation,
                    "refined_content": content  # No refinement applied
                }
            
            logger.info(f"Supervision completed for {agent_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error in supervision: {str(e)}")
            return {
                "agent_name": agent_name,
                "original_content": content,
                "evaluation": {
                    "quality_check": {"quality_score": 0.0, "issues": [{"type": "error", "description": f"Supervision failed: {str(e)}"}]},
                    "consistency_check": {"consistency_score": 0.0, "issues": []}
                },
                "error": str(e),
                "refined_content": content  # Return original content on error
            }
    
    def evaluate_quality(
        self,
        agent_name: str,
        content: Dict[str, Any],
        guidelines: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate quality of agent output without refinement.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            guidelines (Dict[str, Any], optional): Custom guidelines for quality evaluation
            
        Returns:
            Dict[str, Any]: Quality evaluation results
        """
        try:
            logger.info(f"Evaluating quality for {agent_name}")
            
            # Use AI model for quality evaluation
            quality_result = self.models.evaluate_quality(
                content=content,
                agent_type=agent_name,
                guidelines=guidelines or self.reasoning.get_guidelines("quality")
            )
            
            # Format using schema
            formatted_result = QualityCheckSchema.format(quality_result)
            
            logger.info(f"Quality evaluation completed for {agent_name}")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in quality evaluation: {str(e)}")
            return {
                "quality_score": 0.0,
                "metrics": {},
                "issues": [{"type": "error", "description": f"Quality evaluation failed: {str(e)}"}]
            }
    
    def evaluate_consistency(
        self,
        agent_name: str,
        content: Dict[str, Any],
        comparison_data: Optional[Dict[str, Dict[str, Any]]] = None,
        guidelines: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate consistency of agent output without refinement.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            comparison_data (Dict[str, Dict[str, Any]], optional): Data to compare with
            guidelines (Dict[str, Any], optional): Custom guidelines for consistency evaluation
            
        Returns:
            Dict[str, Any]: Consistency evaluation results
        """
        try:
            logger.info(f"Evaluating consistency for {agent_name}")
            
            # If comparison data not provided, use stored outputs
            if not comparison_data:
                comparison_data = self._get_comparison_data(agent_name)
            
            # Use AI model for consistency evaluation
            consistency_result = self.models.evaluate_consistency(
                content=content,
                comparison_data=comparison_data,
                agent_type=agent_name,
                guidelines=guidelines or self.reasoning.get_guidelines("consistency")
            )
            
            # Format using schema
            formatted_result = ConsistencyCheckSchema.format(consistency_result)
            
            logger.info(f"Consistency evaluation completed for {agent_name}")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in consistency evaluation: {str(e)}")
            return {
                "consistency_score": 0.0,
                "metrics": {},
                "issues": [{"type": "error", "description": f"Consistency evaluation failed: {str(e)}"}]
            }
    
    def refine_output(
        self,
        agent_name: str,
        content: Dict[str, Any],
        quality_evaluation: Optional[Dict[str, Any]] = None,
        consistency_evaluation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Refine agent output based on quality and consistency evaluations.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
            quality_evaluation (Dict[str, Any], optional): Quality evaluation results
            consistency_evaluation (Dict[str, Any], optional): Consistency evaluation results
            
        Returns:
            Dict[str, Any]: Refinement results
        """
        try:
            logger.info(f"Refining output for {agent_name}")
            
            # If evaluations not provided, perform them
            if not quality_evaluation:
                quality_evaluation = self.evaluate_quality(agent_name, content)
                
            if not consistency_evaluation:
                consistency_evaluation = self.evaluate_consistency(agent_name, content)
            
            # Determine if refinement is needed
            needs_refinement = (
                quality_evaluation.get("quality_score", 1.0) < self.reasoning.get_guidelines("refinement").get("quality_threshold", 0.7) or
                consistency_evaluation.get("consistency_score", 1.0) < self.reasoning.get_guidelines("refinement").get("consistency_threshold", 0.7) or
                len(quality_evaluation.get("issues", [])) > 0 or
                len(consistency_evaluation.get("issues", [])) > 0
            )
            
            if not needs_refinement:
                logger.info(f"No refinement needed for {agent_name}")
                return {
                    "original": content,
                    "refined": content,
                    "changes": [],
                    "refinement_applied": False
                }
            
            # Create evaluation result for refinement planning
            evaluation_result = {
                "agent_name": agent_name,
                "quality_check": quality_evaluation,
                "consistency_check": consistency_evaluation,
                "needs_refinement": needs_refinement
            }
            
            # Generate refinement plan
            refinement_plan = self.reasoning.plan_refinement(
                agent_name,
                content,
                evaluation_result
            )
            
            # Get model refinements
            model_refinements = self.models.refine_content(
                content=content,
                quality_check=quality_evaluation,
                consistency_check=consistency_evaluation,
                guidelines=self.reasoning.get_guidelines()
            )
            
            # Apply refinements
            refinement = self.reasoning.refine_content(
                agent_name,
                content,
                refinement_plan,
                model_refinements
            )
            
            # Save refinement
            self._save_refinement(agent_name, refinement)
            
            logger.info(f"Refinement completed for {agent_name}")
            return refinement
            
        except Exception as e:
            logger.error(f"Error in refinement: {str(e)}")
            return {
                "original": content,
                "refined": content,
                "changes": [],
                "refinement_applied": False,
                "error": str(e)
            }
    
    def update_guidelines(self, new_guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update supervision guidelines.
        
        Args:
            new_guidelines (Dict[str, Any]): New guidelines to incorporate
            
        Returns:
            Dict[str, Any]: Updated guidelines
        """
        return self.reasoning.update_guidelines(new_guidelines)
    
    def get_guidelines(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current supervision guidelines.
        
        Args:
            section (str, optional): Specific section to retrieve
            
        Returns:
            Dict[str, Any]: Current guidelines
        """
        return self.reasoning.get_guidelines(section)
    
    def _store_agent_output(self, agent_name: str, content: Dict[str, Any]) -> None:
        """
        Store agent output for future comparison.
        
        Args:
            agent_name (str): Name of the agent
            content (Dict[str, Any]): Agent output content
        """
        try:
            logger.info(f"Storing output from agent: {agent_name}")
            
            # Handle content of different types
            if not isinstance(content, dict):
                logger.warning(f"Content from {agent_name} is not a dictionary, wrapping it")
                content = {"raw_content": content}
            
            # Initialize list for this agent if it doesn't exist
            if agent_name not in self.agent_outputs:
                self.agent_outputs[agent_name] = []
            
            # Add content to agent outputs
            output_entry = {
                "timestamp": None,  # Will be filled in by datetime
                "content": content
            }
            
            # Add timestamp
            from datetime import datetime
            output_entry["timestamp"] = datetime.now().isoformat()
            
            # Save to agent outputs
            self.agent_outputs[agent_name].append(output_entry)
            
            # Prune history if needed (keep last 5 outputs)
            if len(self.agent_outputs[agent_name]) > 5:
                self.agent_outputs[agent_name] = self.agent_outputs[agent_name][-5:]
            
            logger.info(f"Stored output from {agent_name}, now have {len(self.agent_outputs[agent_name])} outputs")
        except Exception as e:
            logger.error(f"Error saving agent output: {str(e)}")
    
    def _get_comparison_data(self, agent_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get comparison data for consistency evaluation.
        
        Args:
            agent_name (str): Name of the agent
            
        Returns:
            Dict[str, Dict[str, Any]]: Comparison data
        """
        comparison_data = {}
        
        try:
            logger.info(f"Getting comparison data for agent: {agent_name}")
            
            # Get past outputs for this agent
            if agent_name in self.agent_outputs and len(self.agent_outputs[agent_name]) > 1:
                for i, output_entry in enumerate(self.agent_outputs[agent_name][:-1]):  # All except the most recent
                    comparison_data[f"{agent_name}_previous_{i+1}"] = output_entry["content"]
            
            # Get outputs from related agents
            for other_agent, outputs in self.agent_outputs.items():
                if other_agent != agent_name and outputs:
                    # Get the latest output
                    latest_output = outputs[-1]["content"]
                    comparison_data[f"{other_agent}_latest"] = latest_output
            
            logger.info(f"Found {len(comparison_data)} comparison data entries for {agent_name}")
            return comparison_data
            
        except Exception as e:
            logger.error(f"Error getting comparison data: {str(e)}")
            return {}
    
    def _save_refinement(self, agent_name: str, refinement: Dict[str, Any]) -> None:
        """
        Save refinement results to disk.
        
        Args:
            agent_name (str): Name of the agent
            refinement (Dict[str, Any]): Refinement results
        """
        from datetime import datetime
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to disk
        refinement_file = self.output_dir / f"{agent_name}_refinement_{timestamp}.json"
        try:
            with open(refinement_file, 'w') as f:
                json.dump(refinement, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving refinement: {str(e)}")
            
    def get_agent_outputs(self, agent_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get stored agent outputs.
        
        Args:
            agent_name (str, optional): Name of agent to get outputs for
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Stored agent outputs
        """
        if agent_name:
            return {agent_name: self.agent_outputs.get(agent_name, [])}
        return self.agent_outputs 