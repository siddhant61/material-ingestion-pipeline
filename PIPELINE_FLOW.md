# Material Ingestion Pipeline - Complete Data Flow

## Pipeline Architecture (After Phase 7)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MATERIAL INGESTION PIPELINE                              │
│                          (main.py orchestration)                             │
└─────────────────────────────────────────────────────────────────────────────┘

INPUT FILES                     AGENTS                           OUTPUT FILES
═══════════                     ══════                           ════════════

┌─────────────┐
│ Course Info │
│   (.md)     │──────────┐
└─────────────┘          │
                         │     ┌─────────────────┐         ┌──────────────────┐
                         └────▶│ ContextAgent    │────────▶│ course_context/  │
                               │ (Stage 1)       │         │  context.json    │
                               └─────────────────┘         └──────────────────┘
                                       │
                                       │ result_from_course_context
                                       ▼
┌─────────────┐              ┌─────────────────┐         ┌──────────────────┐
│ Transcripts │──────────────▶│TranscriptAgent  │────────▶│ transcripts/     │
│   (.txt)    │              │ (Stage 2)       │         │  processed.json  │
└─────────────┘              └─────────────────┘         └──────────────────┘
                                       │
                                       │ result_from_process_transcripts
                                       ▼
┌─────────────┐              ┌─────────────────┐         ┌──────────────────┐
│   Slides    │──────────────▶│  SlideAgent     │────────▶│ slides/          │
│   (.pdf)    │              │ (Stage 3)       │         │  processed.json  │
└─────────────┘              └─────────────────┘         └──────────────────┘
                                       │
                                       │ result_from_process_slides
                                       ▼
                               ┌─────────────────┐         ┌──────────────────┐
                               │  FusionAgent    │────────▶│ fused_context/   │
                               │ (Stage 4)       │         │  fused.json      │
                               └─────────────────┘         └──────────────────┘
                                       │
                                       │ result_from_context_fusion
                                       ▼
                               ┌─────────────────┐         ┌──────────────────┐
                               │ SupervisionOr-  │────────▶│ supervision/     │
                               │ chestratorAgent │         │  refined.json    │
                               │ (Stage 5)       │         └──────────────────┘
                               └─────────────────┘
                                       │
                                       │ result_from_supervision
                                       │   ├─ refined course_context
                                       │   ├─ refined transcript_processor
                                       │   ├─ refined slide_processor
                                       │   └─ refined context_fusion ◄──── EXTRACTED
                                       ▼
                               ┌─────────────────┐         ┌──────────────────┐
                               │ KnowledgeGraph  │────────▶│ knowledge_graph/ │
                               │     Agent       │         │    graph.json    │
                               │ (Stage 6) ★NEW★ │         └──────────────────┘
                               └─────────────────┘
                                       │
                                       │ Final Knowledge Graph
                                       ▼
                               ┌─────────────────┐
                               │  COMPLETE!      │
                               │  Knowledge      │
                               │  Graph Ready    │
                               └─────────────────┘
```

## Data Flow Details

### Stage 1: ContextAgent
**Input**: Course info files (markdown or PDF)
**Process**: Extract global course context (title, objectives, structure)
**Output**: `result_from_course_context` containing course metadata

### Stage 2: TranscriptAgent  
**Input**: 
- Transcript files (.txt, .vtt)
- `result_from_course_context` (for context-aware processing)

**Process**: Process transcripts with course context awareness
**Output**: `result_from_process_transcripts` with structured transcript data

### Stage 3: SlideAgent
**Input**:
- Slide files (.pdf)
- `result_from_course_context`
- `result_from_process_transcripts`

**Process**: Extract content from slides with full context
**Output**: `result_from_process_slides` with slide content

### Stage 4: FusionAgent
**Input**:
- `result_from_course_context`
- `result_from_process_transcripts`
- `result_from_process_slides`

**Process**: Fuse all contexts into unified representation
**Output**: `result_from_context_fusion` with integrated data

### Stage 5: SupervisionOrchestratorAgent
**Input**: All previous stage results
**Process**: Quality check and refine all outputs
**Output**: `result_from_supervision` with refined versions of all data

### Stage 6: KnowledgeGraphAgent ★ NEW ★
**Input**: `result_from_supervision["result"]["context_fusion"]`
**Process**: Generate hierarchical knowledge graph
**Output**: 
- Knowledge graph with entities and relationships
- Saved to `output/knowledge_graph/knowledge_graph.json`

## Agent Communication Protocol

Each agent follows a standard input/output format:

**Input Structure:**
```python
{
    "result_from_<previous_stage>": {
        "status": "success",
        "result": {...},  # Actual data
        "summary": "...",
        "output_type": "..."
    }
}
```

**Output Structure:**
```python
{
    "status": "success" | "error",
    "result": {...},  # Actual data
    "summary": "Human readable summary",
    "output_type": "...",  # Type identifier
    "metadata": {...}  # Optional metadata
}
```

## KnowledgeGraphAgent Specifics

### Input Data Path
```python
input_data["result_from_supervision"]["result"]["context_fusion"]
```

### Key Extraction Logic
```python
# Primary path (new format)
supervision_result["result"]["context_fusion"]

# Fallback path (direct access)
supervision_result["context_fusion"]
```

### Generated Knowledge Graph Structure
```json
{
    "entities": [
        {
            "id": "entity_id",
            "type": "concept|module|lesson|...",
            "name": "Entity Name",
            "description": "...",
            "hierarchy_level": "root|trunk|branch|leaf|resource",
            "properties": {...}
        }
    ],
    "relationships": [
        {
            "source": "entity_id_1",
            "target": "entity_id_2",
            "type": "contains|implements|applies|...",
            "properties": {...}
        }
    ],
    "hierarchy": {
        "root": [...],
        "trunk": [...],
        "branch": [...],
        "leaf": [...],
        "resource": [...]
    },
    "metadata": {
        "entity_count": 123,
        "relationship_count": 456,
        "generated_at": "2025-11-05T...",
        ...
    }
}
```

## Execution

To run the complete pipeline:

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run the pipeline
python main.py
```

The pipeline will execute all 6 stages sequentially, with each agent receiving the outputs of previous stages as input.

## Benefits of Agent Architecture

1. **Modularity**: Each stage is independent and reusable
2. **Testability**: Agents can be tested in isolation
3. **Maintainability**: Changes are localized to specific agents
4. **Extensibility**: New agents can be added easily
5. **Consistency**: All agents follow the same BaseAgent pattern
6. **Error Handling**: Standardized error responses
7. **Debugging**: Clear data flow makes issues easier to trace

## Migration Complete! 🎉

All core pipeline logic has been successfully migrated from `run_enhanced_pipeline.py` to the modular agent architecture. The system is now:
- ✅ Fully modular
- ✅ Independently testable
- ✅ Easy to extend
- ✅ Production-ready
