"""
Context Agent Module

This module provides the ContextAgent class that extracts course context from
course information documents (markdown or PDF files).
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.config import settings
from core.agents.document_loader.tools.document_analyzer import DocumentAnalyzer
from core.agents.course_context.course_context_extractor import CourseContextExtractor

# Configure logging
logger = logging.getLogger(__name__)


class ContextAgent(BaseAgent):
    """
    Agent for extracting course context from course information documents.
    
    This agent processes course information files (markdown or PDF) and extracts
    structured context including title, description, objectives, learning outcomes,
    and course structure.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Context Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize with settings
        if config is None:
            config = {}
        
        # Store course_info_dir from settings
        self.course_info_dir = settings.course_info_dir
        self.output_dir = settings.output_dir
        
        super().__init__(config)
    
    def _init_models(self):
        """Initialize AI models for context extraction."""
        # Models are initialized by the course_context_extractor
        pass
    
    def _init_memory(self):
        """Initialize memory for state tracking."""
        self.memory = {}
    
    def _init_orchestration(self):
        """Initialize orchestration components."""
        pass
    
    def _init_reasoning(self):
        """Initialize reasoning components."""
        pass
    
    def _init_tools(self):
        """Initialize tools for context extraction."""
        self.document_analyzer = DocumentAnalyzer()
        self.course_context_extractor = CourseContextExtractor()
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract course context from course information documents.
        
        Args:
            input_data: Input data dictionary (can contain course_info_path override)
            
        Returns:
            Dictionary containing extracted course context and metadata
        """
        logger.info("Extracting course context...")
        
        try:
            # Get course info path from input_data or use default from settings
            course_info_path = input_data.get("course_info_path", self.course_info_dir)
            course_info_path = Path(course_info_path)
            
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
            
            logger.info(f"Processing course info file: {course_file}")
            
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
            
            # Save the context
            context_output_dir = self.output_dir / "course_context"
            os.makedirs(context_output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            context_file = context_output_dir / f"course_context_{timestamp}.json"
            
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(course_context, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Course context extracted and saved to {context_file}")
            
            # Return the course context as the result
            return {
                "status": "success",
                "output_type": "course_context",
                "result": course_context,
                "context_file": str(context_file),
                "summary": f"Extracted course context from {course_file.name}"
            }
            
        except FileNotFoundError as e:
            logger.error(f"Course info file not found: {str(e)}")
            # Create a fallback context
            fallback_context = self._create_fallback_context(str(e), str(course_info_path))
            return {
                "status": "partial_success",
                "output_type": "course_context",
                "result": fallback_context,
                "summary": "Using fallback course context due to missing file",
                "warning": f"File not found: {str(e)}"
            }
            
        except Exception as e:
            logger.error(f"Error extracting course context: {str(e)}")
            # Create a fallback context
            fallback_context = self._create_fallback_context(str(e), str(course_info_path))
            return {
                "status": "partial_success",
                "output_type": "course_context",
                "result": fallback_context,
                "summary": "Using fallback course context due to extraction error",
                "warning": f"Extraction failed: {str(e)}"
            }
    
    def _create_fallback_context(self, error_message: str, document_source: str) -> Dict[str, Any]:
        """
        Create a fallback context when extraction fails.
        
        Args:
            error_message: The error message
            document_source: The source document path
            
        Returns:
            Fallback course context dictionary
        """
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
                "document_source": document_source,
                "extraction_status": "failed",
                "error_message": error_message,
                "completeness_score": 0.0
            }
        }
        
        # Save the fallback context
        context_output_dir = self.output_dir / "course_context"
        os.makedirs(context_output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_file = context_output_dir / f"course_context_fallback_{timestamp}.json"
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(fallback_context, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Fallback course context saved to {context_file}")
        
        return fallback_context
