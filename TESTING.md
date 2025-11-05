# Testing Guide for Phase 3: Transcript Agent Migration

## Overview
This document provides testing instructions for the migrated ContextAgent and TranscriptAgent integration with the MaterialIngestionPipeline.

## Prerequisites

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Key dependencies:
- pydantic
- pydantic-settings
- langchain
- langchain-core
- langchain-openai

### 2. Set Up Environment Variables
Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
```

## Testing Steps

### Step 1: Basic Execution Test
Run the main pipeline:
```bash
python main.py
```

Expected behavior:
1. Creates sample course_info.md and transcript files if they don't exist
2. Runs ContextAgent to extract course context
3. Runs TranscriptAgent to process transcripts with the context
4. Saves results to output directory

### Step 2: Verify Output Files

Check that the following files are created:

```bash
# Course context output
ls -l output/course_context/
# Should contain: course_context_<timestamp>.json

# Transcript processing output
ls -l output/transcripts/
# Should contain: processed transcript files

# Pipeline results
ls -l output/
# Should contain: transcript_results.json and pipeline_results_<timestamp>.json
```

### Step 3: Verify Data Flow

Examine the pipeline results file:
```bash
cat output/pipeline_results_*.json | jq '.stage_outputs'
```

Expected structure:
```json
{
  "course_context": {
    "status": "success",
    "output_type": "course_context",
    "result": { ... },
    "summary": "Extracted course context from ..."
  },
  "process_transcripts": {
    "status": "success",
    "output_type": "transcript_processing",
    "result": { ... },
    "summary": "Processed N transcript files"
  }
}
```

### Step 4: Test with Custom Course Materials

1. Add your own course info file:
```bash
cp your_course_info.pdf input/course_material/course_info/
```

2. Add transcript files:
```bash
cp your_transcripts/* input/course_material/transcripts/
```

3. Run the pipeline again:
```bash
python main.py
```

## Validation Checks

### 1. Agent Registration
Verify in the logs:
```
Registered ContextAgent for stage: course_context
Registered TranscriptAgent for stage: process_transcripts
```

### 2. Execution Order
Verify in the logs:
```
Executing stage 1/2: course_context
Executing stage 2/2: process_transcripts
```

### 3. Data Passing
Verify in the transcript agent logs:
```
Course context received from previous agent
```

### 4. Success Indicators
Final logs should show:
```
Status: success
Total execution time: X.XX seconds
```

## Troubleshooting

### Issue: Module not found errors
**Solution:** Install missing dependencies:
```bash
pip install <missing_module>
```

### Issue: No course materials found
**Solution:** The pipeline will auto-create sample files. Check:
```bash
ls -l input/course_material/course_info/
ls -l input/course_material/transcripts/
```

### Issue: OpenAI API errors
**Solution:** 
1. Check .env file has valid OPENAI_API_KEY
2. Verify API key has sufficient credits
3. Check network connectivity to OpenAI

### Issue: Pipeline fails at transcript processing
**Solution:**
1. Check that course context was extracted successfully
2. Verify transcript files are in correct format (WebVTT)
3. Check output/transcript_results.json for specific errors

## Manual Verification

### Verify ContextAgent Output
```bash
cat output/course_context/course_context_*.json | jq '.'
```

Should contain:
- title
- description
- objectives
- learning_outcomes
- structure
- metadata

### Verify TranscriptAgent Output
```bash
cat output/transcript_results.json | jq '.'
```

Should contain:
- processed_count
- files (array of processed files)
- timestamps
- status information

## Integration Testing

### Test 1: Empty Input Directory
1. Clear input directory
2. Run pipeline
3. Verify sample files are created
4. Verify pipeline completes successfully

### Test 2: Invalid Course Info
1. Add an empty or corrupted file to course_info/
2. Run pipeline
3. Verify fallback context is created
4. Verify pipeline continues to transcript processing

### Test 3: No Transcripts
1. Remove all transcript files
2. Run pipeline
3. Verify course context is extracted
4. Verify transcript agent handles empty directory gracefully

## Performance Benchmarks

Expected execution times (approximate):
- Course context extraction: 10-30 seconds
- Transcript processing: Variable based on number and length of transcripts
- Total pipeline: 30-120 seconds for typical course

## Code Quality Checks

### Syntax Validation
```bash
python -m py_compile core/agents/context_agent.py
python -m py_compile core/agents/transcript_agent.py
python -m py_compile main.py
```

### Import Validation
```bash
python -c "from core.agents.context_agent import ContextAgent; print('ContextAgent OK')"
python -c "from core.agents.transcript_agent import TranscriptAgent; print('TranscriptAgent OK')"
```

## Success Criteria

The implementation is successful if:
1. ✓ Both agents are properly registered with the pipeline
2. ✓ ContextAgent extracts course context
3. ✓ TranscriptAgent receives course context from ContextAgent
4. ✓ TranscriptAgent processes all transcript files
5. ✓ Pipeline completes without errors
6. ✓ Output files are created in correct locations
7. ✓ Data flow between agents is verified
8. ✓ Execution plan runs in correct order

## Next Steps

After successful testing:
1. Review output quality
2. Add additional agents to the pipeline (slides, fusion, etc.)
3. Implement error recovery mechanisms
4. Add unit tests for individual agents
5. Create integration tests for full pipeline
