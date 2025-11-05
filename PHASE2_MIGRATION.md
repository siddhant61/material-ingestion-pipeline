# Phase 2: Pipeline Orchestrator Migration

This document describes the migration from the procedural `run_enhanced_pipeline.py` script to the formal, class-based `MaterialIngestionPipeline` orchestrator.

## Overview

Phase 2 focuses on migrating the first step of the pipeline: **Course Context Extraction**. This is the foundation for the complete migration of all pipeline functionality into modular, reusable agents.

## Changes Made

### 1. Configuration Module (`core/config.py`)

Created a centralized configuration system that:
- Loads settings from environment variables (`.env` file)
- Provides sensible defaults for all configuration values
- Externalizes all hardcoded paths and model settings
- Ensures all necessary directories exist on initialization

**Key Features:**
- `Settings` class for centralized configuration
- Support for environment variable overrides
- Automatic directory creation
- `to_dict()` method for easy passing to agents

### 2. Context Agent (`core/agents/context_agent.py`)

Created a new `ContextAgent` class that:
- Inherits from `BaseAgent` following the standardized agent architecture
- Implements all required abstract methods
- Migrates the logic from the `extract_course_context` function in `run_enhanced_pipeline.py`
- Supports both PDF and Markdown course information files
- Includes the `_save_fallback_context` helper as a private method
- Uses lazy initialization for DocumentAnalyzer (only when needed for PDF processing)

**Agent Components:**
- **Models**: Uses `CourseContextExtractor` for AI-based context extraction
- **Memory**: Uses `DataManager` for persistent state tracking
- **Orchestration**: Manages input/output directories and file discovery
- **Reasoning**: Delegates to `CourseContextExtractor` for intelligent extraction
- **Tools**: Lazily initializes `DocumentAnalyzer` for PDF processing

### 3. Main Entry Point (`main.py`)

Created a new main entry point that:
- Replaces `run_enhanced_pipeline.py` as the primary entry point
- Uses the formal `MaterialIngestionPipeline` orchestrator
- Registers the `ContextAgent` for the "course_context" stage
- Sets the execution plan to run only course context extraction
- Provides detailed logging and result reporting

## Usage

### Prerequisites

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your OpenAI API key:
   ```bash
   # Copy the example .env file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=your-api-key-here
   ```

### Running the Pipeline

Execute the new main entry point:

```bash
python main.py
```

This will:
1. Initialize the Material Ingestion Pipeline
2. Create and register the Context Agent
3. Execute only the course context extraction stage
4. Save results to `output/course_context/`
5. Generate a pipeline results JSON file in `output/`

### Testing the Structure

To validate the pipeline structure without requiring an API key:

```bash
python test_pipeline_structure.py
```

This runs a comprehensive test suite that validates:
- Configuration loading
- Pipeline initialization
- Agent structure
- Agent registration
- Execution plan setup

## File Organization

```
material-ingestion-pipeline/
├── core/
│   ├── config.py                    # NEW: Centralized configuration
│   ├── agents/
│   │   ├── base_agent.py           # Base agent class (existing)
│   │   ├── context_agent.py        # NEW: Context extraction agent
│   │   └── ...
│   └── pipeline/
│       └── material_ingestion_pipeline.py  # Existing pipeline orchestrator
├── main.py                          # NEW: Primary entry point
├── .env.example                     # NEW: Environment variables template
├── test_pipeline_structure.py       # NEW: Structure validation tests
├── run_enhanced_pipeline.py         # OLD: To be deprecated
└── ...
```

## Migration Status

### Completed
- ✅ Configuration externalization
- ✅ ContextAgent implementation
- ✅ Main.py entry point
- ✅ Course context extraction migration
- ✅ Structure validation tests

### Pending (Future Phases)
- ⏳ Transcript processing agent
- ⏳ Slide processing agent
- ⏳ Context fusion agent
- ⏳ Supervisor agent
- ⏳ Knowledge graph generation agent
- ⏳ Embedding generation agent
- ⏳ Visualization agent

## Key Benefits

1. **Modularity**: Each pipeline stage is now a self-contained agent
2. **Reusability**: Agents can be used independently or in different combinations
3. **Testability**: Agents can be tested in isolation
4. **Configuration**: All settings are centralized and configurable
5. **Extensibility**: New agents can be added without modifying existing code
6. **Error Handling**: Standardized error handling through BaseAgent
7. **Monitoring**: Built-in execution metadata and progress tracking

## Comparison: Old vs New

### Old Approach (run_enhanced_pipeline.py)
```python
# Procedural, hardcoded paths
course_info_dir = script_dir / "input" / "course_material" / "course_info"
course_context = extract_course_context(course_info_dir)
```

### New Approach (main.py)
```python
# Class-based, configurable, orchestrated
from core.config import settings
from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
from core.agents.context_agent import ContextAgent

pipeline = MaterialIngestionPipeline(config=pipeline_config)
context_agent = ContextAgent(config=settings.to_dict())
pipeline.register_agent("course_context", context_agent)
pipeline.set_execution_plan(["course_context"])
results = pipeline.run(input_data)
```

## Next Steps

The next phase will migrate the transcript processing functionality by:
1. Creating a `TranscriptAgent` class
2. Registering it with the pipeline
3. Extending the execution plan to include transcript processing
4. Testing the multi-stage pipeline execution

## Configuration Reference

See `.env.example` for all available configuration options:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `INPUT_DIR`: Input directory path (default: `input`)
- `OUTPUT_DIR`: Output directory path (default: `output`)
- `DATA_DIR`: Data storage directory (default: `output/data`)
- `DEFAULT_MODEL`: Default AI model (default: `gpt-4o-mini`)
- `COURSE_CONTEXT_MODEL`: Model for context extraction (default: uses DEFAULT_MODEL)
- `MODEL_TEMPERATURE`: Model temperature parameter (default: `0.2`)
- `MODEL_MAX_TOKENS`: Maximum tokens for model responses (default: `4000`)

## Troubleshooting

### API Key Issues
If you see `OpenAIError: The api_key client option must be set`:
1. Ensure `.env` file exists in the project root
2. Verify `OPENAI_API_KEY` is set in `.env`
3. Check that the API key is valid

### Import Errors
If you see `ModuleNotFoundError`:
1. Ensure you're in the project root directory
2. Install all dependencies: `pip install -r requirements.txt`
3. Verify Python path includes the project root

### Directory Not Found
If you see directory-related errors:
- The configuration module automatically creates necessary directories
- Ensure you have write permissions in the project directory

## Contributing

When adding new agents:
1. Inherit from `BaseAgent`
2. Implement all required abstract methods
3. Get configuration from the `config` parameter
4. Register the agent with a descriptive stage name
5. Add the stage to the execution plan
6. Update this documentation
