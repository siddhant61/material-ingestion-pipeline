"""
Adaptive Document Loader

This module provides a flexible document loading system that adapts to different document types,
formats, and uses context-aware processing to extract meaningful content.
"""

import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

class AdaptiveDocumentLoader:
    """
    A context-aware document loader that adapts to different document types and formats.
    
    Features:
    - Auto-detection of document types and formats
    - Content extraction tailored to document type
    - Structural analysis for better content parsing
    - Context-aware loading based on document purpose
    - Document validation and quality checks
    - Handles OCR for image-based documents
    """
    
    # Document type constants
    DOC_TYPE_PDF = "pdf"
    DOC_TYPE_DOCX = "docx"
    DOC_TYPE_TXT = "txt"
    DOC_TYPE_PPT = "ppt"
    DOC_TYPE_PPTX = "pptx"
    DOC_TYPE_HTML = "html"
    DOC_TYPE_IMAGE = "image"
    DOC_TYPE_UNKNOWN = "unknown"
    
    # Document category constants
    DOC_CATEGORY_COURSE_INFO = "course_info"
    DOC_CATEGORY_TRANSCRIPT = "transcript"
    DOC_CATEGORY_SLIDES = "slides"
    DOC_CATEGORY_SUPPLEMENTARY = "supplementary"
    DOC_CATEGORY_UNKNOWN = "unknown"
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the AdaptiveDocumentLoader.
        
        Args:
            config (Dict[str, Any], optional): Configuration options for the loader.
                Can include:
                - ocr_enabled: Whether to use OCR for image-based documents
                - max_file_size_mb: Maximum file size to process
                - extraction_quality: Extraction quality setting ('fast', 'balanced', 'high')
                - cache_enabled: Whether to cache extraction results
                - cache_dir: Directory to store cache files
        """
        self.config = config or {}
        
        # Set default configuration values
        self.ocr_enabled = self.config.get("ocr_enabled", True)
        self.max_file_size_mb = self.config.get("max_file_size_mb", 50)
        self.extraction_quality = self.config.get("extraction_quality", "balanced")
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.cache_dir = self.config.get("cache_dir", "output/cache/document_loader")
        
        # Initialize extractors dictionary - will be populated on demand
        self.extractors = {}
        
        # Create cache directory if needed
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
            
        logger.info(f"Initialized AdaptiveDocumentLoader with quality: {self.extraction_quality}, OCR: {self.ocr_enabled}")
    
    def load_document(self, file_path: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Load a document with context-aware processing.
        
        Args:
            file_path (str): Path to the document file
            context (Dict[str, Any], optional): Contextual information to guide processing
                Can include:
                - document_category: Type of document (course_info, transcript, slides)
                - course_context: Course context information
                - related_documents: Information about related documents
                - processing_purpose: Purpose of document processing
                
        Returns:
            Dict[str, Any]: Extracted document data with metadata
        """
        try:
            logger.info(f"Loading document: {file_path}")
            
            # Normalize path
            file_path = os.path.normpath(file_path)
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                logger.warning(f"File exceeds maximum size limit ({file_size_mb:.2f}MB > {self.max_file_size_mb}MB)")
                
            # Initialize context if not provided
            if context is None:
                context = {}
            
            # Generate document ID
            document_id = self._generate_document_id(file_path)
            
            # Check cache if enabled
            if self.cache_enabled and not context.get("force_reload", False):
                cached_data = self._get_from_cache(document_id, context)
                if cached_data:
                    logger.info(f"Using cached extraction for document: {file_path}")
                    return cached_data
            
            # Detect document type and category
            doc_type, doc_category = self._detect_document_properties(file_path, context)
            
            # Update context with detected properties
            context["detected_type"] = doc_type
            context["detected_category"] = doc_category
            
            # Load document content based on type
            content, raw_metadata = self._extract_document_content(file_path, doc_type, context)
            
            # Process content based on category
            processed_content = self._process_content_by_category(content, doc_category, context)
            
            # Prepare result with metadata
            result = {
                "document_id": document_id,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "document_type": doc_type,
                "document_category": doc_category,
                "content": processed_content,
                "metadata": {
                    **raw_metadata,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_quality": self.extraction_quality,
                    "ocr_used": self.ocr_enabled and doc_type in ["pdf", "image"],
                    "file_size_bytes": os.path.getsize(file_path),
                    "content_length": len(processed_content) if isinstance(processed_content, str) else "structured_data",
                    "context_aided": bool(context and len(context) > 0)
                }
            }
            
            # Add quality metrics
            result["quality_metrics"] = self._calculate_quality_metrics(processed_content, doc_type, doc_category)
            
            # Cache the result if enabled
            if self.cache_enabled:
                self._save_to_cache(document_id, result, context)
            
            logger.info(f"Successfully loaded document: {file_path} ({doc_type}, {doc_category})")
            return result
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return {
                "document_id": self._generate_document_id(file_path),
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "document_type": "unknown",
                "document_category": "unknown",
                "content": "",
                "metadata": {
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_error": str(e),
                    "extraction_status": "failed"
                },
                "quality_metrics": {
                    "extraction_success": False,
                    "quality_score": 0.0
                }
            }
    
    def _generate_document_id(self, file_path: str) -> str:
        """
        Generate a unique document ID based on file path and modification time.
        
        Args:
            file_path (str): Path to the document
            
        Returns:
            str: Unique document ID
        """
        try:
            file_path = os.path.normpath(file_path)
            file_stat = os.stat(file_path)
            unique_string = f"{file_path}:{file_stat.st_mtime}:{file_stat.st_size}"
            return hashlib.md5(unique_string.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Error generating document ID, falling back to filename hash: {str(e)}")
            return hashlib.md5(os.path.basename(file_path).encode()).hexdigest()
    
    def _detect_document_properties(self, file_path: str, context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Detect document type and category from file extension and context.
        
        Args:
            file_path (str): Path to the document
            context (Dict[str, Any]): Contextual information
            
        Returns:
            Tuple[str, str]: Document type and category
        """
        # Get file extension
        _, ext = os.path.splitext(file_path.lower())
        ext = ext.lstrip(".")
        
        # Detect document type based on extension
        doc_type = self.DOC_TYPE_UNKNOWN
        if ext in ["pdf"]:
            doc_type = self.DOC_TYPE_PDF
        elif ext in ["docx", "doc"]:
            doc_type = self.DOC_TYPE_DOCX
        elif ext in ["txt", "md", "csv"]:
            doc_type = self.DOC_TYPE_TXT
        elif ext in ["ppt"]:
            doc_type = self.DOC_TYPE_PPT
        elif ext in ["pptx"]:
            doc_type = self.DOC_TYPE_PPTX
        elif ext in ["html", "htm"]:
            doc_type = self.DOC_TYPE_HTML
        elif ext in ["jpg", "jpeg", "png", "tiff", "bmp"]:
            doc_type = self.DOC_TYPE_IMAGE
        
        # Detect document category
        # First check if category is explicitly provided in context
        doc_category = context.get("document_category", self.DOC_CATEGORY_UNKNOWN)
        
        # If category is unknown, try to infer from file path and name
        if doc_category == self.DOC_CATEGORY_UNKNOWN:
            file_path_lower = file_path.lower()
            file_name_lower = os.path.basename(file_path_lower)
            
            # Check for category indicators in path or filename
            if any(indicator in file_path_lower for indicator in ["transcript", "/transcripts/", "_transcript"]):
                doc_category = self.DOC_CATEGORY_TRANSCRIPT
            elif any(indicator in file_path_lower for indicator in ["slide", "/slides/", "presentation", "_slide"]):
                doc_category = self.DOC_CATEGORY_SLIDES
            elif any(indicator in file_path_lower for indicator in ["syllabus", "course_info", "course-info", "course_outline"]):
                doc_category = self.DOC_CATEGORY_COURSE_INFO
            elif any(indicator in file_path_lower for indicator in ["supplement", "additional", "resource", "reading"]):
                doc_category = self.DOC_CATEGORY_SUPPLEMENTARY
            
            # If still unknown, infer from document type
            if doc_category == self.DOC_CATEGORY_UNKNOWN:
                if doc_type in [self.DOC_TYPE_PPTX, self.DOC_TYPE_PPT]:
                    doc_category = self.DOC_CATEGORY_SLIDES
                elif doc_type == self.DOC_TYPE_PDF and "syllabus" in file_name_lower:
                    doc_category = self.DOC_CATEGORY_COURSE_INFO
        
        logger.info(f"Detected document properties: type={doc_type}, category={doc_category}")
        return doc_type, doc_category
    
    def _extract_document_content(self, file_path: str, doc_type: str, context: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """
        Extract content from document based on document type.
        
        Args:
            file_path (str): Path to the document
            doc_type (str): Type of document
            context (Dict[str, Any]): Contextual information
            
        Returns:
            Tuple[Any, Dict[str, Any]]: Extracted content and metadata
        """
        # Import extractors on demand to avoid unnecessary dependencies
        if doc_type == self.DOC_TYPE_PDF:
            if "pdf" not in self.extractors:
                self._init_pdf_extractor()
            return self.extractors["pdf"].extract(file_path, context)
            
        elif doc_type in [self.DOC_TYPE_DOCX, self.DOC_TYPE_DOC]:
            if "docx" not in self.extractors:
                self._init_docx_extractor()
            return self.extractors["docx"].extract(file_path, context)
            
        elif doc_type == self.DOC_TYPE_TXT:
            # Simple text extraction
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return content, {"line_count": len(content.splitlines())}
            
        elif doc_type in [self.DOC_TYPE_PPT, self.DOC_TYPE_PPTX]:
            if "ppt" not in self.extractors:
                self._init_ppt_extractor()
            return self.extractors["ppt"].extract(file_path, context)
            
        elif doc_type == self.DOC_TYPE_HTML:
            if "html" not in self.extractors:
                self._init_html_extractor()
            return self.extractors["html"].extract(file_path, context)
            
        elif doc_type == self.DOC_TYPE_IMAGE:
            if self.ocr_enabled:
                if "ocr" not in self.extractors:
                    self._init_ocr_extractor()
                return self.extractors["ocr"].extract(file_path, context)
            else:
                logger.warning(f"OCR is disabled, cannot extract content from image: {file_path}")
                return "", {"extraction_status": "skipped", "reason": "OCR disabled"}
            
        else:
            logger.warning(f"Unsupported document type: {doc_type}")
            return "", {"extraction_status": "unsupported", "document_type": doc_type}
    
    def _process_content_by_category(self, content: Any, doc_category: str, context: Dict[str, Any]) -> Any:
        """
        Process document content based on document category and context.
        
        Args:
            content (Any): Extracted document content
            doc_category (str): Document category
            context (Dict[str, Any]): Contextual information
            
        Returns:
            Any: Processed content
        """
        # Skip processing if content is empty
        if not content:
            return content
            
        if doc_category == self.DOC_CATEGORY_TRANSCRIPT:
            return self._process_transcript(content, context)
            
        elif doc_category == self.DOC_CATEGORY_SLIDES:
            return self._process_slides(content, context)
            
        elif doc_category == self.DOC_CATEGORY_COURSE_INFO:
            return self._process_course_info(content, context)
            
        elif doc_category == self.DOC_CATEGORY_SUPPLEMENTARY:
            return self._process_supplementary(content, context)
            
        else:
            # No special processing for unknown category
            return content
    
    def _process_transcript(self, content: Any, context: Dict[str, Any]) -> Any:
        """
        Process transcript content with context awareness.
        
        Args:
            content (Any): Transcript content
            context (Dict[str, Any]): Contextual information
            
        Returns:
            Any: Processed transcript content
        """
        # If content is already structured, return as is
        if not isinstance(content, str):
            return content
            
        try:
            # Check if we have course context available
            course_context = context.get("course_context", {})
            
            # Simple transcript structure detection and formatting
            lines = content.splitlines()
            result = []
            current_speaker = None
            current_segment = []
            
            # Process line by line
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Try to detect speaker changes
                # Common patterns: "Name:" or "[Name]" at the start of a line
                speaker_match = re.match(r'^([A-Za-z\s.]+):\s*(.*)$|^\[([A-Za-z\s.]+)\]\s*(.*)$', line)
                
                if speaker_match:
                    # Save previous segment if exists
                    if current_speaker and current_segment:
                        result.append({
                            "speaker": current_speaker,
                            "text": ' '.join(current_segment)
                        })
                    
                    # Start new segment
                    groups = speaker_match.groups()
                    current_speaker = groups[0] if groups[0] else groups[2]
                    text = groups[1] if groups[1] else groups[3]
                    current_segment = [text] if text else []
                else:
                    # Continue current segment
                    if current_speaker is None:
                        # If no speaker detected yet, try to infer from context
                        if course_context and "instructors" in course_context:
                            instructors = course_context.get("instructors", [])
                            if instructors and isinstance(instructors, list) and len(instructors) > 0:
                                current_speaker = instructors[0].get("name", "Unknown Speaker")
                            else:
                                current_speaker = "Unknown Speaker"
                        else:
                            current_speaker = "Unknown Speaker"
                    
                    current_segment.append(line)
            
            # Add the last segment
            if current_speaker and current_segment:
                result.append({
                    "speaker": current_speaker,
                    "text": ' '.join(current_segment)
                })
            
            # If we couldn't parse structure, return raw content
            if not result:
                return content
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
            return content
    
    def _process_slides(self, content: Any, context: Dict[str, Any]) -> Any:
        """
        Process slides content with context awareness.
        
        Args:
            content (Any): Slides content
            context (Dict[str, Any]): Contextual information
            
        Returns:
            Any: Processed slides content
        """
        # If content is already structured, return as is
        if not isinstance(content, str):
            return content
            
        try:
            # For simple text content, try to detect slide boundaries
            lines = content.splitlines()
            slides = []
            current_slide = None
            current_title = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Check for slide boundaries or titles 
                # Common patterns: numbered slides, "Slide X", etc.
                slide_boundary = re.match(r'^(Slide\s+\d+|#{1,3}\s+.*|SLIDE\s+\d+)$', line, re.IGNORECASE)
                
                if slide_boundary or len(line) < 50 and line.upper() == line:  # Potential slide title
                    # Save previous slide if exists
                    if current_title and current_content:
                        slides.append({
                            "title": current_title,
                            "content": '\n'.join(current_content)
                        })
                    
                    # Start new slide
                    current_title = line
                    current_content = []
                else:
                    # Add to current slide content
                    current_content.append(line)
            
            # Add the last slide
            if current_title and current_content:
                slides.append({
                    "title": current_title,
                    "content": '\n'.join(current_content)
                })
            
            # If no slides detected or very few slides, return raw content
            if len(slides) <= 1:
                return content
            
            return slides
            
        except Exception as e:
            logger.error(f"Error processing slides: {str(e)}")
            return content
    
    def _process_course_info(self, content: Any, context: Dict[str, Any]) -> Any:
        """
        Process course information content.
        
        Args:
            content (Any): Course information content
            context (Dict[str, Any]): Contextual information
            
        Returns:
            Any: Processed course information
        """
        # For course info, we usually return the raw content for specialized processors
        return content
    
    def _process_supplementary(self, content: Any, context: Dict[str, Any]) -> Any:
        """
        Process supplementary material content.
        
        Args:
            content (Any): Supplementary content
            context (Dict[str, Any]): Contextual information
            
        Returns:
            Any: Processed supplementary content
        """
        # No special processing for supplementary materials currently
        return content
    
    def _calculate_quality_metrics(self, content: Any, doc_type: str, doc_category: str) -> Dict[str, Any]:
        """
        Calculate quality metrics for extracted content.
        
        Args:
            content (Any): Extracted content
            doc_type (str): Document type
            doc_category (str): Document category
            
        Returns:
            Dict[str, Any]: Quality metrics
        """
        metrics = {
            "extraction_success": bool(content),
            "quality_score": 0.0,
            "issues": []
        }
        
        # Skip for empty content
        if not content:
            metrics["issues"].append("Empty content")
            return metrics
        
        # Text content analysis
        if isinstance(content, str):
            # Check content length
            content_length = len(content)
            if content_length < 100:
                metrics["issues"].append("Content too short")
                metrics["content_length"] = content_length
            
            # Check for common OCR issues
            ocr_errors = len(re.findall(r'[^\w\s.,:;?!()-]', content)) / max(1, content_length)
            if ocr_errors > 0.05:  # More than 5% non-standard characters
                metrics["issues"].append("Possible OCR errors")
                metrics["ocr_error_rate"] = ocr_errors
            
            # Check for reasonable text-to-length ratio
            word_count = len(re.findall(r'\b\w+\b', content))
            if word_count < 10 and content_length > 500:
                metrics["issues"].append("Low text-to-length ratio")
            
            # Estimate quality score
            if content_length > 1000 and word_count > 100 and ocr_errors < 0.02:
                metrics["quality_score"] = 0.9
            elif content_length > 500 and word_count > 50 and ocr_errors < 0.05:
                metrics["quality_score"] = 0.7
            elif content_length > 100:
                metrics["quality_score"] = 0.5
            else:
                metrics["quality_score"] = 0.3
                
            metrics["word_count"] = word_count
            
        # Structured content analysis
        else:
            # Check if we have expected structure for document type
            if doc_category == self.DOC_CATEGORY_TRANSCRIPT and isinstance(content, list):
                segment_count = len(content)
                if segment_count < 5:
                    metrics["issues"].append("Few transcript segments")
                else:
                    metrics["quality_score"] = min(0.9, 0.5 + segment_count / 100)
                metrics["segment_count"] = segment_count
                
            elif doc_category == self.DOC_CATEGORY_SLIDES and isinstance(content, list):
                slide_count = len(content)
                if slide_count < 3:
                    metrics["issues"].append("Few slides detected")
                else:
                    metrics["quality_score"] = min(0.9, 0.5 + slide_count / 50)
                metrics["slide_count"] = slide_count
                
            else:
                # Default for structured content
                metrics["quality_score"] = 0.7
        
        return metrics
    
    def _get_from_cache(self, document_id: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get document extraction from cache if available.
        
        Args:
            document_id (str): Document ID
            context (Dict[str, Any]): Current context
            
        Returns:
            Optional[Dict[str, Any]]: Cached extraction or None
        """
        if not self.cache_enabled:
            return None
            
        # Generate cache path
        cache_path = os.path.join(self.cache_dir, f"{document_id}.json")
        
        # Check if cache file exists
        if not os.path.exists(cache_path):
            return None
            
        try:
            # Load cached data
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            # Check if cache is valid given the current context
            if self._is_cache_valid(cached_data, context):
                logger.info(f"Valid cache found for document {document_id}")
                return cached_data
            else:
                logger.info(f"Cache found but invalid for document {document_id}")
                return None
                
        except Exception as e:
            logger.warning(f"Error reading cache: {str(e)}")
            return None
    
    def _save_to_cache(self, document_id: str, data: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Save extraction results to cache.
        
        Args:
            document_id (str): Document ID
            data (Dict[str, Any]): Extraction data
            context (Dict[str, Any]): Current context
            
        Returns:
            bool: Success status
        """
        if not self.cache_enabled:
            return False
            
        # Generate cache path
        cache_path = os.path.join(self.cache_dir, f"{document_id}.json")
        
        try:
            # Add cache metadata
            cache_data = data.copy()
            cache_data["cache_metadata"] = {
                "cached_at": datetime.now().isoformat(),
                "context_hash": hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest(),
                "extraction_config": {
                    "ocr_enabled": self.ocr_enabled,
                    "extraction_quality": self.extraction_quality
                }
            }
            
            # Save to cache file
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Saved extraction to cache: {cache_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")
            return False
    
    def _is_cache_valid(self, cached_data: Dict[str, Any], current_context: Dict[str, Any]) -> bool:
        """
        Check if cached data is valid for current context.
        
        Args:
            cached_data (Dict[str, Any]): Cached extraction data
            current_context (Dict[str, Any]): Current context
            
        Returns:
            bool: Whether cache is valid
        """
        # Extract cache metadata
        cache_metadata = cached_data.get("cache_metadata", {})
        
        # Check extraction configuration
        extraction_config = cache_metadata.get("extraction_config", {})
        if extraction_config.get("ocr_enabled") != self.ocr_enabled:
            return False
        if extraction_config.get("extraction_quality") != self.extraction_quality:
            return False
            
        # Check context compatibility
        # For now, just check if we had course context before and now
        had_course_context = "context_hash" in cache_metadata
        need_course_context = "course_context" in current_context
        
        # If we need context now but didn't have it before, cache is invalid
        if need_course_context and not had_course_context:
            return False
            
        # Otherwise, cache is valid
        return True
    
    def _init_pdf_extractor(self):
        """Initialize PDF extractor on first use."""
        try:
            from core.extractors.pdf_extractor import PDFExtractor
            self.extractors["pdf"] = PDFExtractor(self.ocr_enabled, self.extraction_quality)
            logger.info("Initialized PDF extractor")
        except ImportError as e:
            logger.warning(f"Could not initialize PDF extractor: {str(e)}")
            # Fallback to basic text extraction
            self.extractors["pdf"] = self._create_fallback_extractor("pdf")
    
    def _init_docx_extractor(self):
        """Initialize DOCX extractor on first use."""
        try:
            from core.extractors.docx_extractor import DOCXExtractor
            self.extractors["docx"] = DOCXExtractor()
            logger.info("Initialized DOCX extractor")
        except ImportError as e:
            logger.warning(f"Could not initialize DOCX extractor: {str(e)}")
            # Fallback to basic text extraction
            self.extractors["docx"] = self._create_fallback_extractor("docx")
    
    def _init_ppt_extractor(self):
        """Initialize PowerPoint extractor on first use."""
        try:
            from core.extractors.ppt_extractor import PPTExtractor
            self.extractors["ppt"] = PPTExtractor()
            logger.info("Initialized PowerPoint extractor")
        except ImportError as e:
            logger.warning(f"Could not initialize PowerPoint extractor: {str(e)}")
            # Fallback to basic text extraction
            self.extractors["ppt"] = self._create_fallback_extractor("ppt")
    
    def _init_html_extractor(self):
        """Initialize HTML extractor on first use."""
        try:
            from core.extractors.html_extractor import HTMLExtractor
            self.extractors["html"] = HTMLExtractor()
            logger.info("Initialized HTML extractor")
        except ImportError as e:
            logger.warning(f"Could not initialize HTML extractor: {str(e)}")
            # Fallback to basic text extraction
            self.extractors["html"] = self._create_fallback_extractor("html")
    
    def _init_ocr_extractor(self):
        """Initialize OCR extractor on first use."""
        try:
            from core.extractors.ocr_extractor import OCRExtractor
            self.extractors["ocr"] = OCRExtractor()
            logger.info("Initialized OCR extractor")
        except ImportError as e:
            logger.warning(f"Could not initialize OCR extractor: {str(e)}")
            # Fallback to empty extractor
            class EmptyExtractor:
                def extract(self, file_path, context):
                    return "", {"error": "OCR not available"}
            self.extractors["ocr"] = EmptyExtractor()
    
    def _create_fallback_extractor(self, doc_type: str):
        """
        Create a fallback extractor for a document type.
        
        Args:
            doc_type (str): Document type
            
        Returns:
            object: A simple extractor object with extract method
        """
        class FallbackExtractor:
            def __init__(self, doc_type):
                self.doc_type = doc_type
                
            def extract(self, file_path, context):
                logger.warning(f"Using fallback extractor for {self.doc_type}")
                
                try:
                    # Try basic text extraction
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    return content, {
                        "extraction_method": "fallback",
                        "line_count": len(content.splitlines())
                    }
                except Exception as e:
                    logger.error(f"Fallback extraction failed: {str(e)}")
                    return "", {"error": str(e)}
                    
        return FallbackExtractor(doc_type)
    
    def clear_cache(self, document_id: Optional[str] = None) -> int:
        """
        Clear extraction cache.
        
        Args:
            document_id (Optional[str]): Specific document ID to clear, or None for all
            
        Returns:
            int: Number of cache entries cleared
        """
        if not self.cache_enabled:
            return 0
            
        try:
            count = 0
            if document_id:
                # Clear specific document cache
                cache_path = os.path.join(self.cache_dir, f"{document_id}.json")
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    count = 1
            else:
                # Clear all cache
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.cache_dir, filename))
                        count += 1
                        
            logger.info(f"Cleared {count} cache entries")
            return count
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0 