"""
Document Loader Agent Package

This package provides functionality for loading, analyzing, and extracting content from 
educational documents using AI-powered assistants for intelligent processing.

The Document Loader Agent is responsible for:
1. Discovering educational documents in specified directories
2. Classifying document types (textbooks, lecture notes, research papers, etc.)
3. Extracting content adaptively based on document structure
4. Extracting rich educational metadata
5. Processing and analyzing images within documents
6. Generating structured outputs for downstream processing
"""

from core.agents.document_loader.agent import DocumentLoaderAgent
from core.agents.document_loader.assistants import DocumentClassifierAssistant, AdaptiveExtractorAssistant, MetadataExtractorAssistant
from core.agents.document_loader.tools import DocumentAnalyzer

__all__ = [
    'DocumentLoaderAgent',
    'DocumentClassifierAssistant',
    'AdaptiveExtractorAssistant',
    'MetadataExtractorAssistant',
    'DocumentAnalyzer'
] 