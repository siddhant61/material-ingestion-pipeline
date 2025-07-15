# Slide Processor

This component of the educational content pipeline is responsible for processing educational slide files (PDFs) and extracting structured information aligned with the course context and transcript data.

## Functionality

The SlideProcessor provides the following capabilities:

1. **PDF Content Extraction**: Extract text and image information from slide deck PDFs
2. **Slide Structure Analysis**: Identify slides, their titles, content, and organization
3. **Course Alignment**: Align slides with the course structure from the global context
4. **Transcript Matching**: Connect slide content with relevant transcript segments
5. **Visual Element Analysis**: Identify diagrams, figures, and important visual elements
6. **Concept Extraction**: Identify key concepts, terms, and relationships in each slide

## Input Format

The slide processor expects:

1. **Slide PDFs**: PDF files containing educational slides/presentations
2. **Course Context**: JSON structure containing the course structure, learning outcomes, and other context information (output from the CourseContextExtractor)
3. **Transcript Data** (optional): Structured transcript data from the TranscriptProcessor

## Dependencies

The slide processor requires these additional Python packages:

- `pypdf`: For basic PDF text extraction
- `PyMuPDF` (fitz): For enhanced PDF processing and image extraction

Install these dependencies with:

```bash
pip install pypdf PyMuPDF
```

## Output Format

The slide processor produces structured JSON output with the following format:

```json
{
  "slide_deck_info": {
    "title": "Slide deck title",
    "slide_count": 45,
    "estimated_duration": "90 minutes",
    "main_topic": "Quantum Computing Basics"
  },
  "alignment": {
    "course_module": "Module name",
    "module_position": "Position within module",
    "learning_outcomes": ["Learning outcomes addressed"],
    "transcript_alignment": "Matching transcript file if available"
  },
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "title",
      "title": "Introduction to Quantum Computing",
      "content": "Full text content of the slide",
      "section": "Introduction",
      "has_image": true,
      "image_description": "Description of image if present",
      "keywords": ["quantum", "computing", "introduction"],
      "concepts": ["quantum computing", "superposition"],
      "relationships": ["quantum computing builds on quantum mechanics"],
      "matching_transcript_segments": ["segment-123", "segment-124"]
    }
  ],
  "key_topics": ["Quantum Computing", "Qubits", "Superposition"],
  "visual_elements": [
    {
      "slide_number": 12,
      "element_type": "diagram",
      "description": "Bloch sphere representation of a qubit",
      "concepts_illustrated": ["qubit representation", "Bloch sphere"]
    }
  ],
  "extraction_metadata": {
    "title": "Extracted metadata title",
    "author": "Document author",
    "page_count": 45,
    "has_images": true
  }
}
```

## Usage

```python
from core.agents.slide_processor import SlideProcessor

# Initialize the processor
processor = SlideProcessor()

# Process a single slide deck
slide_data = processor.process_slide_deck(
    "path/to/slides.pdf",
    course_context_data,
    transcript_data  # Optional
)

# Process all slide decks in a directory
results = processor.process_all_slides(
    "path/to/slides/directory",
    course_context_data,
    transcript_data,  # Optional
    "path/to/output/directory"
)
```

## Integration with Pipeline

The slide processor is designed to work in the educational content pipeline:

1. It receives global course context extracted by the CourseContextExtractor
2. It optionally uses transcript data from the TranscriptProcessor
3. It processes slide files and extracts structured information
4. It outputs data that can be used by downstream components like context fusion modules

## Matching with Transcripts

When transcript data is available, the slide processor will:

1. Find the most likely matching transcript based on filename similarity
2. Align slide content with transcript segments based on content similarity
3. Include transcript segment IDs in the slide data for cross-referencing

## Fallback Behavior

If AI-powered processing fails, the processor falls back to basic slide extraction, which:

1. Extracts basic slide text and structure
2. Preserves slide numbers and content
3. Attempts simple keyword extraction
4. Attempts basic alignment with course structure
