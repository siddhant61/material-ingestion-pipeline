# Before and After: Pipeline Migration Comparison

This document provides a side-by-side comparison of the old procedural approach versus the new class-based orchestrator approach.

## Overview

### Old Approach: `run_enhanced_pipeline.py`
- Procedural script with hardcoded paths
- Functions called sequentially in the script
- Configuration scattered throughout the code
- Difficult to test individual components
- Limited reusability

### New Approach: `main.py` + `MaterialIngestionPipeline`
- Class-based agents inheriting from `BaseAgent`
- Orchestrated execution through `MaterialIngestionPipeline`
- Centralized configuration in `core/config.py`
- Easy to test individual agents
- Highly modular and reusable

## Code Comparison

### Configuration

#### Old (run_enhanced_pipeline.py)
```python
# Hardcoded paths scattered in the script
script_dir = Path(__file__).parent.absolute()
input_dir = script_dir / "input"
output_dir = script_dir / "output"
course_info_dir = input_dir / "course_material" / "course_info"
transcripts_dir = input_dir / "course_material" / "transcripts"
slides_dir = input_dir / "course_material" / "slides"

# Hardcoded in function calls
document_analyzer = DocumentAnalyzer()  # Uses default model
course_context_extractor = CourseContextExtractor()  # Uses default model
```

#### New (core/config.py + .env)
```python
# Centralized configuration with environment variable support
class Settings:
    def __init__(self):
        # Load from environment or use defaults
        self.input_dir = Path(os.getenv("INPUT_DIR", str(self.project_root / "input")))
        self.output_dir = Path(os.getenv("OUTPUT_DIR", str(self.project_root / "output")))
        self.course_info_dir = self.input_dir / "course_material" / "course_info"
        self.course_context_model = os.getenv("COURSE_CONTEXT_MODEL", self.default_model)
        # ... all configuration in one place

# Usage
from core.config import settings
# All paths and settings available through settings object
```

### Course Context Extraction

#### Old (run_enhanced_pipeline.py)
```python
def extract_course_context(course_info_path):
    """Extract global context from course information document."""
    logger.info(f"Extracting course context from {course_info_path}")
    
    try:
        # Check if the path is a directory or file
        if course_info_path.is_dir():
            markdown_files = list(course_info_path.glob("*.md"))
            pdf_files = list(course_info_path.glob("*.pdf"))
            
            if markdown_files:
                course_file = markdown_files[0]
                is_markdown = True
            elif pdf_files:
                course_file = pdf_files[0]
                is_markdown = False
            else:
                raise FileNotFoundError(f"No markdown or PDF files found")
        
        # Initialize components
        document_analyzer = DocumentAnalyzer()
        course_context_extractor = CourseContextExtractor()
        
        # Process document...
        if is_markdown:
            with open(course_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            # Create metadata...
        else:
            pdf_document, basic_metadata = document_analyzer.load_pdf(str(course_file))
            text_content = document_analyzer.extract_text(pdf_document)
        
        # Extract and save context
        course_context = course_context_extractor.extract_course_context(
            text_content, basic_metadata
        )
        
        # Save to file
        context_file = output_dir / "course_context" / f"course_context_{timestamp}.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(course_context, f, ensure_ascii=False, indent=2)
        
        # Store in data manager
        data_manager.store_agent_output("course_context", course_context, pipeline_run_id)
        
        return course_context
    except Exception as e:
        # Error handling with fallback context...
        fallback_context = {...}
        _save_fallback_context(fallback_context)
        return fallback_context

# Call the function
course_context = extract_course_context(course_info_dir)
```

#### New (core/agents/context_agent.py)
```python
class ContextAgent(BaseAgent):
    """Agent responsible for extracting course context."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configuration."""
        super().__init__(config)
    
    def _init_models(self):
        """Initialize the model component."""
        model_name = self.config.get("course_context_model", "gpt-4o-mini")
        self.course_context_extractor = CourseContextExtractor(model_name=model_name)
    
    def _init_memory(self):
        """Initialize the memory component."""
        base_data_dir = self.config.get("data_dir", "output/data")
        self.data_manager = DataManager({"base_data_dir": base_data_dir})
        self.pipeline_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _init_orchestration(self):
        """Initialize orchestration component."""
        self.course_info_dir = Path(self.config.get("course_info_dir"))
        self.output_dir = Path(self.config.get("course_context_dir"))
        self.course_info_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_reasoning(self):
        """Reasoning handled by CourseContextExtractor."""
        pass
    
    def _init_tools(self):
        """Initialize tools (lazily)."""
        self.document_analyzer = None  # Lazy initialization
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the course context extraction."""
        try:
            course_info_path = input_data.get("course_info_path", self.course_info_dir)
            course_context = self._extract_course_context(Path(course_info_path))
            context_file = self._save_course_context(course_context)
            self.data_manager.store_agent_output("course_context", course_context, self.pipeline_run_id)
            
            return {
                "status": "success",
                "output_type": "course_context",
                "result": course_context,
                "output_file": str(context_file),
                "summary": f"Successfully extracted course context",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            fallback_context = self._create_fallback_context(str(e), course_info_path)
            context_file = self._save_fallback_context(fallback_context)
            return {
                "status": "warning",
                "output_type": "course_context",
                "result": fallback_context,
                "output_file": str(context_file),
                "summary": f"Used fallback context due to error",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_course_context(self, course_info_path: Path) -> Dict[str, Any]:
        """Internal method for extraction logic (same logic as old function)."""
        # ... (implementation details)
    
    def _save_course_context(self, course_context: Dict[str, Any]) -> Path:
        """Save extracted context."""
        # ... (implementation details)
    
    def _create_fallback_context(self, error_message: str, course_info_path: Path) -> Dict[str, Any]:
        """Create fallback context on error."""
        # ... (implementation details)
    
    def _save_fallback_context(self, fallback_context: Dict[str, Any]) -> Path:
        """Save fallback context."""
        # ... (implementation details)

# Usage with pipeline
from core.config import settings
from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
from core.agents.context_agent import ContextAgent

pipeline = MaterialIngestionPipeline(config=pipeline_config)
context_agent = ContextAgent(config=settings.to_dict())
pipeline.register_agent("course_context", context_agent)
pipeline.set_execution_plan(["course_context"])
results = pipeline.run(input_data)
```

