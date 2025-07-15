"""
Document Loader Assistants

This module provides AI-powered assistants for the Document Loader agent,
supporting document classification, adaptive extraction, and metadata extraction.
"""

from core.agents.document_loader.assistants.document_classifier import DocumentClassifierAssistant
from core.agents.document_loader.assistants.adaptive_extractor import AdaptiveExtractorAssistant
from core.agents.document_loader.assistants.metadata_extractor import MetadataExtractorAssistant

__all__ = ["DocumentClassifierAssistant","AdaptiveExtractorAssistant","MetadataExtractorAssistant"
] 