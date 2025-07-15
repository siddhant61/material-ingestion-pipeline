# Local Context: Codebase Analysis & Reorganization Plan

## Current Codebase Structure

### Main Components

1. **Entry Points**:
   - `ingestion_pipeline.py`: Main orchestration script (1461 lines)
   - `run_course_material_pipeline.py`: Runner script (372 lines)

2. **Agent Architecture**:
   - `agents/base_agent.py`: Base classes for all agents (304 lines)
   - Individual agent modules in `agents/` directory

3. **Agent Modules**:
   - Document Loader Agent (`agents/document_loader/`)
   - Transcript Agent (`agents/transcript/`)
   - Context Extraction Agent (`agents/context_extraction/`)
   - Vision Model Agent (`agents/vision_model/`)
   - Targeted Image Extraction Agent (`agents/targeted_image_extraction/`)
   - Embedding Agent (`agents/embedding/`)
   - Concept Extraction Agent (`agents/concept_extraction/`)
   - Graph Builder Agent (`agents/graph_builder/`)
   - Coordinator Agent (`agents/coordinator/`)
   - Supervisor Agent (`agents/supervisor/`)
   - Vector Storage Agent (`agents/vector_storage/`)

4. **Infrastructure**:
   - `utils/`: Common utility functions
   - `config/`: Pipeline configuration
   - `input/`, `output/`, `data/`: Data directories

## Issues & Improvement Areas

1. **Inconsistent Implementation**: Varied levels of development across agents
2. **Limited AI Assistant Integration**: Framework exists but implementation is limited
3. **Monolithic Pipeline Class**: Too many responsibilities in main pipeline class
4. **Error Handling**: Basic structure exists but needs robustness
5. **Data Flow Management**: Needs clearer definitions between agents
6. **Testing Infrastructure**: Limited testing capabilities
7. **Documentation**: Varying documentation quality

## Reorganization Plan

### Core Infrastructure Enhancements

1. **Modularize Pipeline Architecture**:
   - Create a core pipeline module
   - Implement plugin-based agent architecture
   - Define clear inter-agent interfaces

2. **Standardize Agent Framework**:
   - Enforce consistent input/output contracts
   - Standardize error reporting
   - Implement comprehensive logging

3. **Enhance AI Assistant Integration**:
   - Create standardized assistant base class
   - Implement chain-of-thought reasoning patterns
   - Upgrade to GPT-4o-mini

### Agent-Specific Enhancements

1. **Document Loader Agent**:
   - Enhance OCR capabilities
   - Add document type classification
   - Implement adaptive extraction

2. **Graph Builder Agent**:
   - Refine knowledge graph schema
   - Implement hierarchical structure
   - Add rich relationship types

3. **Vector Storage Agent**:
   - Optimize embedding strategies
   - Implement efficient storage and retrieval
   - Add similarity search capabilities

### Implementation Phases

1. **Phase 1**: Core infrastructure restructuring
   - Modularize pipeline architecture
   - Standardize agent interfaces
   - Implement error handling framework

2. **Phase 2**: Document Loader Agent enhancement
   - Integration of AI assistants
   - Adaptive extraction techniques
   - Document type classification

3. **Phase 3**: Transcript and Context Extraction enhancement
   - Semantic chunking improvements
   - Enhanced context extraction

4. **Phase 4**: Knowledge Graph and Vector Storage enhancement
   - Hierarchical structure implementation
   - Optimization of vector storage

5. **Phase 5**: Integration and testing
   - End-to-end pipeline validation
   - Performance optimization
   - Documentation updates

This context will be updated as the implementation progresses.