### Main Execution

#### Old (run_enhanced_pipeline.py)
```python
# At the bottom of the script
if __name__ == "__main__":
    # Fix templates
    run_template_fixes()
    
    # Extract course context
    course_context = extract_course_context(course_info_dir)
    
    # Process transcripts
    transcript_data = process_transcripts(transcripts_dir, course_context)
    
    # Process slides
    slide_data = process_slides(slides_dir, course_context)
    
    # ... more procedural steps
```

#### New (main.py)
```python
from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
from core.agents.context_agent import ContextAgent
from core.config import settings

def main():
    # Create pipeline configuration
    pipeline_config = {
        "pipeline_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "version": settings.pipeline_version,
        "input_dir": str(settings.input_dir),
        "output_dir": str(settings.output_dir),
        "data_dir": str(settings.data_dir),
    }
    
    # Initialize pipeline
    pipeline = MaterialIngestionPipeline(config=pipeline_config)
    
    # Initialize and register agents
    context_agent = ContextAgent(config=settings.to_dict())
    pipeline.register_agent("course_context", context_agent)
    
    # Future agents would be registered here:
    # transcript_agent = TranscriptAgent(config=settings.to_dict())
    # pipeline.register_agent("transcripts", transcript_agent)
    
    # Set execution plan
    pipeline.set_execution_plan(["course_context"])
    
    # Run pipeline
    input_data = {
        "input_dir": str(settings.input_dir),
        "course_info_path": str(settings.course_info_dir),
    }
    results = pipeline.run(input_data)
    
    # Results include metadata, stage outputs, and execution time
    return results

if __name__ == "__main__":
    main()
```

## Key Improvements

### 1. Modularity
**Old:** Everything in one large script
**New:** Separate modules for configuration, agents, and orchestration

### 2. Reusability
**Old:** Functions tightly coupled to the script
**New:** Agents can be reused in different contexts

### 3. Testability
**Old:** Hard to test individual components
**New:** Each agent can be tested in isolation

```python
# Easy to test the agent independently
def test_context_agent():
    config = {"course_info_dir": "test/data", "course_context_model": "gpt-4o-mini"}
    agent = ContextAgent(config=config)
    input_data = {"course_info_path": "test/data/sample.md"}
    result = agent.run(input_data)
    assert result["status"] == "success"
```

### 4. Configuration Management
**Old:** Hardcoded values scattered throughout
**New:** Centralized in `core/config.py` with environment variable support

### 5. Error Handling
**Old:** Try-except in each function
**New:** Standardized through `BaseAgent.run_with_error_handling()`

### 6. Metadata and Monitoring
**Old:** Manual logging
**New:** Built-in execution metadata

```python
results = pipeline.run(input_data)
# Automatically includes:
# - Execution time per stage
# - Total pipeline execution time
# - Stage status and outputs
# - Error information if any
```

### 7. Extensibility
**Old:** Add new step = modify the main script
**New:** Add new step = create new agent and register it

```python
# Adding a new agent is simple:
class NewAgent(BaseAgent):
    # Implement required methods...
    pass

# Register and use
pipeline.register_agent("new_stage", NewAgent(config))
pipeline.set_execution_plan(["course_context", "new_stage"])
```

## Benefits Summary

| Aspect | Old Approach | New Approach |
|--------|-------------|--------------|
| **Code Organization** | Single large file | Modular architecture |
| **Configuration** | Hardcoded | Centralized + environment variables |
| **Testability** | Difficult | Easy with unit tests |
| **Reusability** | Low | High |
| **Extensibility** | Modify main script | Add new agents |
| **Error Handling** | Manual in each function | Standardized through base class |
| **Monitoring** | Manual logging | Built-in metadata |
| **Flexibility** | Fixed execution order | Configurable execution plan |
| **Maintainability** | Decreases over time | Stays consistent |

## Migration Path

1. **Phase 1**: Configuration externalization ✅
2. **Phase 2**: Course context extraction (Current) ✅
3. **Phase 3**: Transcript processing
4. **Phase 4**: Slide processing
5. **Phase 5**: Context fusion
6. **Phase 6**: Supervisor agent
7. **Phase 7**: Knowledge graph generation
8. **Phase 8**: Visualization

Each phase adds a new agent while maintaining backward compatibility. The old `run_enhanced_pipeline.py` can coexist until all functionality is migrated.

## Running the New System

```bash
# Setup
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run
python main.py

# Test structure
python test_pipeline_structure.py
```

## Next Steps

After completing the course context extraction migration, the next step is to create a `TranscriptAgent` following the same pattern:

1. Create `core/agents/transcript_agent.py`
2. Inherit from `BaseAgent`
3. Migrate logic from `process_transcripts()` function
4. Register with pipeline
5. Extend execution plan
6. Test and validate

The pattern is now established and repeatable for all remaining pipeline stages.
