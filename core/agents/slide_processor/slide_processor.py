"""
Slide Processor

This module provides functionality for processing educational slide files (PDFs) 
and extracting structured information aligned with the course context and transcript data.
"""

import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.assistants.base_assistant import BaseAssistant

# Configure logging
logger = logging.getLogger(__name__)

class SlideProcessor(BaseAssistant):
    """
    Processor for educational slide files that:
    1. Extracts text and images from PDF slides
    2. Structures slide content by slide number and section
    3. Aligns slides with course structure from global context
    4. Matches slides with transcript segments when available
    5. Extracts key concepts, terms, and diagrams
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize the slide processor.
        
        Args:
            model_name (str): Name of the model to use
        """
        super().__init__(model_name=model_name)
        self._init_prompts()
        
    def _init_prompts(self):
        """Initialize prompt templates for slide processing."""
        
        # System prompt for slide analysis
        self.slide_analysis_system_prompt = """
        You are an expert in educational content analysis specializing in analyzing 
        slide decks and presentation materials from educational courses.
        
        You will be provided with slide content, course context information, and optionally
        related transcript data. Your task is to:
        1. Identify the structure and organization of the slide deck
        2. Extract key concepts, definitions, and relationships 
        3. Align slides with the course structure from the provided context
        4. Match slides with transcript segments when available
        5. Identify diagrams, figures, and important visual elements
        
        FORMAT YOUR RESPONSE AS A JSON OBJECT with the following structure:
        {{
            "slide_deck_info": {{
                "title": "slide deck title",
                "slide_count": number of slides,
                "estimated_duration": "estimated presentation time",
                "main_topic": "primary topic of the slides"
            }},
            "alignment": {{
                "course_module": "name of the course module these slides belong to",
                "module_position": "position within the module (e.g., 'lecture 1', 'introduction')",
                "learning_outcomes": ["list of learning outcomes addressed in these slides"],
                "transcript_alignment": "matching transcript file if available"
            }},
            "slides": [
                {{
                    "slide_number": slide number (1-indexed),
                    "slide_type": "title|content|diagram|exercise|summary|etc.",
                    "title": "title or heading of the slide",
                    "content": "main text content of the slide",
                    "section": "section name or topic",
                    "has_image": boolean indicating presence of images,
                    "image_description": "description of image content if present",
                    "keywords": ["list of important keywords on this slide"],
                    "concepts": ["list of key concepts explained on this slide"],
                    "relationships": ["list of relationships between concepts"],
                    "matching_transcript_segments": ["list of transcript segment IDs that match this slide"]
                }}
            ],
            "key_topics": ["list of the most important topics covered in the slides"],
            "visual_elements": [
                {{
                    "slide_number": slide number containing the visual element,
                    "element_type": "diagram|chart|table|image|etc.",
                    "description": "description of the visual element",
                    "concepts_illustrated": ["concepts illustrated by this visual"]
                }}
            ]
        }}
        
        IMPORTANT GUIDELINES:
        1. Analyze both the text and any described visual elements
        2. For each slide, identify the key concepts and their relationships
        3. Ensure proper alignment with the course structure from the context
        4. When transcript data is provided, match slides to appropriate segments
        5. Include only the most relevant information in the key topics
        """
        
        # Human prompt template for slide analysis with transcript data
        self.slide_analysis_with_transcript_prompt = """
        Here is a slide deck to analyze:
        
        COURSE CONTEXT:
        {course_context}
        
        TRANSCRIPT DATA (if available):
        {transcript_data}
        
        SLIDE DECK FILENAME:
        {slide_filename}
        
        SLIDE CONTENT:
        {slide_content}
        
        Please analyze this slide deck, aligning it with the course context and transcript data.
        """
        
        # Human prompt template for slide analysis without transcript data
        self.slide_analysis_without_transcript_prompt = """
        Here is a slide deck to analyze:
        
        COURSE CONTEXT:
        {course_context}
        
        SLIDE DECK FILENAME:
        {slide_filename}
        
        SLIDE CONTENT:
        {slide_content}
        
        Please analyze this slide deck, aligning it with the course context.
        """
        
        # Create the full prompt templates
        self.slide_analysis_with_transcript_template = ChatPromptTemplate.from_messages([
            ("system", self.slide_analysis_system_prompt),
            ("human", self.slide_analysis_with_transcript_prompt)
        ])
        
        self.slide_analysis_without_transcript_template = ChatPromptTemplate.from_messages([
            ("system", self.slide_analysis_system_prompt),
            ("human", self.slide_analysis_without_transcript_prompt)
        ])
        
        # Setup the processing chains
        self.slide_analysis_with_transcript_chain = self.build_chain_of_thought_chain(
            self.slide_analysis_with_transcript_template,
            JsonOutputParser()
        )
        
        self.slide_analysis_without_transcript_chain = self.build_chain_of_thought_chain(
            self.slide_analysis_without_transcript_template,
            JsonOutputParser()
        )
    
    def extract_slide_content(self, slide_path: str, output_dir: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Extract content from a slide deck PDF file.
        
        Args:
            slide_path (str): Path to the slide deck PDF file
            output_dir (Optional[str]): Directory to save extracted images
            
        Returns:
            Tuple[str, Dict[str, Any]]: Extracted text content and basic metadata
        """
        slide_path = Path(slide_path)
        logger.info(f"Extracting content from slide deck: {slide_path.name}")
        
        try:
            # Import PDF tools here to avoid unnecessary dependencies if not used
            from pypdf import PdfReader
            import fitz  # PyMuPDF
            
            # Basic extraction with PyPDF
            pdf = PdfReader(slide_path)
            num_pages = len(pdf.pages)
            
            # Extract text content
            text_content = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text() or f"[Slide {i+1} - No text content]"
                text_content.append(f"--- Slide {i+1} ---\n{page_text}")
            
            # Extract images info with PyMuPDF for enhanced image processing
            doc = fitz.open(slide_path)
            image_info = []
            extracted_images = []
            
            # Setup output directory for images if specified
            if output_dir:
                output_path = Path(output_dir)
                os.makedirs(output_path, exist_ok=True)
            
            for i, page in enumerate(doc):
                images = page.get_images()
                
                if images:
                    # Enhanced image extraction
                    image_details = {
                        "slide_number": i+1,
                        "image_count": len(images),
                        "has_image": True,
                        "image_texts": [],
                        "image_paths": []
                    }
                    
                    # Save actual image files if output_dir is provided
                    if output_dir:
                        for img_index, img in enumerate(images):
                            try:
                                xref = img[0]
                                base_image = doc.extract_image(xref)
                                
                                # Validate extracted image format
                                if not base_image or "image" not in base_image or "ext" not in base_image:
                                    logger.warning(f"Invalid image format for image {img_index+1} on slide {i+1}")
                                    continue
                                
                                image_bytes = base_image["image"]
                                image_ext = base_image["ext"]
                                
                                # Create filename
                                image_filename = f"{slide_path.stem}_slide{i+1}_img{img_index+1}.{image_ext}"
                                image_path = output_path / image_filename
                                
                                # Save image
                                with open(image_path, "wb") as img_file:
                                    img_file.write(image_bytes)
                                
                                image_details["image_paths"].append(str(image_path))
                                extracted_images.append(str(image_path))
                                logger.debug(f"Saved image: {image_path}")
                            except Exception as img_save_err:
                                logger.warning(f"Error saving image {img_index+1} from slide {i+1}: {str(img_save_err)}")
                    
                    # Basic OCR for image content when possible
                    try:
                        # Extract text blocks that may be on top of images
                        blocks = page.get_text("blocks")
                        for block in blocks:
                            # Check if block is likely associated with an image (based on position)
                            if any(block[:4] for img in images):
                                image_details["image_texts"].append(block[4])  # Text content
                    except Exception as img_err:
                        logger.warning(f"Error extracting image text from slide {i+1}: {str(img_err)}")
                    
                    image_info.append(image_details)
            
            # Process metadata properly - avoid datetime objects that can cause JSON serialization issues
            creation_date = pdf.metadata.creation_date
            if creation_date:
                if hasattr(creation_date, 'isoformat'):
                    creation_date_str = creation_date.isoformat()
                else:
                    # If it's already a string or other format, convert safely
                    creation_date_str = str(creation_date)
            else:
                creation_date_str = datetime.now().isoformat()
            
            # Extract metadata
            metadata = {
                "title": pdf.metadata.title or slide_path.stem,
                "author": pdf.metadata.author or "Unknown",
                "creation_date": creation_date_str,
                "page_count": num_pages,
                "has_images": any(page.get_images() for page in doc),
                "filename": slide_path.name,
                "image_info": image_info,
                "extracted_images": extracted_images
            }
            
            # Close PyMuPDF document
            doc.close()
            
            logger.info(f"Successfully extracted content from {slide_path.name}: {num_pages} slides, images: {metadata['has_images']}")
            return "\n\n".join(text_content), metadata
            
        except Exception as e:
            logger.exception(f"Error extracting content from {slide_path.name}: {str(e)}")
            # Return minimal content
            return f"[Error extracting content from {slide_path.name}]", {
                "title": slide_path.stem,
                "page_count": 0,
                "has_images": False,
                "filename": slide_path.name,
                "creation_date": datetime.now().isoformat(),  # Ensure this field is always present
                "error": str(e)
            }
    
    def find_matching_transcript(self, slide_filename: str, transcript_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a matching transcript for a slide deck based on filename similarity.
        
        Args:
            slide_filename (str): Filename of the slide deck
            transcript_data (Dict[str, Any]): Collection of transcript data
            
        Returns:
            Optional[Dict[str, Any]]: Matching transcript data if found
        """
        if not transcript_data or "transcripts" not in transcript_data:
            return None
        
        slide_name = Path(slide_filename).stem.lower()
        best_match = None
        best_match_score = 0
        
        for transcript in transcript_data.get("transcripts", []):
            if "filename" not in transcript:
                continue
                
            transcript_name = Path(transcript["filename"]).stem.lower()
            
            # Calculate simple similarity score (common words)
            slide_words = set(re.findall(r'\w+', slide_name))
            transcript_words = set(re.findall(r'\w+', transcript_name))
            
            common_words = slide_words.intersection(transcript_words)
            if not common_words:
                continue
                
            # Calculate score based on common words and length similarity
            similarity_score = len(common_words) / max(len(slide_words), len(transcript_words))
            
            if similarity_score > best_match_score:
                best_match_score = similarity_score
                best_match = transcript
        
        # Only return match if similarity is above threshold
        if best_match_score > 0.3:
            logger.info(f"Found matching transcript for {slide_filename}: {best_match.get('filename')} (score: {best_match_score:.2f})")
            
            # Load the full transcript data
            if "output_file" in best_match:
                try:
                    with open(best_match["output_file"], 'r', encoding='utf-8') as f:
                        full_transcript = json.load(f)
                    return full_transcript
                except Exception as e:
                    logger.warning(f"Error loading matching transcript file: {str(e)}")
            
            return best_match
            
        return None
    
    def _match_slide_to_transcript_segments(self, slide_content: str, transcript_segments: List[Dict[str, Any]]) -> List[str]:
        """
        Match a slide's content to transcript segments based on content similarity.
        
        Args:
            slide_content (str): Text content of the slide
            transcript_segments (List[Dict[str, Any]]): List of transcript segments
            
        Returns:
            List[str]: List of matching transcript segment IDs
        """
        matching_segments = []
        
        # Extract key terms from slide content (nouns, verbs, technical terms)
        slide_terms = set(re.findall(r'\b[A-Z][a-z]{2,}\b|\b[a-z]{3,}\b', slide_content.lower()))
        
        # Remove common stopwords
        stopwords = {"und", "oder", "der", "die", "das", "ein", "eine", "ist", "sind", "von", "mit", "für", "auf", "in", "im", "sich", "den", "dem", "des"}
        slide_terms = slide_terms - stopwords
        
        # Match with transcript segments
        for segment in transcript_segments:
            segment_id = segment.get("id", "")
            segment_text = segment.get("text", "").lower()
            
            # Extract terms from transcript segment
            segment_terms = set(re.findall(r'\b[A-Z][a-z]{2,}\b|\b[a-z]{3,}\b', segment_text.lower())) - stopwords
            
            # Calculate overlap
            common_terms = slide_terms.intersection(segment_terms)
            if len(common_terms) >= 3 or (len(common_terms) >= 2 and len(slide_terms) <= 5):
                matching_segments.append(segment_id)
                
        return matching_segments
    
    def _normalize_math_notation(self, text: str) -> str:
        """
        Normalize mathematical notation in text for better readability.
        
        Args:
            text (str): Original text with potentially malformed mathematical notation
            
        Returns:
            str: Text with normalized mathematical notation
        """
        # Replace common malformed quantum notation with proper symbols
        replacements = [
            (r'ۧȁ0', '|0⟩'),
            (r'ۧȁ1', '|1⟩'),
            (r'\|ۧ0', '|0⟩'),
            (r'\|ۧ1', '|1⟩'),
            (r'ۧ0', '|0⟩'),
            (r'ۧ1', '|1⟩'),
            (r'α\|0', 'α|0⟩'),
            (r'β\|1', 'β|1⟩')
        ]
        
        normalized_text = text
        for pattern, replacement in replacements:
            normalized_text = re.sub(pattern, replacement, normalized_text)
            
        return normalized_text
    
    def _extract_cross_slide_relationships(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relationships between concepts across different slides.
        
        Args:
            slides (List[Dict[str, Any]]): List of processed slides
            
        Returns:
            List[Dict[str, Any]]: List of cross-slide concept relationships
        """
        relationships = []
        
        # Collect all concepts from all slides
        all_concepts = {}
        for slide in slides:
            slide_num = slide.get("slide_number", 0)
            for concept in slide.get("concepts", []):
                if concept not in all_concepts:
                    all_concepts[concept] = []
                all_concepts[concept].append(slide_num)
        
        # Find concepts that appear in sequence (potential progression)
        for concept1 in all_concepts:
            for concept2 in all_concepts:
                if concept1 != concept2:
                    # Check if concept2 tends to appear in slides after concept1
                    if min(all_concepts[concept1]) < min(all_concepts[concept2]):
                        relationships.append({
                            "source_concept": concept1,
                            "target_concept": concept2,
                            "relationship_type": "progression",
                            "source_slides": all_concepts[concept1],
                            "target_slides": all_concepts[concept2]
                        })
        
        return relationships
    
    def process_slide_deck(self, slide_path: str, course_context: Dict[str, Any], 
                          transcript_data: Optional[Dict[str, Any]] = None, 
                          images_output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a slide deck PDF and align it with course context and transcript data.
        
        Args:
            slide_path (str): Path to the slide deck PDF file
            course_context (Dict[str, Any]): Previously extracted course context
            transcript_data (Optional[Dict[str, Any]]): Previously processed transcript data
            images_output_dir (Optional[str]): Directory to save extracted images
            
        Returns:
            Dict[str, Any]: Structured slide deck data aligned with course context
        """
        slide_path = Path(slide_path)
        logger.info(f"Processing slide deck: {slide_path.name}")
        
        try:
            # Extract slide content
            slide_content, slide_metadata = self.extract_slide_content(str(slide_path), images_output_dir)
            
            # Find matching transcript if available
            matching_transcript = None
            if transcript_data:
                matching_transcript = self.find_matching_transcript(slide_path.name, transcript_data)
            
            # Normalize math notation in slide content
            normalized_slide_content = self._normalize_math_notation(slide_content)
            
            # Prepare input for AI processing
            input_data = {
                "slide_filename": slide_path.name,
                "slide_content": normalized_slide_content,
                "course_context": json.dumps(course_context, ensure_ascii=False)
            }
            
            # Use appropriate chain based on transcript availability
            if matching_transcript:
                input_data["transcript_data"] = json.dumps(matching_transcript, ensure_ascii=False)
                result = self.run_with_error_handling(self.slide_analysis_with_transcript_chain, input_data)
            else:
                result = self.run_with_error_handling(self.slide_analysis_without_transcript_chain, input_data)
            
            if result.get("status") == "success":
                structured_slides = result["result"]
                
                # Add metadata from extraction
                structured_slides["extraction_metadata"] = slide_metadata
                
                # Enhance with transcript segment matching if available
                if matching_transcript and "segments" in matching_transcript:
                    transcript_segments = matching_transcript.get("segments", [])
                    
                    for slide in structured_slides.get("slides", []):
                        matching_segments = self._match_slide_to_transcript_segments(
                            slide.get("content", ""), 
                            transcript_segments
                        )
                        slide["matching_transcript_segments"] = matching_segments
                
                # Add cross-slide relationships
                cross_slide_relationships = self._extract_cross_slide_relationships(
                    structured_slides.get("slides", [])
                )
                structured_slides["cross_slide_relationships"] = cross_slide_relationships
                
                logger.info(f"Successfully processed slide deck with {len(structured_slides.get('slides', []))} analyzed slides")
                return structured_slides
            else:
                logger.error(f"Error processing slide deck: {result.get('error_message')}")
                return self._generate_basic_slide_data(slide_path.name, slide_content, slide_metadata, course_context)
                
        except Exception as e:
            logger.exception(f"Exception in slide deck processing: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to process slide deck: {str(e)}",
                "slide_filename": slide_path.name,
                "creation_date": datetime.now().isoformat()  # Ensure this field is always present
            }
    
    def _generate_basic_slide_data(self, filename: str, content: str, metadata: Dict[str, Any], 
                                  course_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate basic slide deck data when AI processing fails.
        
        Args:
            filename (str): Slide deck filename
            content (str): Extracted slide content
            metadata (Dict[str, Any]): Extraction metadata
            course_context (Dict[str, Any]): Course context
            
        Returns:
            Dict[str, Any]: Basic slide deck data structure
        """
        try:
            # Extract title from filename
            title = metadata.get("title", Path(filename).stem)
            
            # Extract slide count
            slide_count = metadata.get("page_count", 0)
            
            # Extract individual slides
            slide_pattern = re.compile(r"---\s*Slide\s+(\d+)\s*---\n(.*?)(?=---\s*Slide|\Z)", re.DOTALL)
            slides_matches = slide_pattern.findall(content)
            
            slides = []
            for slide_num, slide_content in slides_matches:
                # Try to extract a title from the slide content
                slide_title = ""
                lines = slide_content.strip().split("\n")
                if lines:
                    slide_title = lines[0].strip()
                
                slides.append({
                    "slide_number": int(slide_num),
                    "slide_type": "content",
                    "title": slide_title[:100] if slide_title else f"Slide {slide_num}",
                    "content": slide_content.strip(),
                    "section": "Unknown",
                    "has_image": any(img["slide_number"] == int(slide_num) for img in metadata.get("image_info", [])),
                    "image_description": "Image content not analyzed in basic processing",
                    "keywords": [],
                    "concepts": [],
                    "relationships": [],
                    "matching_transcript_segments": []
                })
            
            # Find matching module in course context if possible
            matching_module = "Unknown"
            module_position = "Unknown"
            learning_outcomes = []
            
            # Try to match the slide deck to a module based on the title
            if isinstance(course_context, dict) and "course_structure" in course_context and "modules" in course_context["course_structure"]:
                for module in course_context["course_structure"]["modules"]:
                    module_title = module.get("title", "")
                    if module_title and (module_title.lower() in title.lower() or title.lower() in module_title.lower()):
                        matching_module = module_title
                        if "lessons" in module and isinstance(module["lessons"], list):
                            for i, lesson in enumerate(module["lessons"]):
                                lesson_title = lesson.get("title", "")
                                if lesson_title and (lesson_title.lower() in title.lower() or title.lower() in lesson_title.lower()):
                                    module_position = f"Lesson {i+1}"
                                    break
                        break
            
            # Extract potential keywords
            keywords = set()
            for slide in slides:
                # Simple keyword extraction based on capitalization and frequency
                words = re.findall(r'\b[A-Z][a-z]{2,}\b', slide["content"])
                common_words = re.findall(r'\b[a-z]{3,}\b', slide["content"].lower())
                word_freq = {}
                for word in common_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
                
                # Add capitalized words and frequent common words
                keywords.update([w for w in words if len(w) > 3])
                keywords.update([w for w, freq in word_freq.items() if freq > 3 and len(w) > 3])
            
            # Limit keywords to 20
            top_keywords = list(keywords)[:20]
            
            return {
                "slide_deck_info": {
                    "title": title,
                    "slide_count": slide_count,
                    "estimated_duration": f"{slide_count * 2} minutes (estimated)",
                    "main_topic": title
                },
                "alignment": {
                    "course_module": matching_module,
                    "module_position": module_position,
                    "learning_outcomes": learning_outcomes,
                    "transcript_alignment": "None"
                },
                "slides": slides,
                "key_topics": top_keywords[:5],
                "visual_elements": [
                    {
                        "slide_number": img["slide_number"],
                        "element_type": "image",
                        "description": "Visual element (not analyzed in basic processing)",
                        "concepts_illustrated": []
                    } for img in metadata.get("image_info", [])
                ],
                "extraction_metadata": metadata
            }
        except Exception as e:
            logger.exception(f"Error in basic slide data generation: {str(e)}")
            # Return a minimal valid structure
            return {
                "slide_deck_info": {
                    "title": Path(filename).stem,
                    "slide_count": metadata.get("page_count", 0),
                    "estimated_duration": "Unknown",
                    "main_topic": "Unknown"
                },
                "alignment": {
                    "course_module": "Unknown",
                    "module_position": "Unknown",
                    "learning_outcomes": [],
                    "transcript_alignment": "None"
                },
                "slides": [],
                "key_topics": [],
                "visual_elements": [],
                "extraction_metadata": metadata,
                "error": str(e)
            }
    
    def process_all_slides(self, slides_dir: str, course_context: Dict[str, Any], 
                          transcript_data: Optional[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        """
        Process all slide decks in a directory.
        
        Args:
            slides_dir (str): Directory containing slide deck files
            course_context (Dict[str, Any]): Course context for alignment
            transcript_data (Optional[Dict[str, Any]]): Transcript data for matching
            output_dir (str): Directory to save processed slides
            
        Returns:
            Dict[str, Any]: Summary of slide processing results
        """
        slides_dir = Path(slides_dir)
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create images output directory
        images_dir = output_dir.parent / "slide_images"
        os.makedirs(images_dir, exist_ok=True)
        
        logger.info(f"Processing all slide decks in {slides_dir}")
        logger.info(f"Saving extracted images to {images_dir}")
        
        results = {
            "processed_count": 0,
            "error_count": 0,
            "slides": [],
            "images_directory": str(images_dir)
        }
        
        # Process each slide deck file
        for slide_file in slides_dir.glob("*.pdf"):
            try:
                # Process the slide deck
                slide_data = self.process_slide_deck(
                    str(slide_file), 
                    course_context,
                    transcript_data,
                    str(images_dir)
                )
                
                # Save the result with proper serialization
                output_file = output_dir / f"{slide_file.stem}_processed.json"
                try:
                    # Ensure all values are properly serializable
                    def sanitize_for_json(item):
                        if isinstance(item, (str, int, float, bool, type(None))):
                            return item
                        elif isinstance(item, (list, tuple)):
                            return [sanitize_for_json(i) for i in item]
                        elif isinstance(item, dict):
                            return {str(k): sanitize_for_json(v) for k, v in item.items()}
                        else:
                            return str(item)
                    
                    # Sanitize the data
                    sanitized_data = sanitize_for_json(slide_data)
                    
                    # Write to file
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(sanitized_data, f, ensure_ascii=False, indent=2)
                    
                except Exception as json_err:
                    logger.error(f"Error saving JSON for {slide_file.name}: {str(json_err)}")
                    # Fallback to simpler approach
                    with open(output_file, 'w', encoding='utf-8') as f:
                        # Convert all non-serializable objects to strings
                        simplified_data = json.loads(json.dumps(slide_data, default=str, ensure_ascii=False))
                        json.dump(simplified_data, f, ensure_ascii=False, indent=2)
                
                # Add to results summary
                results["processed_count"] += 1
                results["slides"].append({
                    "filename": slide_file.name,
                    "title": slide_data.get("slide_deck_info", {}).get("title", "Unknown"),
                    "module": slide_data.get("alignment", {}).get("course_module", "Unknown"),
                    "slide_count": slide_data.get("slide_deck_info", {}).get("slide_count", 0),
                    "output_file": str(output_file)
                })
                
                logger.info(f"Successfully processed and saved slide deck: {slide_file.name}")
                
            except Exception as e:
                logger.exception(f"Error processing slide deck {slide_file.name}: {str(e)}")
                results["error_count"] += 1
                results["slides"].append({
                    "filename": slide_file.name,
                    "status": "error",
                    "error_message": str(e)
                })
        
        # Save summary
        summary_file = output_dir / "slide_processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Slide processing complete: {results['processed_count']} processed, {results['error_count']} errors")
        logger.info(f"Summary saved to {summary_file}")
        
        return results 