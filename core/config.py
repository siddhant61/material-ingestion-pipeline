"""
Configuration Module

This module provides centralized configuration management for the Material Ingestion Pipeline.
All configuration values are externalized using environment variables and Pydantic Settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration class for the Material Ingestion Pipeline.
    
    All settings can be overridden via environment variables.
    Environment variables should be prefixed with the setting name in uppercase.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for AI model access"
    )
    
    # AI Model Settings
    ai_model_name: str = Field(
        default="gpt-3.5-turbo",
        description="Primary AI model to use for processing"
    )
    
    ai_model_temperature: float = Field(
        default=0.2,
        description="Temperature setting for AI model responses (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    ai_fallback_model: str = Field(
        default="gpt-3.5-turbo",
        description="Fallback AI model if primary model fails"
    )
    
    # Directory Paths
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.absolute(),
        description="Base directory of the project"
    )
    
    input_dir: Optional[Path] = Field(
        default=None,
        description="Input directory for course materials"
    )
    
    output_dir: Optional[Path] = Field(
        default=None,
        description="Output directory for processed data"
    )
    
    course_info_dir: Optional[Path] = Field(
        default=None,
        description="Directory containing course information documents"
    )
    
    transcripts_dir: Optional[Path] = Field(
        default=None,
        description="Directory containing transcript files"
    )
    
    slides_dir: Optional[Path] = Field(
        default=None,
        description="Directory containing slide files"
    )
    
    # Data Manager Settings
    data_base_dir: str = Field(
        default="output/data",
        description="Base directory for data manager storage"
    )
    
    def __init__(self, **kwargs):
        """Initialize settings and resolve default paths."""
        super().__init__(**kwargs)
        
        # Set default paths if not provided
        if self.input_dir is None:
            self.input_dir = self.base_dir / "input"
        
        if self.output_dir is None:
            self.output_dir = self.base_dir / "output"
        
        if self.course_info_dir is None:
            self.course_info_dir = self.input_dir / "course_material" / "course_info"
        
        if self.transcripts_dir is None:
            self.transcripts_dir = self.input_dir / "course_material" / "transcripts"
        
        if self.slides_dir is None:
            self.slides_dir = self.input_dir / "course_material" / "slides"
    
    def ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        directories = [
            self.input_dir,
            self.output_dir,
            self.course_info_dir,
            self.transcripts_dir,
            self.slides_dir
        ]
        
        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)
    
    def get_ai_model_config(self) -> dict:
        """
        Get AI model configuration as a dictionary.
        
        Returns:
            dict: Configuration dictionary for AI model creation
        """
        return {
            "model_name": self.ai_model_name,
            "temperature": self.ai_model_temperature,
            "fallback_model": self.ai_fallback_model
        }


# Create a global settings instance
settings = Settings()
