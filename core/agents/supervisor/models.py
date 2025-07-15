"""
Supervisor Agent Models

This module provides the SupervisorModels class that manages
the AI models used by the SupervisorAgent.
"""

import os
import json
import logging
import time
import copy
from typing import Dict, List, Any, Optional, Union, Type
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class SupervisorModels:
    """
    Models component for the SupervisorAgent.
    
    This class manages the AI models used by the SupervisorAgent for
    quality checks, consistency checks, and output refinement.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the SupervisorModels component.
        
        Args:
            config: Configuration for models
        """
        self.config = config or {}
        
        # Initialize model configurations
        self.quality_model_name = self.config.get("quality_model", "gpt-4o-mini")
        self.consistency_model_name = self.config.get("consistency_model", "gpt-4o-mini")
        self.refinement_model_name = self.config.get("refinement_model", "gpt-4o")
        
        # Initialize model instances
        self._init_models()
        
        logger.info(f"Initialized supervisor models: quality={self.quality_model_name}, "
                   f"consistency={self.consistency_model_name}, "
                   f"refinement={self.refinement_model_name}")
    
    def _init_models(self):
        """Initialize the model instances."""
        try:
            # Import the necessary modules for models
            from core.utils.ai_models import AIModelFactory
            
            # Create model instances
            self.quality_model = AIModelFactory.create_model(self.quality_model_name)
            self.consistency_model = AIModelFactory.create_model(self.consistency_model_name)
            self.refinement_model = AIModelFactory.create_model(self.refinement_model_name)
            
            logger.info("Successfully initialized all supervisor models")
        except Exception as e:
            logger.error(f"Error initializing supervisor models: {e}")
            raise
    
    def evaluate_quality(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the quality of content based on guidelines.
        
        Args:
            content: Content to evaluate
            guidelines: Quality guidelines
            
        Returns:
            Quality evaluation results
        """
        logger.info(f"Evaluating quality using model: {self.quality_model_name}")
        
        try:
            # Create the evaluation prompt
            prompt = self._create_quality_eval_prompt(content, guidelines)
            
            # Get the evaluation from the model
            response = self.quality_model.generate(prompt)
            
            # Parse the response
            evaluation = self._parse_quality_eval_response(response)
            
            logger.info(f"Quality evaluation complete: score={evaluation.get('score', 0)}, "
                       f"needs_refinement={evaluation.get('needs_refinement', False)}")
            
            return evaluation
        except Exception as e:
            logger.error(f"Error in quality evaluation: {e}")
            return {
                "needs_refinement": True,
                "score": 0.0,
                "issues": [f"Error in quality evaluation: {str(e)}"],
                "strengths": [],
                "recommendations": ["Re-evaluate with proper error handling"]
            }
    
    def evaluate_consistency(self, content: Dict[str, Any], guidelines: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the consistency of content based on guidelines.
        
        Args:
            content: Content to evaluate
            guidelines: Consistency guidelines
            
        Returns:
            Consistency evaluation results
        """
        logger.info(f"Evaluating consistency using model: {self.consistency_model_name}")
        
        try:
            # Create the evaluation prompt
            prompt = self._create_consistency_eval_prompt(content, guidelines)
            
            # Get the evaluation from the model
            response = self.consistency_model.generate(prompt)
            
            # Parse the response
            evaluation = self._parse_consistency_eval_response(response)
            
            logger.info(f"Consistency evaluation complete: score={evaluation.get('score', 0)}, "
                       f"needs_refinement={evaluation.get('needs_refinement', False)}")
            
            return evaluation
        except Exception as e:
            logger.error(f"Error in consistency evaluation: {e}")
            return {
                "needs_refinement": True,
                "score": 0.0,
                "issues": [f"Error in consistency evaluation: {str(e)}"],
                "consistent_elements": [],
                "recommendations": ["Re-evaluate with proper error handling"]
            }
    
    def refine_content(
        self, 
        content: Dict[str, Any],
        quality_check: Dict[str, Any],
        consistency_check: Dict[str, Any],
        guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refine content based on quality and consistency checks.
        
        Args:
            content: Content to refine
            quality_check: Quality check results
            consistency_check: Consistency check results
            guidelines: Refinement guidelines
            
        Returns:
            Refined content
        """
        logger.info(f"Refining content using model: {self.refinement_model_name}")
        
        try:
            # Check if the content is very large (estimate token count)
            content_str = json.dumps(content, indent=2)
            token_estimate = len(content_str) // 4  # Rough estimate: ~4 chars per token
            
            # If token estimate is very large, use a summarized approach
            if token_estimate > 15000:  # Conservative threshold
                logger.warning(f"Content is very large (est. {token_estimate} tokens), using summarized approach")
                return self._refine_large_content(content, quality_check, consistency_check, guidelines)
            
            # For smaller content, use the standard approach
            # Create the refinement prompt
            prompt = self._create_refinement_prompt(
                content, 
                quality_check, 
                consistency_check,
                guidelines
            )
            
            # Get the refinement from the model
            response = self.refinement_model.generate(prompt)
            
            # Parse the response
            refined_content = self._parse_refinement_response(response, content)
            
            logger.info("Content refinement complete")
            
            return refined_content
        except Exception as e:
            logger.error(f"Error in content refinement: {e}")
            return content  # Return original content if refinement fails
    
    def _refine_large_content(
        self,
        content: Dict[str, Any],
        quality_check: Dict[str, Any],
        consistency_check: Dict[str, Any],
        guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refine very large content by breaking it into manageable chunks.
        
        Args:
            content: Large content to refine
            quality_check: Quality check results
            consistency_check: Consistency check results
            guidelines: Refinement guidelines
            
        Returns:
            Refined content
        """
        logger.info("Breaking large content into chunks for refinement")
        
        try:
            # Create a deep copy of the content to modify
            refined_content = copy.deepcopy(content)
            
            # Get the top-level keys to process separately
            top_level_keys = list(content.keys())
            
            # Process each top-level key separately
            for key in top_level_keys:
                if key in content and isinstance(content[key], (dict, list)):
                    # Get just this section of the content
                    section_content = {key: content[key]}
                    
                    # Create focused refinement guidelines
                    focused_guidelines = {
                        "focus_area": f"Refine only the '{key}' section of the content",
                        "general": guidelines.get("general", {}),
                        "specific": guidelines.get("specific", {}).get(key, {})
                    }
                    
                    # Extract relevant issues from the quality and consistency checks
                    focused_quality_check = self._extract_focused_issues(quality_check, key)
                    focused_consistency_check = self._extract_focused_issues(consistency_check, key)
                    
                    logger.info(f"Refining section: {key}")
                    
                    # Create the refinement prompt for this section
                    prompt = self._create_focused_refinement_prompt(
                        section_content,
                        focused_quality_check,
                        focused_consistency_check,
                        focused_guidelines
                    )
                    
                    try:
                        # Get the refinement from the model
                        response = self.refinement_model.generate(prompt)
                        
                        # Parse the response
                        section_refined = self._parse_refinement_response(response, section_content)
                        
                        # Update the refined content with this section
                        if key in section_refined:
                            refined_content[key] = section_refined[key]
                    except Exception as section_error:
                        logger.error(f"Error refining section '{key}': {section_error}")
                        # Keep the original section on error
            
            logger.info("Large content refinement complete")
            return refined_content
            
        except Exception as e:
            logger.error(f"Error in large content refinement: {e}")
            return content  # Return original content if refinement fails
    
    def _extract_focused_issues(self, check_results: Dict[str, Any], focus_key: str) -> Dict[str, Any]:
        """
        Extract issues relevant to a specific section of content.
        
        Args:
            check_results: Complete check results
            focus_key: The key to focus on
            
        Returns:
            Focused check results
        """
        focused_results = copy.deepcopy(check_results)
        
        # Filter issues to only those mentioning the focus key
        if "issues" in focused_results:
            focused_results["issues"] = [
                issue for issue in focused_results.get("issues", [])
                if focus_key.lower() in str(issue).lower()
            ]
        
        return focused_results
    
    def _create_focused_refinement_prompt(
        self,
        section_content: Dict[str, Any],
        quality_check: Dict[str, Any],
        consistency_check: Dict[str, Any],
        guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a prompt for focused content refinement.
        
        Args:
            section_content: Section of content to refine
            quality_check: Quality check results for this section
            consistency_check: Consistency check results for this section
            guidelines: Refinement guidelines
            
        Returns:
            Prompt for section refinement
        """
        # Convert the data to string representations
        content_str = json.dumps(section_content, indent=2)
        quality_check_str = json.dumps(quality_check, indent=2)
        consistency_check_str = json.dumps(consistency_check, indent=2)
        guidelines_str = json.dumps(guidelines, indent=2)
        
        # Create the system message
        system_message = (
            "You are an educational content refinement specialist. "
            "Your task is to refine a specific section of content based on quality and consistency checks "
            "according to the specified guidelines. "
            "Maintain the original structure and format while addressing the identified issues."
        )
        
        # Create the user message
        user_message = (
            f"Please refine the following section of content based on the quality and consistency checks "
            f"according to the provided guidelines.\n\n"
            f"CONTENT SECTION:\n{content_str}\n\n"
            f"QUALITY CHECK:\n{quality_check_str}\n\n"
            f"CONSISTENCY CHECK:\n{consistency_check_str}\n\n"
            f"GUIDELINES:\n{guidelines_str}\n\n"
            f"Respond with the refined section in the same JSON structure as the original content. "
            f"Only modify the section provided - do not add or modify other sections."
        )
        
        # Return the prompt
        return {"system": system_message, "user": user_message}
    
    def _create_quality_eval_prompt(
        self, 
        content: Dict[str, Any],
        guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a prompt for quality evaluation.
        
        Args:
            content: Content to evaluate
            guidelines: Quality guidelines
            
        Returns:
            Prompt for quality evaluation
        """
        # Convert the content and guidelines to a string representation
        content_str = json.dumps(content, indent=2)
        guidelines_str = json.dumps(guidelines, indent=2)
        
        # Create the system message
        system_message = (
            "You are an educational content quality evaluator. "
            "Your task is to evaluate the quality of the provided content "
            "according to the specified guidelines. "
            "Provide a thorough analysis of the content quality."
        )
        
        # Create the user message
        user_message = (
            f"Please evaluate the quality of the following content according to the provided guidelines.\n\n"
            f"CONTENT:\n{content_str}\n\n"
            f"GUIDELINES:\n{guidelines_str}\n\n"
            f"Respond with a JSON object containing the following fields:\n"
            f"- needs_refinement (boolean): Whether the content needs refinement\n"
            f"- score (float): Quality score between 0 and 1\n"
            f"- issues (array of strings): List of quality issues\n"
            f"- strengths (array of strings): List of quality strengths\n"
            f"- recommendations (array of strings): List of recommendations for improvement"
        )
        
        # Return the prompt
        return {"system": system_message, "user": user_message}
    
    def _parse_quality_eval_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the response from quality evaluation.
        
        Args:
            response: Response from the model
            
        Returns:
            Parsed quality evaluation
        """
        try:
            # Extract JSON from the response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            
            # Parse the JSON
            evaluation = json.loads(json_str)
            
            # Ensure all required fields are present
            if "needs_refinement" not in evaluation:
                evaluation["needs_refinement"] = False
            if "score" not in evaluation:
                evaluation["score"] = 0.0
            if "issues" not in evaluation:
                evaluation["issues"] = []
            if "strengths" not in evaluation:
                evaluation["strengths"] = []
            if "recommendations" not in evaluation:
                evaluation["recommendations"] = []
            
            return evaluation
        except Exception as e:
            logger.error(f"Error parsing quality evaluation response: {e}")
            return {
                "needs_refinement": True,
                "score": 0.0,
                "issues": [f"Error parsing quality evaluation response: {str(e)}"],
                "strengths": [],
                "recommendations": ["Re-evaluate with proper error handling"]
            }
    
    def _create_consistency_eval_prompt(
        self, 
        content: Dict[str, Any],
        guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a prompt for consistency evaluation.
        
        Args:
            content: Content to evaluate
            guidelines: Consistency guidelines
            
        Returns:
            Prompt for consistency evaluation
        """
        # Convert the content and guidelines to a string representation
        content_str = json.dumps(content, indent=2)
        guidelines_str = json.dumps(guidelines, indent=2)
        
        # Create the system message
        system_message = (
            "You are an educational content consistency evaluator. "
            "Your task is to evaluate the consistency of the provided content "
            "according to the specified guidelines. "
            "Provide a thorough analysis of the content consistency."
        )
        
        # Create the user message
        user_message = (
            f"Please evaluate the consistency of the following content according to the provided guidelines.\n\n"
            f"CONTENT:\n{content_str}\n\n"
            f"GUIDELINES:\n{guidelines_str}\n\n"
            f"Respond with a JSON object containing the following fields:\n"
            f"- needs_refinement (boolean): Whether the content needs refinement\n"
            f"- score (float): Consistency score between 0 and 1\n"
            f"- issues (array of strings): List of consistency issues\n"
            f"- consistent_elements (array of strings): List of elements that are consistent\n"
            f"- recommendations (array of strings): List of recommendations for improvement"
        )
        
        # Return the prompt
        return {"system": system_message, "user": user_message}
    
    def _parse_consistency_eval_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the response from consistency evaluation.
        
        Args:
            response: Response from the model
            
        Returns:
            Parsed consistency evaluation
        """
        try:
            # Extract JSON from the response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            
            # Parse the JSON
            evaluation = json.loads(json_str)
            
            # Ensure all required fields are present
            if "needs_refinement" not in evaluation:
                evaluation["needs_refinement"] = False
            if "score" not in evaluation:
                evaluation["score"] = 0.0
            if "issues" not in evaluation:
                evaluation["issues"] = []
            if "consistent_elements" not in evaluation:
                evaluation["consistent_elements"] = []
            if "recommendations" not in evaluation:
                evaluation["recommendations"] = []
            
            return evaluation
        except Exception as e:
            logger.error(f"Error parsing consistency evaluation response: {e}")
            return {
                "needs_refinement": True,
                "score": 0.0,
                "issues": [f"Error parsing consistency evaluation response: {str(e)}"],
                "consistent_elements": [],
                "recommendations": ["Re-evaluate with proper error handling"]
            }
    
    def _create_refinement_prompt(
        self, 
        content: Dict[str, Any],
        quality_check: Dict[str, Any],
        consistency_check: Dict[str, Any],
        guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a prompt for content refinement.
        
        Args:
            content: Content to refine
            quality_check: Quality check results
            consistency_check: Consistency check results
            guidelines: Refinement guidelines
            
        Returns:
            Prompt for content refinement
        """
        # Convert the data to string representations
        content_str = json.dumps(content, indent=2)
        quality_check_str = json.dumps(quality_check, indent=2)
        consistency_check_str = json.dumps(consistency_check, indent=2)
        guidelines_str = json.dumps(guidelines, indent=2)
        
        # Create the system message
        system_message = (
            "You are an educational content refinement specialist. "
            "Your task is to refine the provided content based on quality and consistency checks "
            "according to the specified guidelines. "
            "Maintain the original structure and format of the content while addressing the identified issues."
        )
        
        # Create the user message
        user_message = (
            f"Please refine the following content based on the quality and consistency checks "
            f"according to the provided guidelines.\n\n"
            f"CONTENT:\n{content_str}\n\n"
            f"QUALITY CHECK:\n{quality_check_str}\n\n"
            f"CONSISTENCY CHECK:\n{consistency_check_str}\n\n"
            f"GUIDELINES:\n{guidelines_str}\n\n"
            f"Respond with the refined content in the same JSON structure as the original content. "
            f"Make sure to preserve all keys and maintain the same overall structure."
        )
        
        # Return the prompt
        return {"system": system_message, "user": user_message}
    
    def _parse_refinement_response(self, response: str, original_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the response from content refinement.
        
        Args:
            response: Response from the model
            original_content: Original content before refinement
            
        Returns:
            Parsed refined content
        """
        try:
            logger.info("Parsing refinement response")
            
            # Clean up the response
            # Remove leading and trailing whitespace
            response = response.strip()
            
            # Check if the response is marked as JSON with backticks
            if "```json" in response:
                # Extract JSON between backticks
                start_marker = "```json"
                end_marker = "```"
                start_idx = response.find(start_marker) + len(start_marker)
                end_idx = response.find(end_marker, start_idx)
                if end_idx != -1:
                    json_str = response[start_idx:end_idx].strip()
                else:
                    # If no end marker, try to extract from start marker to end
                    json_str = response[start_idx:].strip()
            else:
                # Try to find JSON object markers
                json_start = response.find("{")
                if json_start == -1:
                    raise ValueError("No JSON object found in response")
                    
                # Find matching closing brace by counting opening and closing braces
                open_count = 0
                json_end = -1
                
                for i in range(json_start, len(response)):
                    if response[i] == '{':
                        open_count += 1
                    elif response[i] == '}':
                        open_count -= 1
                        if open_count == 0:
                            json_end = i + 1
                            break
                
                if json_end == -1:
                    json_end = response.rfind("}") + 1  # Fallback to the last closing brace
                
                json_str = response[json_start:json_end]
            
            # Log the extracted JSON string for debugging
            logger.debug(f"Extracted JSON string: {json_str}")
            
            try:
                # Try to parse the JSON
                refined_content = json.loads(json_str)
            except json.JSONDecodeError as json_error:
                logger.error(f"JSONDecodeError: {json_error}")
                logger.error(f"JSON string that failed to parse: {json_str}")
                
                # Try to repair common JSON issues
                # Replace single quotes with double quotes
                json_str = json_str.replace("'", '"')
                # Remove trailing commas before closing braces/brackets
                json_str = json_str.replace(",}", "}")
                json_str = json_str.replace(",]", "]")
                
                # Try parsing again
                try:
                    refined_content = json.loads(json_str)
                    logger.info("Successfully parsed JSON after repairs")
                except Exception as repair_error:
                    logger.error(f"Still failed to parse JSON after repairs: {repair_error}")
                    raise
            
            # Ensure the refined content has the same structure as the original
            for key in original_content:
                if key not in refined_content:
                    refined_content[key] = original_content[key]
            
            return refined_content
        except Exception as e:
            logger.error(f"Error parsing refinement response: {e}")
            logger.error(f"Original response: {response}")
            return original_content  # Return original content if parsing fails 