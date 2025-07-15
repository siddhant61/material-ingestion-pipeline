"""
Metadata Extraction Assistant

This module provides an AI-powered assistant for extracting rich metadata from
educational documents, including educational context, topics, learning objectives,
and relationships to other materials.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.assistants.base_assistant import BaseAssistant

# Configure logging
logger = logging.getLogger(__name__)

class MetadataExtractorAssistant(BaseAssistant):
    """
    Assistant for extracting rich metadata from educational documents.
    
    This assistant analyzes document content to extract educational metadata,
    including:
    - Educational level and prerequisites
    - Learning objectives and outcomes
    - Key topics and concepts
    - Context within a course or curriculum
    - Relationships to other educational materials
    """
    
    def _init_prompts(self):
        """Initialize prompt templates for metadata extraction."""
        
        # System prompt for educational metadata extraction
        self.metadata_system_prompt = """
        You are an expert in educational content analysis and metadata extraction.
        
        You will be given excerpts from an educational document along with basic information.
        Your task is to extract rich educational metadata, including:
        1. Educational level (K-12, undergraduate, graduate, professional)
        2. Learning objectives and outcomes
        3. Prerequisites and assumed knowledge
        4. Key topics and concepts covered
        5. Educational context (course, module, curriculum placement)
        6. Relationships to other educational materials
        
        FORMAT YOUR RESPONSE AS A JSON OBJECT with the following structure:
        {"educational_metadata": {"educational_level": "level of education this is intended for","discipline": "primary academic discipline","subdisciplines": ["list","of","relevant","subdisciplines"],"prerequisites": ["list","of","prerequisites"],"learning_objectives": ["list","of","learning","objectives"],"estimated_study_time": "estimated time to complete/study this material","difficulty_level": "beginner|intermediate|advanced|expert"
            },"content_metadata": {"key_topics": ["list","of","main","topics"],"key_concepts": ["list","of","key","concepts"],"key_terms": {
                    "term1": "definition or explanation",
                    "term2": "definition or explanation"
                }
            },"contextual_metadata": {"course_context": "how this fits into a larger course","curriculum_placement": "where this belongs in curriculum","related_materials": ["list","of","related","materials"]
            },"confidence_scores": {"overall_confidence": float between 0-1,"educational_level_confidence": float between 0-1,"topic_confidence": float between 0-1
            },"reasoning": "explanation of your metadata extraction decisions"
        }
        
        Focus on extracting accurate educational context that would be useful for
        knowledge graph construction and educational pathways.
        """
        
        # Prompt template for metadata extraction
        self.metadata_prompt = ChatPromptTemplate.from_messages([
            ("system", self.metadata_system_prompt),
            ("human", """DOCUMENT INFORMATION:
Type: {{document_type}}
Title: {{title}}
Author: {{author}}

DOCUMENT CONTENT:
{{content}}

Please extract rich educational metadata from this document.""")
        ])
        
        # Initialize the parser
        self.metadata_parser = JsonOutputParser()
        
        # Build the metadata extraction chain
        self.metadata_chain = self.build_chain_of_thought_chain(
            self.metadata_prompt,
            self.metadata_parser
        )
        
        logger.info("Initialized metadata extraction prompts and chains")
    
    def extract_metadata(self, document_info: Dict[str, Any], content: str) -> Dict[str, Any]:
        """
        Extract rich educational metadata from a document.
        
        Args:
            document_info (Dict[str, Any]): Basic information about the document
            content (str): The document content to analyze
            
        Returns:
            Dict[str, Any]: Extracted educational metadata
        """
        logger.info(f"Extracting metadata from document: {document_info.get('title', 'untitled')}")
        
        # Prepare content sample (first 4000 characters for metadata extraction)
        content_sample = content[:4000] + "..." if len(content) > 4000 else content
        
        # Prepare input for metadata extraction
        input_data = {"document_type": document_info.get("document_type","unknown"),"title": document_info.get("title","untitled"),"author": document_info.get("author","unknown"),"content": content_sample
        }
        
        # Run the metadata extraction chain with error handling
        try:
            result = self.run_with_error_handling(self.metadata_chain, input_data)
            
            if result.get("status") =="success":
                metadata = result["result"]
                logger.info(f"Extracted metadata with {len(metadata.get('content_metadata', {}).get('key_topics', []))} key topics")
                return metadata
            else:
                logger.error(f"Error extracting metadata: {result.get('error_message')}")
                return {"educational_metadata": {"educational_level":"unknown","discipline":"unknown","subdisciplines": [],"prerequisites": [],"learning_objectives": [],"estimated_study_time":"unknown","difficulty_level":"unknown"
                    },"content_metadata": {"key_topics": [],"key_concepts": [],"content_type":"unknown","pedagogical_approach":"unknown"
                    },"course_metadata": {"course_name": document_info.get("title","untitled"),"course_code":"unknown","institution":"unknown","instructor": document_info.get("author","unknown"),"term":"unknown"
                    },"reasoning": "Error extracting metadata, using fallback values","error": result.get("error_message", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Exception in metadata extraction: {str(e)}")
            return {"educational_metadata": {"educational_level":"unknown","discipline":"unknown","subdisciplines": [],"prerequisites": [],"learning_objectives": [],"estimated_study_time":"unknown","difficulty_level":"unknown"
                },"content_metadata": {"key_topics": [],"key_concepts": [],"content_type":"unknown","pedagogical_approach":"unknown"
                },"course_metadata": {"course_name": document_info.get("title","untitled"),"course_code":"unknown","institution":"unknown","instructor": document_info.get("author","unknown"),"term":"unknown"
                },"reasoning": "Exception in metadata extraction, using fallback values","error": str(e)
            } 