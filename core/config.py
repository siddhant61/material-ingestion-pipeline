"""
Configuration Module

This module provides centralized configuration management for the Material Ingestion Pipeline.
All hardcoded paths, model settings, and parameters are externalized through this module.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Centralized configuration settings for the Material Ingestion Pipeline.
    
    All configuration values can be overridden via environment variables.
    """
    
    def __init__(self):
        """Initialize settings from environment variables with sensible defaults."""
        
        # Base directories
        self.project_root = Path(__file__).parent.parent.absolute()
        self.input_dir = Path(os.getenv("INPUT_DIR", str(self.project_root / "input")))
        self.output_dir = Path(os.getenv("OUTPUT_DIR", str(self.project_root / "output")))
        self.data_dir = Path(os.getenv("DATA_DIR", str(self.output_dir / "data")))
        
        # Course material directories
        self.course_info_dir = self.input_dir / "course_material" / "course_info"
        self.transcripts_dir = self.input_dir / "course_material" / "transcripts"
        self.slides_dir = self.input_dir / "course_material" / "slides"
        
        # Output directories
        self.course_context_dir = self.output_dir / "course_context"
        self.transcripts_output_dir = self.output_dir / "transcripts"
        self.slides_output_dir = self.output_dir / "slides"
        self.knowledge_graph_dir = self.output_dir / "knowledge_graph"
        
        # AI Model settings
        self.default_model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        self.course_context_model = os.getenv("COURSE_CONTEXT_MODEL", self.default_model)
        self.transcript_model = os.getenv("TRANSCRIPT_MODEL", self.default_model)
        self.slide_model = os.getenv("SLIDE_MODEL", self.default_model)
        
        # OpenAI API settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Model parameters
        self.temperature = float(os.getenv("MODEL_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("MODEL_MAX_TOKENS", "4000"))
        
        # Pipeline settings
        self.pipeline_version = os.getenv("PIPELINE_VERSION", "1.0.0")
        
        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Create necessary directories
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist."""
        directories = [
            self.input_dir,
            self.output_dir,
            self.data_dir,
            self.course_info_dir,
            self.transcripts_dir,
            self.slides_dir,
            self.course_context_dir,
            self.transcripts_output_dir,
            self.slides_output_dir,
            self.knowledge_graph_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self):
        """Convert settings to a dictionary for passing to agents."""
        return {
            "project_root": str(self.project_root),
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "data_dir": str(self.data_dir),
            "course_info_dir": str(self.course_info_dir),
            "transcripts_dir": str(self.transcripts_dir),
            "slides_dir": str(self.slides_dir),
            "course_context_dir": str(self.course_context_dir),
            "transcripts_output_dir": str(self.transcripts_output_dir),
            "slides_output_dir": str(self.slides_output_dir),
            "knowledge_graph_dir": str(self.knowledge_graph_dir),
            "default_model": self.default_model,
            "course_context_model": self.course_context_model,
            "transcript_model": self.transcript_model,
            "slide_model": self.slide_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "pipeline_version": self.pipeline_version,
            "log_level": self.log_level,
        }


# Create a global settings instance
settings = Settings()
