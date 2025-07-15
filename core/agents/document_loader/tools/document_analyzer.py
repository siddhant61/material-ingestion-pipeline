"""
Document Analyzer Tool

This module provides tools for analyzing and processing educational documents,
leveraging AI assistants for document classification, content extraction,
and metadata extraction.
"""

import os
import fitz  # PyMuPDF
import logging
import json
import time
from typing import Dict, List, Any, Optional, Tuple, TypeVar, Callable, Type
from pathlib import Path
from functools import wraps

from core.agents.document_loader.assistants.document_classifier import DocumentClassifierAssistant
from core.agents.document_loader.assistants.adaptive_extractor import AdaptiveExtractorAssistant
from core.agents.document_loader.assistants.metadata_extractor import MetadataExtractorAssistant
from core.utils.error_handling import PDFReadError, ImageExtractionError

# Configure logging
logger = logging.getLogger(__name__)

# Define generic type for return value
T = TypeVar('T')

# Create a retry decorator that can be used with parameters
def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0, 
                       exponential_base: float = 2.0, retry_on: List[Type[Exception]] = None):
    """
    Decorator factory for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        exponential_base: Base for exponential backoff
        retry_on: List of exception types to retry on (defaults to all exceptions)
        
    Returns:
        A decorator function
    """
    if retry_on is None:
        retry_on = [Exception]
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for retry_count in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(retry_on) as e:
                    last_exception = e
                    
                    if retry_count == max_retries:
                        logger.warning(f"Failed after {max_retries} retries: {str(e)}")
                        raise last_exception
                    
                    sleep_time = delay * (exponential_base ** retry_count)
                    logger.info(f"Retrying in {sleep_time:.2f} seconds after error: {str(e)}")
                    time.sleep(sleep_time)
            
            # This should never happen, but just in case
            raise last_exception or Exception("Retry loop exited without raising or returning")
        
        return wrapper
    
    return decorator

