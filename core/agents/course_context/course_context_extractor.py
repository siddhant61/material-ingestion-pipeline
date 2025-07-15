"""
Course Context Extractor

This module provides the CourseContextExtractor class for extracting comprehensive
context from course information PDFs.
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class CourseContextExtractor:
    """
    Extracts comprehensive context from course information PDFs.

    The CourseContextExtractor analyzes course documents to extract structured data
    including course objectives, structure, instructor information, prerequisites,
    and related resources.
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize the CourseContextExtractor.

        Args:
            model_name (str, optional): Model to use for extraction. Defaults to "gpt-4o-mini".
        """
        self.model_name = model_name
        
        # Initialize prompt templates
        self._init_prompts()
        
        logger.info(f"Initialized CourseContextExtractor with model: {model_name}")

    def _init_prompts(self):
        """Initialize prompt templates for context extraction."""
        # System prompt for the extraction
        self.system_prompt = """
        You are an expert educational content analyzer specializing in extracting structured information from course materials.
        Your task is to analyze the provided course content and extract comprehensive context following these guidelines:
        
        1. Extract ALL available information into the structured schema - don't skip any fields or information
        2. Be factual and precise - only use information explicitly stated in the document
        3. When information is not provided, indicate this with "Not specified in document" rather than making assumptions
        4. Format extracted data in JSON format according to the specified schema
        5. Provide complete and comprehensive information for each field
        6. For taxonomies and hierarchies (like course structure), preserve the exact hierarchical relationships
        
        After extraction, verify the completeness of your schema to ensure all available information has been captured.
        """
        
        # Human prompt template for the extraction
        self.human_prompt_template = """
        Please analyze this course material and extract comprehensive course context in a structured JSON format.
        
        COURSE MATERIAL:
        {document_content}
        
        DOCUMENT METADATA:
        {document_metadata}
        
        Extract all available information into the following JSON schema:
        
        ```
        {{
            "title": "Full course title",
            "description": "Comprehensive course description",
            "objectives": [
                "List of learning objectives"
            ],
            "learning_outcomes": [
                "Expected outcomes after course completion"
            ],
            "subject_domain": "Primary subject domain",
            "sub_domains": ["Related sub-domains"],
            "level": "Educational level (e.g., undergraduate, graduate)",
            "prerequisites": [
                "Required prerequisites"
            ],
            "credits": "Number of credits if applicable",
            "duration": "Duration information",
            "structure": [
                {{
                    "title": "Module/section title",
                    "description": "Module/section description",
                    "topics": ["Topic 1", "Topic 2"],
                    "sub_sections": [
                        {{
                            "title": "Sub-section title",
                            "description": "Sub-section description",
                            "topics": ["Topic 1", "Topic 2"]
                        }}
                    ]
                }}
            ],
            "instructors": [
                {{
                    "name": "Instructor name",
                    "title": "Academic title/position",
                    "bio": "Brief biography",
                    "contact": "Contact information if available"
                }}
            ],
            "teaching_methods": [
                "List of teaching methods used"
            ],
            "assessment_methods": [
                "List of assessment methods"
            ],
            "materials": [
                "List of course materials"
            ],
            "references": [
                "Bibliographic references"
            ],
            "keywords": [
                "Key terms and concepts"
            ],
            "language": "Primary language of instruction",
            "certification": "Any certification information",
            "target_audience": "Description of intended audience",
            "institutional_context": {{
                "institution": "Hosting institution",
                "department": "Department/faculty",
                "program": "Program this course belongs to"
            }}
        }}
        ```
        
        Ensure all available information is captured in the appropriate fields. If information is not available for a specific field, use "Not specified in document" instead of leaving it blank or making assumptions.
        
        After completing the extraction, verify that you have included all relevant information from the document.
        """
        
        # Self-verification prompt
        self.verification_prompt = """
        Now verify your extraction results:
        
        1. Have you included ALL the information available in the document?
        2. Are there any fields with missing information that should be filled?
        3. Are there any inconsistencies or errors in the extracted data?
        
        If you find any issues, please correct the JSON and provide the final, complete extraction.
        
        FINAL VERIFIED EXTRACTION:
        """

    def extract_course_context(self, document_content: str, document_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract structured course context from document content.

        Args:
            document_content (str): Text content of the document
            document_metadata (Dict[str, Any], optional): Metadata about the document

        Returns:
            Dict[str, Any]: Structured course context
        """
        try:
            logger.info("Starting course context extraction")
            
            # Initialize document metadata if not provided
            if document_metadata is None:
                document_metadata = {}
            
            # Import necessary components
            from core.utils.ai_models import AIModelFactory
            
            # Create model instance
            model = AIModelFactory.create_model(self.model_name)
            
            # Prepare the prompt
            prompt = {
                "system": self.system_prompt,
                "user": self.human_prompt_template.format(
                    document_content=document_content[:25000],  # Limit to avoid context length issues
                    document_metadata=json.dumps(document_metadata, ensure_ascii=False, indent=2)
                )
            }
            
            # Generate extraction
            extraction_response = model.generate(prompt)
            
            # Extract JSON
            extracted_context = self._extract_json_from_text(extraction_response)
            
            # Verify and refine the extraction
            verified_context = self._verify_extraction(extracted_context, document_content, model)
            
            # Add extraction metadata
            verified_context["metadata"] = {
                "extraction_timestamp": datetime.now().isoformat(),
                "model_used": self.model_name,
                "document_source": document_metadata.get("source_file", "Unknown"),
                "document_type": document_metadata.get("detected_type", "Unknown"),
                "extraction_confidence": self._calculate_confidence(verified_context),
                "completeness_score": self._calculate_completeness_score(verified_context)
            }
            
            logger.info(f"Extracted course context with completeness score: {verified_context['metadata']['completeness_score']}")
            
            return verified_context
        
        except Exception as e:
            logger.error(f"Error extracting course context: {str(e)}")
            return self._generate_fallback_context(document_content, document_metadata, str(e))

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON object from text response.

        Args:
            text (str): Text containing JSON

        Returns:
            Dict[str, Any]: Extracted JSON
        """
        try:
            # Find JSON block
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in extraction response")
                return {}
            
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        
        except Exception as e:
            logger.error(f"Error extracting JSON from text: {str(e)}")
            return {}

    def _verify_extraction(self, extracted_context: Dict[str, Any], document_content: str, model) -> Dict[str, Any]:
        """
        Verify and refine the extraction results.

        Args:
            extracted_context (Dict[str, Any]): Initially extracted context
            document_content (str): Original document content
            model: AI model instance

        Returns:
            Dict[str, Any]: Verified and refined context
        """
        # Skip verification if extraction failed
        if not extracted_context:
            logger.warning("Skipping verification due to failed extraction")
            return extracted_context
        
        try:
            # First check for completeness
            missing_fields = self._check_schema_completeness(extracted_context)
            
            # If we have missing fields, perform a second pass to fill them
            if missing_fields:
                logger.info(f"Incomplete extraction, missing fields: {missing_fields}")
                
                # Prepare verification prompt
                verification_prompt = {
                    "system": self.system_prompt,
                    "user": f"""
                    I've extracted the following course context, but I'm missing information for these fields: {', '.join(missing_fields)}.
                    
                    EXTRACTED CONTEXT:
                    {json.dumps(extracted_context, ensure_ascii=False, indent=2)}
                    
                    ORIGINAL DOCUMENT:
                    {document_content[:10000]}
                    
                    Please review the original document and provide a COMPLETE JSON with all missing fields filled if the information is available.
                    Specifically focus on extracting information for: {', '.join(missing_fields)}.
                    
                    {self.verification_prompt}
                    """
                }
                
                # Generate verification response
                verification_response = model.generate(verification_prompt)
                
                # Extract JSON
                verified_context = self._extract_json_from_text(verification_response)
                
                # Merge with original if extraction failed
                if not verified_context:
                    logger.warning("Verification extraction failed, using original extraction")
                    return extracted_context
                
                # Check if verification improved completeness
                new_missing_fields = self._check_schema_completeness(verified_context)
                if len(new_missing_fields) < len(missing_fields):
                    logger.info(f"Verification improved extraction, remaining missing fields: {new_missing_fields}")
                    return verified_context
                else:
                    logger.info("Verification did not improve extraction, using original")
                    return extracted_context
            
            # If extraction is already complete, return as is
            logger.info("Extraction passed completeness check, no verification needed")
            return extracted_context
        
        except Exception as e:
            logger.error(f"Error during extraction verification: {str(e)}")
            return extracted_context

    def _check_schema_completeness(self, context: Dict[str, Any]) -> List[str]:
        """
        Check if all fields in the schema are populated.

        Args:
            context (Dict[str, Any]): Extracted context

        Returns:
            List[str]: List of missing fields
        """
        missing_fields = []
        
        # Define required top-level fields
        required_fields = [
            "title", "description", "objectives", "learning_outcomes", 
            "subject_domain", "level", "structure", "instructors"
        ]
        
        # Check top-level fields
        for field in required_fields:
            if field not in context or not context[field] or context[field] == "Not specified in document":
                missing_fields.append(field)
        
        # Check nested fields in structure
        if "structure" in context and isinstance(context["structure"], list):
            for i, section in enumerate(context["structure"]):
                if not isinstance(section, dict):
                    missing_fields.append(f"structure[{i}]")
                    continue
                
                if "title" not in section or not section["title"]:
                    missing_fields.append(f"structure[{i}].title")
        
        # Check nested fields in instructors
        if "instructors" in context and isinstance(context["instructors"], list):
            for i, instructor in enumerate(context["instructors"]):
                if not isinstance(instructor, dict):
                    missing_fields.append(f"instructors[{i}]")
                    continue
                
                if "name" not in instructor or not instructor["name"]:
                    missing_fields.append(f"instructors[{i}].name")
        
        return missing_fields

    def _generate_fallback_context(self, document_content: str, document_metadata: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        Generate a minimal fallback context when extraction fails.

        Args:
            document_content (str): Document content
            document_metadata (Dict[str, Any]): Document metadata
            error_message (str): Error message from extraction

        Returns:
            Dict[str, Any]: Minimal fallback context
        """
        # Extract a title from metadata or first line
        title = document_metadata.get("title", "Unknown Course")
        if title == "Unknown Course" and document_content:
            first_line = document_content.strip().split('\n')[0]
            if len(first_line) < 100:  # Reasonable title length
                title = first_line
        
        # Create minimal context
        return {
            "title": title,
            "description": "Content extraction failed",
            "objectives": ["Not available due to extraction failure"],
            "learning_outcomes": ["Not available due to extraction failure"],
            "subject_domain": document_metadata.get("subject", "Unknown"),
            "level": "Unknown",
            "structure": [
                {
                    "title": "Content unavailable",
                    "description": "Course structure could not be extracted",
                    "topics": []
                }
            ],
            "instructors": [
                {
                    "name": document_metadata.get("author", "Unknown"),
                    "title": "",
                    "bio": "",
                    "contact": ""
                }
            ],
            "metadata": {
                "extraction_timestamp": datetime.now().isoformat(),
                "model_used": self.model_name,
                "document_source": document_metadata.get("source_file", "Unknown"),
                "extraction_status": "failed",
                "error_message": error_message,
                "completeness_score": 0.0
            }
        }

    def _calculate_completeness_score(self, context: Dict[str, Any]) -> float:
        """
        Calculate a completeness score for the extracted context.

        Args:
            context (Dict[str, Any]): Extracted context

        Returns:
            float: Completeness score between 0 and 1
        """
        # Define weights for different sections
        weights = {
            "title": 0.05,
            "description": 0.1,
            "objectives": 0.1,
            "learning_outcomes": 0.1,
            "subject_domain": 0.05,
            "level": 0.05,
            "structure": 0.2,
            "instructors": 0.1,
            "teaching_methods": 0.05,
            "assessment_methods": 0.05,
            "materials": 0.05,
            "references": 0.05,
            "keywords": 0.05
        }
        
        score = 0.0
        for field, weight in weights.items():
            if field in context and context[field]:
                # Simple presence check for string fields
                if isinstance(context[field], str):
                    if context[field] != "Not specified in document":
                        score += weight
                
                # Check for non-empty lists
                elif isinstance(context[field], list):
                    if context[field] and context[field][0] != "Not specified in document":
                        score += weight
                
                # Check for structure with content
                elif field == "structure" and isinstance(context[field], list):
                    if context[field] and len(context[field]) > 0:
                        # Check if structure has meaningful content
                        has_content = False
                        for section in context[field]:
                            if isinstance(section, dict) and section.get("title") and section.get("title") != "Not specified in document":
                                has_content = True
                                break
                        
                        if has_content:
                            score += weight
        
        return min(1.0, score)

    def _calculate_confidence(self, context: Dict[str, Any]) -> float:
        """
        Calculate a confidence score for the extraction.

        Args:
            context (Dict[str, Any]): Extracted context

        Returns:
            float: Confidence score between 0 and 1
        """
        # For now, use completeness as a proxy for confidence
        completeness = self._calculate_completeness_score(context)
        
        # Adjust confidence based on completeness
        if completeness > 0.8:
            return 0.9  # High confidence if very complete
        elif completeness > 0.5:
            return 0.7  # Medium confidence
        else:
            return 0.4  # Low confidence
    
    def save_context(self, context: Dict[str, Any], output_dir: str) -> str:
        """
        Save extracted context to a JSON file.

        Args:
            context (Dict[str, Any]): Extracted context
            output_dir (str): Directory to save the file

        Returns:
            str: Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"course_context_{timestamp}.json"
        output_path = os.path.join(output_dir, filename)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved course context to {output_path}")
        
        return output_path


# Example usage
if __name__ == "__main__":
    from core.agents.document_loader.tools.document_analyzer import DocumentAnalyzer
    
    # Initialize the components
    document_analyzer = DocumentAnalyzer()
    course_context_extractor = CourseContextExtractor()
    
    # Example PDF path
    pdf_path = "input/course_material/course_info/Quantencomputing Ferienkurs – Einführung für SchülerInnen.pdf"
    
    # Process the PDF
    pdf_document, basic_metadata = document_analyzer.load_pdf(pdf_path)
    text_content = document_analyzer.extract_text(pdf_document)
    
    # Extract course context
    course_context = course_context_extractor.extract_course_context(
        text_content,
        basic_metadata
    )
    
    # Save the context
    context_file = course_context_extractor.save_context(
        course_context,
        "output/course_context"
    )
    
    print(f"Course context extracted and saved to {context_file}") 