"""
Error Handling Utilities

This module provides standardized error handling utilities for the material ingestion pipeline,
including custom exception classes, error formatting, and retry mechanisms.
"""

import time
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T')

# Base exception class
class PipelineError(Exception):
    """Base exception class for all pipeline errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

# Document processing errors
class DocumentProcessingError(PipelineError):
    """Error raised during document processing."""
    pass

class PDFReadError(DocumentProcessingError):
    """Error raised when reading a PDF document fails."""
    pass

class ImageExtractionError(DocumentProcessingError):
    """Error raised when extracting images from a document fails."""
    pass

class OCRError(DocumentProcessingError):
    """Error raised when OCR processing fails."""
    pass

# Transcript processing errors
class TranscriptProcessingError(PipelineError):
    """Error raised during transcript processing."""
    pass

# Context extraction errors
class ContextExtractionError(PipelineError):
    """Error raised during context extraction."""
    pass

# Vector storage errors
class VectorStorageError(PipelineError):
    """Error raised during vector storage operations."""
    pass

# Knowledge graph errors
class KnowledgeGraphError(PipelineError):
    """Error raised during knowledge graph operations."""
    pass

# Model errors
class ModelError(PipelineError):
    """Error raised during model operations."""
    pass

class ModelTimeoutError(ModelError):
    """Error raised when a model operation times out."""
    pass

class ModelRateLimitError(ModelError):
    """Error raised when a model operation hits a rate limit."""
    pass

# Function for retrying operations with exponential backoff
def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 5,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    retry_on: List[Type[Exception]] = None,
    logger_name: Optional[str] = None
) -> Callable[..., T]:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        func: The function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        exponential_base: Base for exponential backoff
        retry_on: List of exception types to retry on (defaults to all exceptions)
        logger_name: Name of the logger to use
    
    Returns:
        A wrapper function that implements retry logic
    """
    retry_logger = logging.getLogger(logger_name or __name__)
    
    def wrapper(*args, **kwargs):
        delay = initial_delay
        last_exception = None
        
        for retry_count in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if we should retry on this exception type
                if retry_on and not any(isinstance(e, exc_type) for exc_type in retry_on):
                    raise e
                
                # If we've reached the maximum retries, raise the last exception
                if retry_count >= max_retries:
                    retry_logger.error(
                        f"Max retries ({max_retries}) reached for {func.__name__}. "
                        f"Final exception: {str(e)}"
                    )
                    raise e
                
                # Calculate next retry delay
                wait = delay * (exponential_base ** retry_count)
                
                retry_logger.warning(
                    f"Retry {retry_count + 1}/{max_retries} for {func.__name__} "
                    f"after {wait:.2f}s due to: {str(e)}"
                )
                
                # Wait before retrying
                time.sleep(wait)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        
        # This should also never be reached
        raise RuntimeError(f"Unexpected error in retry logic for {func.__name__}")
    
    return wrapper

def format_error_for_output(error: Exception) -> Dict[str, Any]:
    """
    Format an exception for structured output.
    
    Args:
        error: The exception to format
    
    Returns:
        A dictionary with formatted error information
    """
    error_details = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc()
    }
    
    # Add additional details for PipelineError types
    if isinstance(error, PipelineError) and hasattr(error, 'details'):
        error_details["details"] = error.details
    
    return error_details 