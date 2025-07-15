"""
Adaptive Extraction Assistant

This module provides an AI-powered assistant for adaptively extracting content from
educational documents based on their type and structure, using a chain-of-thought
approach to make extraction decisions.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.assistants.base_assistant import BaseAssistant

# Configure logging
logger = logging.getLogger(__name__)

class AdaptiveExtractorAssistant(BaseAssistant):
    """
    Assistant for adaptively extracting content from educational documents.
    
    This assistant analyzes document structure and content to make intelligent
    decisions about extraction strategies, including:
    - Identifying key sections to extract
    - Determining how to handle tables, diagrams, and complex layouts
    - Extracting structured metadata
    - Organizing content hierarchically
    """
    
    def _init_prompts(self):
        """Initialize prompt templates for the adaptive extractor."""
        
        # System prompt for extraction planning
        self.extraction_planning_system_prompt = """
        You are an expert document structure analyzer specializing in educational materials.
        
        You will be given information about a document including its type and sample content.
        Your task is to:
        1. Analyze the document structure
        2. Determine the best extraction strategy
        3. Identify key sections, their relationships, and importance
        4. Propose a structured extraction plan
        
        FORMAT YOUR RESPONSE AS A JSON OBJECT with the following structure:
        {"document_structure": {"sections": ["list","of","main","sections"],"hierarchy_depth": int (estimated depth of hierarchical structure),"has_complex_layouts": bool,"has_tables": bool,"has_diagrams": bool,"has_mathematical_notation": bool
            },"extraction_strategy": {"approach": "text_flow | structural | hybrid","section_handling": "how sections should be identified and extracted","table_handling": "how tables should be processed","image_regions": ["list","of","regions","to","extract","as","images"],"special_considerations": ["list","of","special","cases","to","handle"]
            },"extraction_plan": [
                {"step": 1,"description": "description of extraction step","target": "what to extract in this step","method": "how to extract it"
                },
                ... additional steps ...
            ],"reasoning": "explanation of your analysis and extraction plan"
        }
        
        Be detailed in your analysis but focus on practical extraction strategies
        that would lead to effectively structured educational content.
        """
        
        # Prompt template for extraction planning
        self.extraction_planning_prompt = ChatPromptTemplate.from_messages([
            ("system", self.extraction_planning_system_prompt),
            ("human", """DOCUMENT INFORMATION:
Type: {{document_type}}
Title: {{title}}
Page Count: {{page_count}}

DOCUMENT STRUCTURE SAMPLE:
{{content}}

Based on this information, analyze the document structure and create an extraction plan.""")
        ])
        
        # Prompt for content structuring
        self.content_structuring_system_prompt = """
        You are an expert in educational content structuring.
        
        You will be given extracted content from a document and must structure it
        according to educational principles. Your task is to:
        1. Organize the content hierarchically
        2. Identify main topics and subtopics
        3. Extract key concepts and their relationships
        4. Highlight important educational content
        
        FORMAT YOUR RESPONSE AS A JSON OBJECT with the following hierarchical structure:
        {"title": "document title","document_type": "document type","educational_level": "estimated educational level","content": [
                {"section_type": "heading|paragraph|list|table|image_reference|etc","content": "section content","level": int (hierarchical level),"children": [
                        ... similar structure for child sections ...
                    ],"key_concepts": ["list","of","key","concepts"],"educational_role": "what role this section plays (definition, example, explanation, etc)"
                },
                ... additional sections ...
            ],"key_topics": ["list","of","main","topics"],"reasoning": "explanation of your structuring decisions"
        }
        
        Focus on creating a structure that would be useful for educational purposes
        and knowledge graph construction.
        """
        
        # Prompt template for content structuring
        self.content_structuring_prompt = ChatPromptTemplate.from_messages([
            ("system", self.content_structuring_system_prompt),
            ("human", """DOCUMENT INFORMATION:
Type: {{document_type}}
Title: {{title}}

EXTRACTION STRATEGY USED:
{{extraction_strategy}}

EXTRACTED CONTENT:
{{content}}

