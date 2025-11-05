# Quick Start Guide - Phase 2 Migration

This guide helps you get started with the newly migrated pipeline architecture.

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your-api-key-here
```

### Step 3: Run the Pipeline
```bash
# Run the new pipeline
python main.py

# Or test the structure without API key
python test_pipeline_structure.py
```

## 📋 What's New?

Phase 2 introduces a **modular, class-based architecture** for the material ingestion pipeline:

### Before (Old Way)
```bash
python run_enhanced_pipeline.py  # Procedural script with hardcoded values
```

### After (New Way)
```bash
python main.py  # Orchestrated pipeline with configurable agents
```

## 🏗️ New Architecture

```
MaterialIngestionPipeline (Orchestrator)
    ↓
ContextAgent (inherits from BaseAgent)
    ↓
CourseContextExtractor (AI-powered extraction)
```

## 📁 New Files

1. **`core/config.py`** - Centralized configuration
2. **`core/agents/context_agent.py`** - Context extraction agent
3. **`main.py`** - New entry point
4. **`.env.example`** - Environment variable template
5. **`test_pipeline_structure.py`** - Validation tests

## 🎯 Key Benefits

- ✅ **Modular**: Each stage is a separate agent
- ✅ **Configurable**: All settings via environment variables
- ✅ **Testable**: Each component tested independently
- ✅ **Reusable**: Agents can be used in different contexts
- ✅ **Extensible**: Easy to add new agents

## 🔍 Verify Installation

Run the structure tests to ensure everything is set up correctly:

```bash
python test_pipeline_structure.py
```

Expected output:
```
Tests passed: 5/5
✓ All tests passed!
```

## 📖 Documentation

- **`PHASE2_MIGRATION.md`** - Detailed migration guide
- **`COMPARISON.md`** - Before/after comparison
- **`README.md`** - Original project documentation

## 🛠️ Configuration Options

Edit `.env` to customize:

```bash
# Required
OPENAI_API_KEY=your-api-key-here

# Optional (with defaults)
INPUT_DIR=input
OUTPUT_DIR=output
DEFAULT_MODEL=gpt-4o-mini
MODEL_TEMPERATURE=0.2
```

See `.env.example` for all options.

## 🧪 Testing Without API Key

You can validate the pipeline structure without an OpenAI API key:

```bash
python test_pipeline_structure.py
```

This tests:
- Configuration loading
- Pipeline initialization
- Agent structure
- Agent registration
- Execution plan setup

## 📊 Expected Output

When you run `python main.py` with a valid API key:

```
================================================================================
Material Ingestion Pipeline - Course Context Extraction
================================================================================
INFO - Initializing Material Ingestion Pipeline...
INFO - Initializing Context Agent...
INFO - Registering Context Agent with pipeline...
INFO - Setting execution plan...
INFO - Starting pipeline execution...
--------------------------------------------------------------------------------
INFO - Executing stage 1/1: course_context
INFO - Extracting course context from [path]
INFO - Course context extracted and saved to [output file]
--------------------------------------------------------------------------------
INFO - Pipeline execution completed!
Status: success
Course title: [Extracted Title]
================================================================================
```

## 🚧 Troubleshooting

### "OpenAI API key not set"
Make sure `.env` exists and contains `OPENAI_API_KEY=your-key`

### "ModuleNotFoundError"
Run `pip install -r requirements.txt`

### "No course info files found"
Place a `.md` or `.pdf` course info file in `input/course_material/course_info/`

## 🎓 Example Course Info

A sample markdown file is included at:
```
input/course_material/course_info/sample_course.md
```

## 📞 Next Steps

1. ✅ Run `python test_pipeline_structure.py` to verify setup
2. ✅ Add your OpenAI API key to `.env`
3. ✅ Place course materials in `input/course_material/course_info/`
4. ✅ Run `python main.py` to execute the pipeline
5. ✅ Check `output/course_context/` for results

## 🔜 Coming Soon

Future phases will add more agents following the same pattern:
- **Phase 3**: Transcript processing
- **Phase 4**: Slide processing
- **Phase 5**: Context fusion
- **Phase 6**: Supervisor
- **Phase 7**: Knowledge graph
- **Phase 8**: Visualization

Each new agent will be registered with the pipeline and extend the execution plan.

---

**Questions?** See `PHASE2_MIGRATION.md` for detailed documentation.
