"""
Vision Agent Module

This module provides the VisionAgent class that analyzes images extracted
from slide PDFs using vision-capable AI models.

The agent processes images from the slide processing stage and provides
descriptions and analysis of visual content.
"""

import os
import logging
import base64
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from langchain_core.messages import HumanMessage

from core.agents.base_agent import BaseAgent
from core.config import settings
from core.utils.ai_models import AIModelFactory

# Configure logging
logger = logging.getLogger(__name__)

# Supported image extensions
SUPPORTED_IMAGE_EXTENSIONS = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']


class VisionAgent(BaseAgent):
    """
    Agent for analyzing images from slides using vision AI models.
    
    This agent receives image paths from the SlideAgent and uses
    vision-capable models (like GPT-4 Vision) to analyze and describe
    the visual content.
    
    The agent performs:
    - Extraction of image paths from slide processing results
    - Image analysis using vision-capable AI models
    - Generation of descriptions for each image
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Vision Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store output directory from settings
        self.output_dir = settings.output_dir / "vision_analysis"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for vision analysis."""
        # Get vision model name from config or use default
        vision_model_name = self.config.get("vision_model", settings.vision_model)
        
        # Create vision-capable model
        self.vision_model = AIModelFactory.create_model(
            model_name=vision_model_name,
            config={
                "temperature": self.config.get("temperature", settings.temperature)
            }
        )
        logger.info(f"Initialized vision model: {vision_model_name}")
    
    def _init_memory(self):
        """Initialize memory for state tracking."""
        self.memory = {
            "processed_images": [],
            "analysis_results": {}
        }
    
    def _init_orchestration(self):
        """Initialize orchestration components."""
        pass
    
    def _init_reasoning(self):
        """Initialize reasoning components."""
        pass
    
    def _init_tools(self):
        """Initialize tools for vision analysis."""
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for the vision agent.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if the input is valid, False otherwise
        """
        # Input must be a dictionary (checked by base class)
        if not super().validate_input(input_data):
            return False
        
        # Must have slide processing results
        if "result_from_process_slides" not in input_data:
            logger.error("Missing required key: result_from_process_slides")
            return False
        
        return True
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate the output data from the vision agent.
        
        Args:
            output_data: Output data to validate
            
        Returns:
            True if the output is valid, False otherwise
        """
        # Output must be a dictionary (checked by base class)
        if not super().validate_output(output_data):
            return False
        
        # Output must have required keys
        required_keys = ["status", "result", "summary"]
        return all(key in output_data for key in required_keys)
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode an image file to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
            raise
    
    def _get_image_mime_type(self, image_path: str) -> str:
        """
        Get the MIME type for an image based on its extension.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            MIME type string
        """
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def _analyze_image(self, image_path: str) -> str:
        """
        Analyze a single image using the vision model.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Description of the image
        """
        try:
            logger.info(f"Analyzing image: {image_path}")
            
            # Encode the image
            base64_image = self._encode_image(image_path)
            mime_type = self._get_image_mime_type(image_path)
            
            # Create the vision prompt
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": (
                            "Analyze this educational image from a course slide. "
                            "Describe what you see, including any diagrams, charts, formulas, "
                            "or text. Focus on the educational content and key concepts "
                            "being illustrated. Be concise but thorough."
                        )
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            )
            
            # Use the vision model to analyze
            response = self.vision_model.model.invoke([message])
            description = response.content
            
            logger.info(f"Successfully analyzed image: {Path(image_path).name}")
            return description
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {str(e)}")
            return f"Error analyzing image: {str(e)}"
    
    def _extract_images_from_slide_data(self, slide_result: Dict[str, Any]) -> List[str]:
        """
        Extract image paths from slide processing results.
        
        Args:
            slide_result: Slide processing results
            
        Returns:
            List of image file paths
        """
        images = []
        
        # Get the result dictionary from slide processing
        if "result" in slide_result:
            result = slide_result["result"]
            
            # Check if images_directory is specified
            if "images_directory" in result:
                images_dir = Path(result["images_directory"])
                
                # Get all image files from the directory
                if images_dir.exists():
                    for ext in SUPPORTED_IMAGE_EXTENSIONS:
                        images.extend([str(p) for p in images_dir.glob(ext)])
            
            # Also check for extracted_images in individual slide data
            for slide_info in result.get("slides", []):
                if "output_file" in slide_info:
                    # Load the processed slide data
                    try:
                        with open(slide_info["output_file"], 'r') as f:
                            slide_data = json.load(f)
                        
                        # Check for extracted images in metadata
                        extracted = slide_data.get("extraction_metadata", {}).get("extracted_images", [])
                        images.extend(extracted)
                    except Exception as e:
                        logger.warning(f"Error loading slide data from {slide_info['output_file']}: {str(e)}")
        
        # Remove duplicates and return
        return list(set(images))
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze images from slide processing results.
        
        Args:
            input_data: Input data dictionary containing:
                - result_from_process_slides: Slide processing results with image paths
                
        Returns:
            Dictionary containing image analysis results
        """
        logger.info("Starting vision analysis...")
        
        try:
            # Extract slide processing results
            slide_result = input_data["result_from_process_slides"]
            
            # Extract image paths
            image_paths = self._extract_images_from_slide_data(slide_result)
            
            if not image_paths:
                logger.warning("No images found in slide processing results")
                return {
                    "status": "success",
                    "result": {},
                    "summary": "No images found to analyze",
                    "image_count": 0
                }
            
            logger.info(f"Found {len(image_paths)} images to analyze")
            
            # Analyze each image
            analysis_results = {}
            successful_analyses = 0
            failed_analyses = 0
            
            for image_path in image_paths:
                if not Path(image_path).exists():
                    logger.warning(f"Image file not found: {image_path}")
                    failed_analyses += 1
                    continue
                
                try:
                    description = self._analyze_image(image_path)
                    analysis_results[image_path] = description
                    self.memory["processed_images"].append(image_path)
                    successful_analyses += 1
                except Exception as e:
                    logger.error(f"Failed to analyze {image_path}: {str(e)}")
                    analysis_results[image_path] = f"Analysis failed: {str(e)}"
                    failed_analyses += 1
            
            # Store results in memory
            self.memory["analysis_results"] = analysis_results
            
            # Save results to file
            output_file = self.output_dir / "vision_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "total_images": len(image_paths),
                    "successful_analyses": successful_analyses,
                    "failed_analyses": failed_analyses,
                    "analysis_results": analysis_results
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Vision analysis complete: {successful_analyses} successful, {failed_analyses} failed")
            logger.info(f"Results saved to {output_file}")
            
            return {
                "status": "success",
                "result": analysis_results,
                "summary": f"Analyzed {successful_analyses} images successfully ({failed_analyses} failed)",
                "output_file": str(output_file),
                "image_count": successful_analyses,
                "total_images": len(image_paths),
                "metadata": {
                    "successful_analyses": successful_analyses,
                    "failed_analyses": failed_analyses,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {str(e)}")
            return {
                "status": "error",
                "result": {},
                "summary": f"Vision analysis failed: {str(e)}",
                "error": str(e)
            }