Please structure this educational content hierarchically.""")
        ])
        
        # Initialize parsers
        self.extraction_planning_parser = JsonOutputParser()
        self.content_structuring_parser = JsonOutputParser()
        
        # Build chains
        self.extraction_planning_chain = self.build_chain_of_thought_chain(
            self.extraction_planning_prompt,
            self.extraction_planning_parser
        )
        
        self.content_structuring_chain = self.build_chain_of_thought_chain(
            self.content_structuring_prompt,
            self.content_structuring_parser
        )
        
        logger.info("Initialized adaptive extraction prompts and chains")
    
    def create_extraction_plan(self, document_info: Dict[str, Any], content_sample: str) -> Dict[str, Any]:
        """
        Create a plan for extracting content from a document.
        
        Args:
            document_info (Dict[str, Any]): Information about the document
            content_sample (str): Sample content from the document
            
        Returns:
            Dict[str, Any]: Extraction plan
        """
        logger.info(f"Creating extraction plan for document: {document_info.get('title', 'untitled')}")
        
        # Prepare input for extraction planning
        input_data = {"document_type": document_info.get("document_type","unknown"),"title": document_info.get("title","untitled"),"page_count": document_info.get("page_count","unknown"),"content": content_sample[:2000] + "..." if len(content_sample) > 2000 else content_sample
        }
        
        # Run the extraction planning chain with error handling
        try:
            result = self.run_with_error_handling(self.extraction_planning_chain, input_data)
            
            if result.get("status") =="success":
                extraction_plan = result["result"]
                logger.info(f"Created extraction plan with {len(extraction_plan.get('extraction_plan', []))} steps")
                return extraction_plan
            else:
                logger.error(f"Error creating extraction plan: {result.get('error_message')}")
                return {"document_structure": {"sections": [],"hierarchy_depth": 1,"has_complex_layouts": False,"has_tables": False,"has_diagrams": False,"has_images": False
                    },"extraction_strategy": {"approach":"basic","process_tables": False,"process_images": False,"section_detection":"simple","hierarchical_extraction": False
                    },"extraction_plan": [
                        "Extract basic text content"
                    ],"error": result.get("error_message", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Exception in extraction planning: {str(e)}")
            return {"document_structure": {"sections": [],"hierarchy_depth": 1,"has_complex_layouts": False,"has_tables": False,"has_diagrams": False,"has_images": False
                },"extraction_strategy": {"approach":"basic","process_tables": False,"process_images": False,"section_detection":"simple","hierarchical_extraction": False
                },"extraction_plan": [
                    "Extract basic text content"
                ],"error": str(e)
            }
            
    def structure_content(self, document_info: Dict[str, Any], extraction_strategy: Dict[str, Any], 
                         extracted_content: str) -> Dict[str, Any]:
        """
        Structure extracted content hierarchically.
        
        Args:
            document_info (Dict[str, Any]): Information about the document
            extraction_strategy (Dict[str, Any]): The extraction strategy used
            extracted_content (str): The extracted content to structure
            
        Returns:
            Dict[str, Any]: Structured content
        """
        logger.info(f"Structuring content for document: {document_info.get('title', 'untitled')}")
        
        # Prepare input for content structuring
        input_data = {"document_type": document_info.get("document_type","unknown"),"title": document_info.get("title","untitled"),"extraction_strategy": json.dumps(extraction_strategy, indent=2),"content": extracted_content[:4000] + "..." if len(extracted_content) > 4000 else extracted_content
        }
        
        # Run the content structuring chain with error handling
        try:
            result = self.run_with_error_handling(self.content_structuring_chain, input_data)
            
            if result.get("status") =="success":
                structured_content = result["result"]
                logger.info(f"Structured content with {len(structured_content.get('content', []))} top-level sections")
                return structured_content
            else:
                logger.error(f"Error structuring content: {result.get('error_message')}")
                return {"title": document_info.get("title","untitled"),"document_type": document_info.get("document_type","unknown"),"educational_level":"unknown","content": [
                        {"section_type":"paragraph","content": extracted_content[:1000] + "..." if len(extracted_content) > 1000 else extracted_content,"level": 1,"children": [],"key_concepts": [],"educational_role":"content"
                        }
                    ],"key_topics": [],"reasoning": "Error structuring content, using fallback structure","error": result.get("error_message", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Exception in content structuring: {str(e)}")
            return {"title": document_info.get("title","untitled"),"document_type": document_info.get("document_type","unknown"),"educational_level":"unknown","content": [
                    {"section_type":"paragraph","content": extracted_content[:1000] + "..." if len(extracted_content) > 1000 else extracted_content,"level": 1,"children": [],"key_concepts": [],"educational_role":"content"
                    }
                ],"key_topics": [],"reasoning": "Exception in content structuring, using fallback structure","error": str(e)
            } 