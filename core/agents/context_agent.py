"""
Context Agent Module

This module provides the ContextAgent class that extracts course context from
course information documents. It inherits from BaseAgent and integrates with
the MaterialIngestionPipeline orchestrator.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from core.agents.base_agent import BaseAgent
from core.agents.document_loader.tools.document_analyzer import DocumentAnalyzer
from core.agents.course_context.course_context_extractor import CourseContextExtractor
from core.utils.data_manager import DataManager

# Configure logging
logger = logging.getLogger(__name__)


class ContextAgent(BaseAgent):
    """
    Agent responsible for extracting course context from course information documents.
    
    This agent processes course information files (PDF or Markdown) and extracts
    structured context including course objectives, structure, instructor information,
    prerequisites, and related resources.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the ContextAgent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary containing
                                              paths, model settings, and other parameters.
        """
        # Initialize the base agent
        super().__init__(config)
        
        logger.info(f"ContextAgent initialized with config: {list(config.keys()) if config else 'None'}")
    
    def _init_models(self):
        """Initialize the model component for course context extraction."""
        # Get model name from config
        model_name = self.config.get("course_context_model", "gpt-4o-mini")
        
        # Initialize the course context extractor
        self.course_context_extractor = CourseContextExtractor(model_name=model_name)
        
        logger.info(f"Initialized models with: {model_name}")
    
    def _init_memory(self):
        """Initialize the memory component for state tracking."""
        # Initialize the data manager for storing outputs
        base_data_dir = self.config.get("data_dir", "output/data")
        self.data_manager = DataManager({
            "base_data_dir": base_data_dir
        })
        
        # Create a unique run ID for this execution
        self.pipeline_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Initialized memory with data_dir: {base_data_dir}")
    
    def _init_orchestration(self):
        """Initialize the orchestration component for workflow management."""
        # Set up paths from config
        self.course_info_dir = Path(self.config.get("course_info_dir", "input/course_material/course_info"))
        self.output_dir = Path(self.config.get("course_context_dir", "output/course_context"))
        
        # Ensure directories exist
        self.course_info_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized orchestration with course_info_dir: {self.course_info_dir}")
    
    def _init_reasoning(self):
        """Initialize the reasoning component for decision making."""
        # For the context agent, reasoning is handled by the CourseContextExtractor
        # which uses AI models to extract and structure course information
        logger.info("Reasoning handled by CourseContextExtractor")
    
    def _init_tools(self):
        """Initialize tools for document analysis."""
        # Initialize document analyzer lazily (only when needed for PDF processing)
        # This avoids requiring OpenAI API key when processing markdown files
        self.document_analyzer = None
        
        logger.info("Tools will be initialized on demand")
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the course context extraction.
        
        Args:
            input_data (Dict[str, Any]): Input data containing course info path or directory
            
        Returns:
            Dict[str, Any]: Extracted course context with metadata
        """
        logger.info("Starting course context extraction...")
        
        try:
            # Get course info path from input data or use default
            course_info_path = input_data.get("course_info_path", self.course_info_dir)
            course_info_path = Path(course_info_path)
            
            # Extract the course context
            course_context = self._extract_course_context(course_info_path)
            
            # Save the context
            context_file = self._save_course_context(course_context)
            
            # Store in data manager
            self.data_manager.store_agent_output(
                "course_context",
                course_context,
                self.pipeline_run_id
            )
            
            # Prepare the output
            output = {
                "status": "success",
                "output_type": "course_context",
                "result": course_context,
                "output_file": str(context_file),
                "summary": f"Successfully extracted course context: {course_context.get('title', 'Unknown')}",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Course context extraction completed successfully. Output saved to {context_file}")
            
            return output
            
        except Exception as e:
            logger.error(f"Error during course context extraction: {str(e)}")
            # Create and save fallback context
            fallback_context = self._create_fallback_context(str(e), course_info_path)
            context_file = self._save_fallback_context(fallback_context)
            
            # Return a response with the fallback context
            return {
                "status": "warning",
                "output_type": "course_context",
                "result": fallback_context,
                "output_file": str(context_file),
                "summary": f"Used fallback context due to error: {str(e)[:100]}",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_course_context(self, course_info_path: Path) -> Dict[str, Any]:
        """
        Extract course context from the course information document.
        
        Args:
            course_info_path (Path): Path to the course info file or directory
            
        Returns:
            Dict[str, Any]: Extracted course context
        """
        logger.info(f"Extracting course context from {course_info_path}")
        
        # Check if the path is a directory or file
        if course_info_path.is_dir():
            # Find the first markdown or PDF file in the directory
            markdown_files = list(course_info_path.glob("*.md"))
            pdf_files = list(course_info_path.glob("*.pdf"))
            
            if markdown_files:
                logger.info(f"Found markdown file: {markdown_files[0]}")
                course_file = markdown_files[0]
                is_markdown = True
            elif pdf_files:
                logger.info(f"Found PDF file: {pdf_files[0]}")
                course_file = pdf_files[0]
                is_markdown = False
            else:
                raise FileNotFoundError(f"No markdown or PDF files found in {course_info_path}")
        else:
            course_file = course_info_path
            is_markdown = course_file.suffix.lower() == '.md'
        
        # Print the actual file path to help diagnose encoding issues
        logger.info(f"Full course info file path: {str(course_file)}")
        
        # Process the document based on its type
        if is_markdown:
            logger.info("Loading Markdown document...")
            with open(course_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # Create basic metadata for markdown
            basic_metadata = {
                "filename": course_file.name,
                "filetype": "markdown",
                "filesize": os.path.getsize(course_file),
                "created": datetime.fromtimestamp(os.path.getctime(course_file)).isoformat(),
                "modified": datetime.fromtimestamp(os.path.getmtime(course_file)).isoformat()
            }
        else:
            logger.info("Loading PDF document...")
            # Initialize document analyzer only when needed for PDF processing
            if self.document_analyzer is None:
                model_name = self.config.get("course_context_model", "gpt-4o-mini")
                self.document_analyzer = DocumentAnalyzer(model_name=model_name)
            
            pdf_document, basic_metadata = self.document_analyzer.load_pdf(str(course_file))
            
            logger.info("Extracting text from PDF...")
            text_content = self.document_analyzer.extract_text(pdf_document)
        
        logger.info(f"Extracted {len(text_content)} characters of text content")
        
        # Extract course context
        logger.info("Extracting course context from text...")
        course_context = self.course_context_extractor.extract_course_context(
            text_content,
            basic_metadata
        )
        
        return course_context
    
    def _save_course_context(self, course_context: Dict[str, Any]) -> Path:
        """
        Save the extracted course context to a file.
        
        Args:
            course_context (Dict[str, Any]): The extracted course context
            
        Returns:
            Path: Path to the saved context file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_file = self.output_dir / f"course_context_{timestamp}.json"
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(course_context, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Course context saved to {context_file}")
        
        return context_file
    
    def _create_fallback_context(self, error_message: str, course_info_path: Path) -> Dict[str, Any]:
        """
        Create a fallback course context when extraction fails.
        
        Args:
            error_message (str): The error message from the failed extraction
            course_info_path (Path): The path where course info was expected
            
        Returns:
            Dict[str, Any]: Fallback course context
        """
        logger.warning(f"Creating fallback context due to: {error_message}")
        
        fallback_context = {
            "title": "Unknown Course",
            "description": "Course context extraction failed",
            "objectives": ["Not available due to extraction failure"],
            "learning_outcomes": ["Not available due to extraction failure"],
            "subject_domain": "Unknown",
            "level": "Unknown",
            "structure": [
                {
                    "title": "Content unavailable",
                    "description": "Course structure could not be extracted",
                    "topics": []
                }
            ],
            "instructors": [
                {
                    "name": "",
                    "title": "",
                    "bio": "",
                    "contact": ""
                }
            ],
            "metadata": {
                "extraction_timestamp": datetime.now().isoformat(),
                "model_used": "fallback",
                "document_source": str(course_info_path),
                "extraction_status": "failed",
                "error_message": error_message,
                "completeness_score": 0.0
            }
        }
        
        return fallback_context
    
    def _save_fallback_context(self, fallback_context: Dict[str, Any]) -> Path:
        """
        Save the fallback course context to a file.
        
        Args:
            fallback_context (Dict[str, Any]): The fallback course context
            
        Returns:
            Path: Path to the saved fallback context file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_file = self.output_dir / f"course_context_fallback_{timestamp}.json"
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(fallback_context, f, ensure_ascii=False, indent=2)
        
        # Store the fallback context in the data manager
        self.data_manager.store_agent_output(
            "course_context",
            fallback_context,
            self.pipeline_run_id
        )
        
        logger.info(f"Fallback course context saved to {context_file}")
        
        return context_file
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for the agent.
        
        Args:
            input_data (Dict[str, Any]): Input data to validate
            
        Returns:
            bool: True if the input is valid, False otherwise
        """
        # Input is valid if it's a dictionary (path is optional and will use default)
        return input_data is not None and isinstance(input_data, dict)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        Validate the output data from the agent.
        
        Args:
            output_data (Dict[str, Any]): Output data to validate
            
        Returns:
            bool: True if the output is valid, False otherwise
        """
        # Output is valid if it contains status and result
        return (
            output_data is not None
            and isinstance(output_data, dict)
            and "status" in output_data
            and "result" in output_data
        )