class DocumentAnalyzer:
    """
    Tool for analyzing and processing educational documents.
    
    This tool combines multiple AI assistants to:
    1. Classify document types
    2. Extract content adaptively based on document structure
    3. Extract rich educational metadata
    4. Extract and analyze images
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        # Track processed documents to prevent duplication
        self.processed_documents = set()
        """
        Initialize the document analyzer with AI assistants.
        
        Args:
            model_name (str): The name of the LLM to use for assistants
        """
        self.model_name = model_name
        
        # Initialize assistants
        self.document_classifier = DocumentClassifierAssistant(model_name=model_name)
        self.adaptive_extractor = AdaptiveExtractorAssistant(model_name=model_name)
        self.metadata_extractor = MetadataExtractorAssistant(model_name=model_name)
        
        logger.info(f"Initialized DocumentAnalyzer with model {model_name}")
    
    @retry_with_backoff(max_retries=3)
    def load_pdf(self, pdf_path: str) -> Tuple[fitz.Document, Dict[str, Any]]:
        """
        Load a PDF document and extract basic metadata.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            Tuple[fitz.Document, Dict[str, Any]]: The PDF document and its metadata
        """
        try:
            # Open the PDF
            logger.info(f"Loading PDF: {pdf_path}")
            pdf_document = fitz.open(pdf_path)
            
            # Extract basic metadata
            metadata = {
                "filename": os.path.basename(pdf_path),
                "path": pdf_path,
                "page_count": len(pdf_document),
                "title": pdf_document.metadata.get("title", os.path.basename(pdf_path)),
                "author": pdf_document.metadata.get("author", "Unknown"),
                "creation_date": pdf_document.metadata.get("creationDate", "Unknown"),
                "modification_date": pdf_document.metadata.get("modDate", "Unknown"),
                "file_size": os.path.getsize(pdf_path)
            }
            
            logger.info(f"PDF loaded successfully: {pdf_path} ({metadata['page_count']} pages)")
            return pdf_document, metadata
            
        except Exception as e:
            error_msg = f"Error loading PDF {pdf_path}: {str(e)}"
            logger.error(error_msg)
            raise PDFReadError(error_msg)
    
    def extract_text(self, pdf_document: fitz.Document, page_range: Optional[Tuple[int, int]] = None) -> str:
        """
        Extract text from a PDF document.
        
        Args:
            pdf_document (fitz.Document): The PDF document
            page_range (Optional[Tuple[int, int]]): Range of pages to extract (start, end)
            
        Returns:
            str: Extracted text
        """
        try:
            # Determine page range
            start_page = page_range[0] if page_range else 0
            end_page = min(page_range[1], len(pdf_document) - 1) if page_range else len(pdf_document) - 1
            
            # Extract text from each page
            text = ""
            for page_num in range(start_page, end_page + 1):
                page = pdf_document[page_num]
                text += page.get_text()
                text += f"\n\n--- Page {page_num + 1} ---\n\n"
            
            logger.info(f"Extracted text from pages {start_page+1}-{end_page+1}")
            return text
            
        except Exception as e:
            error_msg = f"Error extracting text: {str(e)}"
            logger.error(error_msg)
            raise PDFReadError(error_msg)
    
    def extract_images(self, pdf_document: fitz.Document, output_dir: str, 
                      page_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """
        Extract images from a PDF document.
        
        Args:
            pdf_document (fitz.Document): The PDF document
            output_dir (str): Directory to save extracted images
            page_range (Optional[Tuple[int, int]]): Range of pages to extract images from
            
        Returns:
            List[Dict[str, Any]]: Information about extracted images
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine page range
            start_page = page_range[0] if page_range else 0
            end_page = min(page_range[1], len(pdf_document) - 1) if page_range else len(pdf_document) - 1
            
            # Extract images
            image_info = []
            image_count = 0
            
            for page_num in range(start_page, end_page + 1):
                page = pdf_document[page_num]
                
                # Get image list
                image_list = page.get_images(full=True)
                
                # Process each image
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Generate image filename
                    image_ext = base_image["ext"]
                    image_filename = f"image_p{page_num+1}_{img_index+1}.{image_ext}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    # Save the image
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # Record image information
                    image_info.append({
                        "filename": image_filename,
                        "path": image_path,
                        "page": page_num + 1,
                        "index": img_index + 1,
                        "width": base_image.get("width", 0),
                        "height": base_image.get("height", 0),
                        "size": len(image_bytes)
                    })
                    
                    image_count += 1
            
            logger.info(f"Extracted {image_count} images from pages {start_page+1}-{end_page+1}")
            return image_info
            
        except Exception as e:
            error_msg = f"Error extracting images: {str(e)}"
            logger.error(error_msg)
            raise ImageExtractionError(error_msg)
    
    def analyze_document(self, pdf_path: str, output_dir: str) -> Dict[str, Any]:
        # Check if document already processed
        document_hash = hash(os.path.basename(pdf_path))
        if document_hash in self.processed_documents:
            logger.info(f"Skipping already processed document: {pdf_path}")
            return {"status": "skipped", "reason": "already_processed"}
        
        # Mark document as processed
        self.processed_documents.add(document_hash)
        """
        Perform comprehensive analysis of a document using AI assistants.
        
        Args:
            pdf_path (str): Path to the PDF file
            output_dir (str): Directory to save extracted content
            
        Returns:
            Dict[str, Any]: Analysis results including classification, content, and metadata
        """
        logger.info(f"Starting comprehensive analysis of document: {pdf_path}")
        
        try:
            # Load the PDF
            pdf_document, basic_metadata = self.load_pdf(pdf_path)
            
            # Extract text for analysis
            text_content = self.extract_text(pdf_document)
            
            # Classify the document
            classification = self.document_classifier.classify_document(
                text_content, basic_metadata
            )
            
            # Create document info with classification results
            document_info = {
                **basic_metadata,
                "document_type": classification.get("document_type", "unknown"),
                "confidence": classification.get("confidence", 0.0),
                "extracted_metadata": classification.get("extracted_metadata", {})
            }
            
            # Create extraction plan based on document type and structure
            extraction_plan = self.adaptive_extractor.create_extraction_plan(
                document_info, text_content
            )
            
            # Extract images if needed
            image_info = []
            if extraction_plan.get("document_structure", {}).get("has_diagrams", False) or \
               extraction_plan.get("document_structure", {}).get("has_complex_layouts", False):
                image_output_dir = os.path.join(output_dir, "images")
                image_info = self.extract_images(pdf_document, image_output_dir)
            
            # Structure the content
            structured_content = self.adaptive_extractor.structure_content(
                document_info,
                extraction_plan.get("extraction_strategy", {}),
                text_content
            )
            
            # Extract educational metadata
            educational_metadata = self.metadata_extractor.extract_metadata(
                document_info, text_content
            )
            
            # Combine all analysis results
            analysis_results = {
                "document_info": document_info,
                "classification": classification,
                "extraction_plan": extraction_plan,
                "structured_content": structured_content,
                "educational_metadata": educational_metadata,
                "image_info": image_info
            }
            
            # Save analysis results
            results_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}_analysis.json")
            with open(results_path, "w") as f:
                json.dump(analysis_results, f, indent=2)
            
            logger.info(f"Completed analysis of document: {pdf_path}")
            return analysis_results
            
        except Exception as e:
            error_msg = f"Error analyzing document {pdf_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error_message": str(e),
                "error_type": type(e).__name__,
                "document_path": pdf_path
            } 