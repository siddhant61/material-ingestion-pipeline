# Knowledge Graph Generation for Educational Content

This project processes educational materials and creates a hierarchical knowledge graph with rich metadata and visualizations.

## Overview

The material ingestion pipeline processes course materials (PDFs, transcripts, slides) and generates:

1. A hierarchical knowledge graph representing the educational content
2. Interactive and static visualizations of the knowledge graph
3. Vector embeddings for semantic search and retrieval

## Enhanced Knowledge Graph Features

### Hierarchical Structure

The knowledge graph is organized in a tree-like structure with multiple levels:

- **Roots**: Domain, field, subject areas (foundation of knowledge)
- **Trunk**: Major theories, principles, frameworks
- **Branches**: Supporting concepts, methods, techniques
- **Leaves/Fruits**: Practical applications, examples, implementations
- **Resources**: Supporting definitions, visualizations, references

### Information Source Tracking

Entities in the knowledge graph are color-coded based on their information source:

- **Course Materials**: Content extracted directly from course documents
- **Transcripts**: Information from lecture transcripts
- **Slides**: Content from presentation slides
- **RAG**: Information added through Retrieval-Augmented Generation
- **Visual RAG**: Content derived from visual recognition
- **External**: Information from additional external sources

### Temporal Information

Knowledge graph entities include temporal data indicating:

- **Origin Year**: When concepts were first introduced
- **Historical Period**: Ancient, Medieval, Renaissance, Classical, Modern, Contemporary, Recent
- **Chronological Relationships**: How concepts evolved over time

### Additional Metadata

Entities are enriched with:

- **Definitions**: Formal definitions of concepts
- **Visual Representations**: Links to related visual content
- **Educational Resources**: Supporting materials for teaching
- **References**: Citations and external resources

## Knowledge Graph Visualization

### Interactive Visualization

The interactive HTML visualization provides:

- **Hierarchical Layout**: Tree-like structure showing relationships between concepts
- **Color Coding**:
  - Node borders by information source
  - Node fill by hierarchy level
- **Visual Differentiation**:
  - Different shapes for different hierarchy levels
  - Size variations based on concept importance
- **Rich Tooltips**: Detailed information on hover including definitions and temporal data
- **Legend**: Interactive legend explaining colors and shapes
- **Navigation**: Pan, zoom, and select features for exploring the graph

### Static Visualization

The static PNG visualization offers:

- **Hierarchical Layout**: Organized by knowledge level
- **Color Scheme**: Consistent with the interactive visualization
- **Legend**: Comprehensive legend for interpretation
- **High Resolution**: Suitable for presentations and documentation

## Usage

### Running the Pipeline

To process educational materials and generate the knowledge graph:

```bash
# On Windows
.\install_and_run.bat

# On Unix-based systems
./install_and_run.sh
```

### Run with Visualization

To run the pipeline and automatically open the visualization:

```bash
python run_and_visualize.py
```

### Run Specific Components

To run specific components of the pipeline:

```bash
python run_component.py <component_name>
```

Available components:

- `fix`: Run only the `fix_pipeline_issues.py` script
- `context`: Extract course context only
- `transcripts`: Process transcripts only
- `slides`: Process slides only
- `fusion`: Generate fused context only
- `supervise`: Supervise outputs only
- `knowledge_graph`: Generate knowledge graph only
- `visualize`: Create visualizations from existing knowledge graph only
- `embeddings`: Generate embeddings from existing knowledge graph only
- `all`: Run the complete pipeline

### Viewing Visualizations

After running the pipeline:

1. Open `output/visualizations/knowledge_graph_interactive.html` in a web browser to explore the interactive visualization
2. View `output/visualizations/knowledge_graph_static.png` for the static visualization

### Accessing the Knowledge Graph Data

The raw knowledge graph data is available at:

- `output/knowledge_graph/knowledge_graph.json`

## Integration with Vision & Mood-Board Creation

The knowledge graph and embeddings serve as the foundation for the next step in the educational content pipeline. To prepare the resources for the Vision & Mood-Board Creation pipeline:

```bash
python prepare_for_vision_board.py
```

This script creates an optimized resource pool in `output/vision_board_input/vision_board_input.json` that includes:

1. **Hierarchical Knowledge Structure**: Categorized entities for structured mood board creation
2. **Key Entity Identification**: Most important concepts based on connectivity
3. **Visual Resource Index**: Pre-indexed visual materials for each entity type
4. **Conceptual Relationships Map**: Entity relationship network for spatial organization
5. **Temporal Progression**: Time-ordered concepts for chronological mood boards
6. **Complete Knowledge Graph**: Full graph data for comprehensive processing
7. **Entity Embeddings**: Vector representations for semantic similarity

The Vision & Mood-Board Creation pipeline can use this resource pool to:

- Generate structured mood boards based on the hierarchical organization
- Ensure proper attribution through source tracking
- Create historically accurate progression through temporal information
- Enrich mood boards with definitions and resources
- Establish thematic connections using semantic relationships

## Directory Structure

```txt
.
├── input/
│   └── course_material/
│       ├── course_info/      # Course information PDFs
│       ├── transcripts/      # Lecture transcripts
│       └── slides/           # Lecture slides
├── output/
│   ├── course_context/       # Extracted course context
│   ├── transcripts/          # Processed transcript data
│   ├── slides/               # Processed slide data
│   ├── fused_context/        # Combined context from all sources
│   ├── knowledge_graph/      # Generated knowledge graph
│   ├── visualizations/       # Knowledge graph visualizations
│   ├── embeddings/           # Vector embeddings
│   ├── supervision/          # Supervision results
│   └── vision_board_input/   # Prepared input for vision board pipeline
├── core/                     # Core pipeline components
├── context_files/            # Stratified context for development
├── run_enhanced_pipeline.py  # Main pipeline script
├── run_and_visualize.py      # Run pipeline with visualization
├── run_component.py          # Run specific pipeline components
├── prepare_for_vision_board.py # Prepare resources for next pipeline
└── install_and_run.sh/bat    # Installation and execution scripts
```

## Development Context Structure

The codebase is developed according to stratified contexts defined in the `context_files` directory:

- **Universal Context**: Overarching project goals and principles
- **Global Context**: High-level system architecture and integration
- **Local Context**: Specific implementation details for components
- **Data Processing Flow**: How data moves through the pipeline
- **Document Loading**: Strategies for loading educational materials

When working on specific elements of the codebase, the appropriate context files should be considered, while remaining cognizant of the larger global and universal context.

## Technical Details

The knowledge graph generation uses:

- NetworkX and Pyvis for graph creation and visualization
- Sentence-Transformers for generating embeddings
- Interactive HTML with customized CSS and JavaScript for visualization
- Matplotlib for static image generation
