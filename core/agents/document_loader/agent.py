"""
Document Loader Agent

This module provides the DocumentLoaderAgent implementation, which is responsible for
loading, analyzing, and extracting content from educational documents using AI-powered
assistants for intelligent processing.
"""

import os
import sys
import json
import logging
from datetime import datetime
import glob
import uuid
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from core.agents.base_agent import BaseAgent
from core.agents.document_loader.tools.document_analyzer import DocumentAnalyzer
from core.utils.error_handling import PDFReadError, ImageExtractionError, retry_with_exponential_backoff
from core.utils.schema_validation import create_standard_header, validate_against_schema

# Configure logging
logger = logging.getLogger(__name__)

class DocumentLoaderAgent(BaseAgent):
    """
    Agent responsible for loading and analyzing educational documents.
    
    This agent uses AI-powered assistants to:
    1. Classify document types
    2. Extract content adaptively based on document structure
    3. Extract rich educational metadata
    4. Process and analyze images
    
    The agent follows the standardized architecture with separate components for:
    - Models (AI model interactions)
    - Memory (state tracking and persistence)
    - Orchestration (workflow management)
    - Reasoning (decision making)
    - Tools (document analysis and extraction)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Document Loader Agent.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary
        """
        # Initialize configuration
        self.config = config or {}
        
        # Set agent properties
        self.agent_id = str(uuid.uuid4())
        self.agent_name = self.__class__.__name__
        self.version = self.config.get("version", "1.0.0")
        self.created_at = datetime.now().isoformat()
        
        # Set directory paths
        self.input_dir = Path(self.config.get("input_dir", "input/course_material"))
        self.output_dir = Path(self.config.get("output_dir", "output/processed_documents"))
        self.data_dir = Path(self.config.get("data_dir", "data/document_loader"))
        
        # Ensure directories exist
        self.input_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize components
        self._init_models()
        self._init_memory()
        self._init_orchestration()
        self._init_reasoning()
        self._init_tools()
        
        logger.info(f"DocumentLoaderAgent initialized with input directory: {self.input_dir}")
    
    def _init_models(self):
        """Initialize the model component."""
        # Get model name from config, defaulting to gpt-4o-mini
        self.model_name = self.config.get("model_name", "gpt-4o-mini")
        logger.info(f"Using model: {self.model_name}")
    
    def _init_memory(self):
        """Initialize the memory component."""
        # Initialize memory for tracking processed documents
        self.memory = {
            "processed_documents": [],
            "failed_documents": [],
            "processing_stats": {
                "total_documents": 0,
                "successful": 0,
                "failed": 0,
                "total_pages": 0,
                "total_images": 0
            }
        }
        
        # Load previous memory if available
        memory_path = self.data_dir / "memory.json"
        if memory_path.exists():
            try:
                with open(memory_path, "r") as f:
                    self.memory = json.load(f)
                logger.info(f"Loaded memory with {len(self.memory['processed_documents'])} processed documents")
            except Exception as e:
                logger.warning(f"Failed to load memory: {e}")
    
    def _init_orchestration(self):
        """Initialize the orchestration component."""
        # Define the document processing workflow
        self.workflow = {
            "steps": [
                "discover_documents",
                "process_documents",
                "generate_summary"
            ],
            "current_step": None,
            "step_results": {}
        }
    
    def _init_reasoning(self):
        """Initialize the reasoning component."""
        # No specific reasoning component needed for this agent
        pass
    
    def _init_tools(self):
        """Initialize document processing tools."""
        # Initialize the document analyzer with the configured model
        self.document_analyzer = DocumentAnalyzer(model_name=self.model_name)
        logger.info("Document analysis tools initialized")
    
    def discover_documents(self, input_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover documents in the input directory.
        
        Args:
            input_dir (Optional[str]): Directory to search for documents
            
        Returns:
            List[Dict[str, Any]]: List of discovered documents
        """
        # Use provided input directory or default
        search_dir = Path(input_dir) if input_dir else self.input_dir
        
        # Find all PDF files
        pdf_files = []
        for pdf_path in glob.glob(str(search_dir / "**" / "*.pdf"), recursive=True):
            pdf_info = {
                "path": pdf_path,
                "filename": os.path.basename(pdf_path),
                "directory": os.path.dirname(pdf_path),
                "size": os.path.getsize(pdf_path),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(pdf_path)).isoformat()
            }
            pdf_files.append(pdf_info)
        
        logger.info(f"Discovered {len(pdf_files)} PDF documents in {search_dir}")
        return pdf_files
    
    def process_document(self, document_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single document.
        
        Args:
            document_info (Dict[str, Any]): Information about the document to process
            
        Returns:
            Dict[str, Any]: Processing results
        """
        pdf_path = document_info["path"]
        logger.info(f"Processing document: {pdf_path}")
        
        try:
            # Create output directory for this document
            document_name = os.path.splitext(os.path.basename(pdf_path))[0]
            document_output_dir = self.output_dir / document_name
            document_output_dir.mkdir(exist_ok=True, parents=True)
            
            # Analyze the document using the document analyzer
            analysis_results = self.document_analyzer.analyze_document(
                pdf_path, str(document_output_dir)
            )
            
            # Check for errors
            if analysis_results.get("status") == "error":
                logger.error(f"Error processing document {pdf_path}: {analysis_results.get('error_message')}")
                return {
                    "status": "error",
                    "document": document_info,
                    "error": analysis_results.get("error_message", "Unknown error"),
                    "error_type": analysis_results.get("error_type", "UnknownError")
                }
            
            # Update processing stats
            self.memory["processing_stats"]["successful"] += 1
            self.memory["processing_stats"]["total_pages"] += analysis_results.get("document_info", {}).get("page_count", 0)
            self.memory["processing_stats"]["total_images"] += len(analysis_results.get("image_info", []))
            
            # Add to processed documents
            self.memory["processed_documents"].append({
                "path": pdf_path,
                "filename": os.path.basename(pdf_path),
                "document_type": analysis_results.get("document_info", {}).get("document_type", "unknown"),
                "processed_at": datetime.now().isoformat(),
                "output_dir": str(document_output_dir)
            })
            
            # Save memory
            with open(self.data_dir / "memory.json", "w") as f:
                json.dump(self.memory, f, indent=2)
            
            # Return success result
            return {
                "status": "success",
                "document": document_info,
                "analysis_results": analysis_results,
                "output_dir": str(document_output_dir)
            }
            
        except Exception as e:
            logger.error(f"Error processing document {pdf_path}: {e}")
            
            # Update processing stats
            self.memory["processing_stats"]["failed"] += 1
            
            # Add to failed documents
            self.memory["failed_documents"].append({
                "path": pdf_path,
                "filename": os.path.basename(pdf_path),
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now().isoformat()
            })
            
            # Save memory
            with open(self.data_dir / "memory.json", "w") as f:
                json.dump(self.memory, f, indent=2)
            
            # Return error result
            return {
                "status": "error",
                "document": document_info,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process multiple documents.
        
        Args:
            documents (List[Dict[str, Any]]): List of documents to process
            
        Returns:
            Dict[str, Any]: Processing results
        """
        logger.info(f"Processing {len(documents)} documents")
        
        # Update processing stats
        self.memory["processing_stats"]["total_documents"] += len(documents)
        
        # Process each document
        results = []
        for document in documents:
            result = self.process_document(document)
            results.append(result)
        
        # Generate summary
        successful = sum(1 for r in results if r.get("status") == "success")
        failed = sum(1 for r in results if r.get("status") == "error")
        
        logger.info(f"Processed {len(documents)} documents: {successful} successful, {failed} failed")
        
        return {
            "status": "success",
            "total": len(documents),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of processed documents.
        
        Returns:
            Dict[str, Any]: Summary information
        """
        logger.info("Generating document processing summary")
        
        # Count document types
        document_types = {}
        for doc in self.memory["processed_documents"]:
            doc_type = doc.get("document_type", "unknown")
            document_types[doc_type] = document_types.get(doc_type, 0) + 1
        
        # Generate summary
        summary = {
            "total_documents": self.memory["processing_stats"]["total_documents"],
            "successful": self.memory["processing_stats"]["successful"],
            "failed": self.memory["processing_stats"]["failed"],
            "total_pages": self.memory["processing_stats"]["total_pages"],
            "total_images": self.memory["processing_stats"]["total_images"],
            "document_types": document_types,
            "processed_documents": self.memory["processed_documents"],
            "failed_documents": self.memory["failed_documents"]
        }
        
        # Save summary
        summary_path = self.output_dir / "processing_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Generated summary saved to {summary_path}")
        
        return summary
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the document loader agent.
        
        Args:
            input_data (Dict[str, Any]): Input data for the agent
            
        Returns:
            Dict[str, Any]: Output data from the agent
        """
        logger.info("Starting DocumentLoaderAgent execution")
        
        # Get input directory from input data or use default
        input_dir = input_data.get("input_dir", str(self.input_dir))
        
        # Execute workflow
        self.workflow["current_step"] = "discover_documents"
        documents = self.discover_documents(input_dir)
        self.workflow["step_results"]["discover_documents"] = {
            "count": len(documents)
        }
        
        self.workflow["current_step"] = "process_documents"
        processing_results = self.process_documents(documents)
        self.workflow["step_results"]["process_documents"] = {
            "successful": processing_results["successful"],
            "failed": processing_results["failed"]
        }
        
        self.workflow["current_step"] = "generate_summary"
        summary = self.generate_summary()
        self.workflow["step_results"]["generate_summary"] = {
            "total_documents": summary["total_documents"],
            "document_types": summary["document_types"]
        }
        
        self.workflow["current_step"] = None
        
        # Prepare output
        output = {
            "status": "success",
            "agent_info": create_standard_header(self.agent_name, self.version, self.agent_id),
            "output_type": "document_processing_results",
            "summary": summary,
            "processing_results": processing_results,
            "output_dir": str(self.output_dir)
        }
        
        logger.info("DocumentLoaderAgent execution completed")
        return output 