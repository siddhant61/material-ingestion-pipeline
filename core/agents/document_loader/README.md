# Document Loader Agent

The Document Loader Agent is an intelligent agent designed to process educational documents, extract structured content, and generate rich metadata for educational knowledge graphs and content pipelines.

## Features

- **Document Discovery**: Automatically finds educational documents in specified directories
- **Document Classification**: Identifies document types (textbooks, lecture notes, research papers, etc.)
- **Adaptive Content Extraction**: Adjusts extraction strategy based on document structure
- **Rich Metadata Extraction**: Extracts educational context, topics, learning objectives, and relationships
- **Image Processing**: Extracts and analyzes images within documents
- **Structured Output**: Generates standardized outputs for downstream processing

## Architecture

The Document Loader Agent follows a modular architecture with the following components:

### AI Assistants

- **Document Classifier Assistant**: Identifies document types and educational contexts
- **Adaptive Extractor Assistant**: Creates extraction plans based on document structure
- **Metadata Extractor Assistant**: Extracts rich educational metadata

### Tools

- **Document Analyzer**: Processes documents using the AI assistants

### Core Components

- **Models**: Manages AI model interactions
- **Memory**: Tracks state and persists processing history
- **Orchestration**: Manages document processing workflow
- **Tools**: Provides document analysis capabilities

## Usage

### Basic Usage

```python
from core.agents.document_loader import DocumentLoaderAgent

# Configure the agent
config = {
    "input_dir": "input/course_material",
    "output_dir": "output/processed_documents",
    "model_name": "gpt-4o-mini"
}

# Initialize the agent
agent = DocumentLoaderAgent(config)

# Run the agent
result = agent.run({
    "input_dir": "input/course_material"
})

# Access the results
print(f"Processed {result['summary']['total_documents']} documents")
print(f"Output directory: {result['output_dir']}")
```

### Command Line Example

You can also use the provided example script:

```bash
python examples/document_loader_example.py --input-dir input/course_material --output-dir output/processed_documents --model gpt-4o-mini
```

## Output Structure

The Document Loader Agent produces the following outputs:

1. **Processed Documents**: Structured content extracted from each document
2. **Document Metadata**: Rich educational metadata for each document
3. **Processing Summary**: Overview of processing results
4. **Extracted Images**: Images extracted from documents

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `input_dir` | Directory containing documents to process | `input/course_material` |
| `output_dir` | Directory to store processed documents | `output/processed_documents` |
| `data_dir` | Directory to store agent data | `data/document_loader` |
| `model_name` | AI model to use for document analysis | `gpt-4o-mini` |
| `log_level` | Logging level | `INFO` |

## Requirements

- Python 3.8+
- PyMuPDF (fitz)
- LangChain
- OpenAI API access

## Error Handling

The Document Loader Agent includes robust error handling:

- Graceful handling of PDF reading errors
- Retry mechanisms for API calls
- Detailed error logging
- Tracking of failed documents

## Contributing

Contributions to the Document Loader Agent are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
