# Transcript Processor

This component of the educational content pipeline is responsible for processing transcript files in WebVTT format and extracting structured information aligned with the global course context.

## Functionality

The TranscriptProcessor provides the following capabilities:

1. **WebVTT Parsing**: Parse transcript files in WebVTT format, extracting timestamps and text content
2. **Context-Aware Segmentation**: Segment transcripts into meaningful units based on topical boundaries
3. **Course Alignment**: Align transcript segments with the course structure from the global context
4. **Concept Extraction**: Identify key concepts, terms, and relationships in each segment
5. **Metadata Generation**: Generate rich metadata about the transcript content, including speaker information and key takeaways

## Input Format

The transcript processor expects:

1. **WebVTT Files**: Text files following the WebVTT format with timestamps and text content:

   ```txt
   WEBVTT
   
   1
   00:00:00.630 --> 00:00:07.389 
   Transcript text content...
   
   2
   00:00:07.389 --> 00:00:13.310 
   More transcript text...
   ```

2. **Course Context**: JSON structure containing the course structure, learning outcomes, and other context information (output from the CourseContextExtractor)

## Output Format

The transcript processor produces structured JSON output with the following format:

```json
{
  "transcript_info": {
    "title": "Lecture title",
    "duration": "total duration",
    "word_count": 1500,
    "speaker_count": 1
  },
  "alignment": {
    "course_module": "Module name",
    "module_position": "Position within module",
    "learning_outcomes": ["Learning outcomes addressed"]
  },
  "segments": [
    {
      "id": "segment-1",
      "start_time": "00:00:00.630",
      "end_time": "00:02:15.250",
      "duration": 135.62,
      "text": "Segment text content...",
      "section": "Introduction",
      "subsection": "Course Overview",
      "keywords": ["keyword1", "keyword2"],
      "concepts": ["concept1", "concept2"],
      "relationships": ["concept1 is related to concept2"],
      "speaker": "Instructor"
    }
  ],
  "key_takeaways": ["Main takeaway 1", "Main takeaway 2"]
}
```

## Usage

```python
from core.agents.transcript_processor import TranscriptProcessor

# Initialize the processor
processor = TranscriptProcessor()

# Process a single transcript file
transcript_data = processor.process_transcript(
    "path/to/transcript.txt",
    course_context_data
)

# Process all transcripts in a directory
results = processor.process_all_transcripts(
    "path/to/transcripts/directory",
    course_context_data,
    "path/to/output/directory"
)
```

## Integration with Pipeline

The transcript processor is designed to work in the educational content pipeline:

1. It receives global course context extracted by the CourseContextExtractor
2. It processes transcript files and extracts structured information
3. It outputs data that can be used by downstream components like the slide processor and context fusion modules

## Fallback Behavior

If AI-powered processing fails, the processor falls back to basic transcript segmentation, which:

1. Preserves all timing information
2. Attempts basic alignment with course structure
3. Returns original transcript segments without advanced analysis
