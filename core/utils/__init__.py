"""
Utilities Module

This module provides utility functions for the material ingestion pipeline.
"""

from core.utils.error_handling import (
    PipelineError, DocumentProcessingError, PDFReadError, 
    ImageExtractionError, OCRError, TranscriptProcessingError,
    ContextExtractionError, VectorStorageError, KnowledgeGraphError,
    ModelError, ModelTimeoutError, ModelRateLimitError,
    retry_with_exponential_backoff, format_error_for_output
)

from core.utils.schema_validation import (
    validate_against_schema, validate_and_log,
    create_standard_header, load_schema_from_file,
    AGENT_OUTPUT_SCHEMA_BASE
)

__all__ = [
    # Error handling
    "PipelineError", "DocumentProcessingError", "PDFReadError",
    "ImageExtractionError", "OCRError", "TranscriptProcessingError",
    "ContextExtractionError", "VectorStorageError", "KnowledgeGraphError",
    "ModelError", "ModelTimeoutError", "ModelRateLimitError",
    "retry_with_exponential_backoff", "format_error_for_output",
    
    # Schema validation
    "validate_against_schema", "validate_and_log",
    "create_standard_header", "load_schema_from_file",
    "AGENT_OUTPUT_SCHEMA_BASE"
] 