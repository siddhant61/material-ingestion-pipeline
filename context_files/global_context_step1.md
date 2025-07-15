# Global Context: Step 1 - Material Ingestion & Knowledge Graph Creation

## Step 1 Overview

The Material Ingestion & Knowledge Graph Creation step is responsible for:

1. Processing raw educational materials (PDFs, transcripts, slides)
2. Extracting structured content and metadata
3. Creating a hierarchical knowledge graph that represents the educational content
4. Building a vector database for similarity search and RAG operations

## Inputs

- **Course Information PDFs**: Located in `input/course_material/course_info/`
- **Lecture Transcripts**: Located in `input/course_material/transcripts/`
- **Lecture Slides**: Located in `input/course_material/slides/`

## Processing Pipeline

1. **Document Loading & Preprocessing**
   - PDF processing and text extraction
   - OCR for image-heavy content
   - Document classification and metadata extraction
   - Image extraction and analysis

2. **Transcript Processing**
   - Semantic chunking of transcripts
   - Speaker identification
   - Time-code alignment
   - Content classification

3. **Context Extraction**
   - Educational level analysis
   - Topic identification
   - Entity recognition
   - Concept extraction

4. **Knowledge Graph Construction**
   - Creation of hierarchical structure (Lessons → Topics → Concepts)
   - Establishing relationships between entities
   - Linking text and image references
   - Metadata enrichment

5. **Vector Database Creation**
   - Text embedding generation
   - Efficient vector storage
   - Similarity search capabilities
   - RAG query optimization

## Outputs

1. **Structured Knowledge Graph**: JSON representation of the educational content hierarchy
2. **Vector Database**: FAISS/Milvus index for RAG operations
3. **Processed Content**: Structured representation of all input materials
4. **Content Metadata**: Additional contextual information about the content

## Key Technologies

- **LangGraph**: For agent orchestration and workflow management
- **LangChain**: For RAG and interaction with LLMs
- **GPT-4o-mini**: As the primary model for AI assistants
- **PyMuPDF/PDF Processing Tools**: For document analysis
- **Vector Storage Solutions**: For efficient embedding storage and retrieval

This context will be updated as the implementation progresses.
