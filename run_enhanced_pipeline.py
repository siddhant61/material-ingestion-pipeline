#!/usr/bin/env python3
"""
Enhanced Educational Content Pipeline Runner

This script demonstrates the enhanced educational content pipeline:
1. Fixes template issues in Document Loader Agent
2. Processes course information documents to extract global context
3. Uses the global context to guide transcript and slide processing
4. Outputs structured data for knowledge graph construction

Usage:
    python run_enhanced_pipeline.py
"""

import os
import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime
import shutil


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pipeline_runner")

# Setup directories
script_dir = Path(__file__).parent.absolute()
input_dir = script_dir / "input"
output_dir = script_dir / "output"

# Course material directories 
course_info_dir = input_dir / "course_material" / "course_info"
transcripts_dir = input_dir / "course_material" / "transcripts"
slides_dir = input_dir / "course_material" / "slides"

# Make sure directories exist
os.makedirs(course_info_dir, exist_ok=True)
os.makedirs(transcripts_dir, exist_ok=True)
os.makedirs(slides_dir, exist_ok=True)

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Check if course material files exist and create samples if needed
def setup_sample_files():
    """Create sample files if no course material files exist."""
    logger.info("Checking for course material files...")
    
    # Check if course info directory is empty
    course_info_files = list(course_info_dir.glob("*"))
    if not course_info_files:
        logger.warning("No course info files found. Creating a sample file.")
        
        # Create a sample course info file
        sample_course_info = """# Quantum Computing Basics
## Course Overview
This course introduces the fundamentals of quantum computing, from basic quantum mechanics to quantum algorithms.

## Learning Objectives
- Understand quantum bits (qubits) and quantum gates
- Learn about quantum superposition and entanglement
- Explore simple quantum algorithms

## Course Structure
1. Introduction to Quantum Computing
2. Quantum Bits and Gates
3. Quantum Algorithms
4. Applications of Quantum Computing
"""
        with open(course_info_dir / "course_info.md", "w", encoding="utf-8") as f:
            f.write(sample_course_info)
        
        logger.info(f"Created sample course info file at {course_info_dir / 'course_info.md'}")
    
    # Check if transcripts directory is empty
    transcript_files = list(transcripts_dir.glob("*"))
    if not transcript_files:
        logger.warning("No transcript files found. Creating a sample file.")
        
        # Create a sample transcript file in WebVTT format
        sample_transcript = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello and welcome to the first lecture on Quantum Computing Basics.

00:00:05.100 --> 00:00:10.000
In this course, we'll explore the fascinating world of quantum computing.

00:00:10.100 --> 00:00:15.000
Let's start by understanding what makes quantum computing different from classical computing.

00:00:15.100 --> 00:00:20.000
The fundamental unit of quantum information is the qubit, which can exist in a superposition of states.

00:00:20.100 --> 00:00:25.000
Unlike classical bits that can only be 0 or 1, qubits can be both 0 and 1 simultaneously.

00:00:25.100 --> 00:00:30.000
This property gives quantum computers their potential for exponential processing power.
"""
        with open(transcripts_dir / "1.1 Introduction to Quantum Computing.txt", "w", encoding="utf-8") as f:
            f.write(sample_transcript)
        
        logger.info(f"Created sample transcript file at {transcripts_dir / '1.1 Introduction to Quantum Computing.txt'}")
    
    # We can't easily create sample PDF files for slides, so just log a warning
    slide_files = list(slides_dir.glob("*"))
    if not slide_files:
        logger.warning("No slide files found. Please add PDF slide files to the slides directory.")
        # Create a placeholder text file explaining how to add slides
        with open(slides_dir / "README.txt", "w", encoding="utf-8") as f:
            f.write("Place your slide PDF files in this directory.\n")
        
        logger.info(f"Created README file at {slides_dir / 'README.txt'}")
    
    logger.info("Course material file check complete.")

# Call the setup function to ensure we have sample files
setup_sample_files()

# Import the DataManager
from core.utils.data_manager import DataManager

# Initialize the DataManager
data_manager = DataManager({
    "base_data_dir": "output/data"
})

# Create a unique run ID for this pipeline run
pipeline_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

def run_template_fixes():
    """Run the template fixes script to address Document Loader Agent issues."""
    logger.info("Fixing template issues in Document Loader Agent...")
    
    try:
        # Import and run the template fixer from our consolidated module
        from core.pipeline.pipeline_fixes import fix_document_loader_templates
        fix_document_loader_templates()
        logger.info("Template fixes completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error fixing templates: {str(e)}")
        return False

def extract_course_context(course_info_path):
    """
    Extract global context from course information document.
    
    Args:
        course_info_path (Path): Path to the course info PDF
        
    Returns:
        dict: The extracted course context
    """
    logger.info(f"Extracting course context from {course_info_path}")
    
    try:
        # Check if the path is a directory or file
        if course_info_path.is_dir():
            # Find the first markdown or PDF file in the directory
            markdown_files = list(course_info_path.glob("*.md"))
            pdf_files = list(course_info_path.glob("*.pdf"))
            
            if markdown_files:
                logger.info(f"Found markdown file: {markdown_files[0]}")
                course_file = markdown_files[0]
                is_markdown = True
            elif pdf_files:
                logger.info(f"Found PDF file: {pdf_files[0]}")
                course_file = pdf_files[0]
                is_markdown = False
            else:
                raise FileNotFoundError(f"No markdown or PDF files found in {course_info_path}")
        else:
            course_file = course_info_path
            is_markdown = course_file.suffix.lower() == '.md'
        
        # Print the actual file path to help diagnose encoding issues
        logger.info(f"Full course info file path: {str(course_file)}")
        
        # Import components
        from core.agents.document_loader.tools.document_analyzer import DocumentAnalyzer
        from core.agents.course_context.course_context_extractor import CourseContextExtractor
        
        # Initialize components
        document_analyzer = DocumentAnalyzer()
        course_context_extractor = CourseContextExtractor()
        
        # Process the document based on its type
        if is_markdown:
            logger.info("Loading Markdown document...")
            with open(course_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
                
            # Create basic metadata for markdown
            basic_metadata = {
                "filename": course_file.name,
                "filetype": "markdown",
                "filesize": os.path.getsize(course_file),
                "created": datetime.fromtimestamp(os.path.getctime(course_file)).isoformat(),
                "modified": datetime.fromtimestamp(os.path.getmtime(course_file)).isoformat()
            }
        else:
            logger.info("Loading PDF document...")
            pdf_document, basic_metadata = document_analyzer.load_pdf(str(course_file))
            
            logger.info("Extracting text from PDF...")
            text_content = document_analyzer.extract_text(pdf_document)
        
        logger.info(f"Extracted {len(text_content)} characters of text content")
        
        # Extract course context
        logger.info("Extracting course context from text...")
        course_context = course_context_extractor.extract_course_context(
            text_content,
            basic_metadata
        )
        
        # Save the context
        context_output_dir = output_dir / "course_context"
        os.makedirs(context_output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_file = context_output_dir / f"course_context_{timestamp}.json"
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(course_context, f, ensure_ascii=False, indent=2)
        
        # Store the course context in the data manager
        data_manager.store_agent_output(
            "course_context", 
            course_context,
            pipeline_run_id
        )
        
        logger.info(f"Course context extracted and saved to {context_file}")
        return course_context
    except FileNotFoundError as e:
        logger.error(f"Course info file not found: {str(e)}")
        # Create a basic fallback context with error information
        fallback_context = {
            "title": "Unknown Course",
            "description": "Course context extraction failed - file not found",
            "objectives": ["Not available due to missing files"],
            "learning_outcomes": ["Not available due to missing files"],
            "subject_domain": "Unknown",
            "level": "Unknown",
            "structure": [
                {
                    "title": "Content unavailable",
                    "description": "Course structure could not be extracted",
                    "topics": []
                }
            ],
            "instructors": [
                {
                    "name": "",
                    "title": "",
                    "bio": "",
                    "contact": ""
                }
            ],
            "metadata": {
                "extraction_timestamp": datetime.now().isoformat(),
                "model_used": "fallback",
                "document_source": str(course_info_path),
                "extraction_status": "failed",
                "error_message": str(e),
                "completeness_score": 0.0
            }
        }
        
        _save_fallback_context(fallback_context)
        return fallback_context
    except Exception as e:
        logger.error(f"Error extracting course context: {str(e)}")
        # Create a basic fallback context with error information
        fallback_context = {
            "title": "Unknown Course",
            "description": "Course context extraction failed",
            "objectives": ["Not available due to extraction failure"],
            "learning_outcomes": ["Not available due to extraction failure"],
            "subject_domain": "Unknown",
            "level": "Unknown",
            "structure": [
                {
                    "title": "Content unavailable",
                    "description": "Course structure could not be extracted",
                    "topics": []
                }
            ],
            "instructors": [
                {
                    "name": "",
                    "title": "",
                    "bio": "",
                    "contact": ""
                }
            ],
            "metadata": {
                "extraction_timestamp": datetime.now().isoformat(),
                "model_used": "fallback",
                "document_source": str(course_info_path),
                "extraction_status": "failed",
                "error_message": str(e),
                "completeness_score": 0.0
            }
        }
        
        _save_fallback_context(fallback_context)
        return fallback_context

def _save_fallback_context(fallback_context):
    """Helper function to save fallback context"""
    # Save the fallback context
    context_output_dir = output_dir / "course_context"
    os.makedirs(context_output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    context_file = context_output_dir / f"course_context_fallback_{timestamp}.json"
    
    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(fallback_context, f, ensure_ascii=False, indent=2)
        
    # Store the fallback context in the data manager
    data_manager.store_agent_output(
        "course_context", 
        fallback_context,
        pipeline_run_id
    )
    
    logger.info(f"Fallback course context saved to {context_file}")

def process_transcripts(transcripts_path, course_context):
    """
    Process transcript files using the course context.
    
    Args:
        transcripts_path (Path): Path to the transcripts directory
        course_context (dict): The extracted course context
        
    Returns:
        dict: The processed transcript data
    """
    logger.info("Processing transcripts with course context...")
    
    try:
        # Run the transcript template fixer first
        logger.info("Fixing transcript template issues...")
        try:
            from core.pipeline.pipeline_fixes import fix_transcript_templates
            fix_transcript_templates()
            logger.info("Transcript template fixes completed successfully")
        except Exception as e:
            logger.warning(f"Warning: Transcript template fixes had issues: {str(e)}")
        
        # Create output directory for processed transcripts
        transcript_output_dir = output_dir / "transcripts"
        os.makedirs(transcript_output_dir, exist_ok=True)
        
        # Import and initialize the transcript processor
        from core.agents.transcript_processor import TranscriptProcessor
        transcript_processor = TranscriptProcessor()
        
        # Process all transcripts
        processing_results = transcript_processor.process_all_transcripts(
            str(transcripts_path),
            course_context,
            str(transcript_output_dir)
        )
        
        logger.info(f"Processed {processing_results['processed_count']} transcript files")
        
        if processing_results.get('error_count', 0) > 0:
            logger.warning(f"Encountered {processing_results['error_count']} errors during transcript processing")
        
        # Save overall results
        results_file = output_dir / "transcript_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(processing_results, f, ensure_ascii=False, indent=2)
        
        # Store the transcript processing results in the data manager
        data_manager.store_agent_output(
            "transcript_processor", 
            processing_results,
            pipeline_run_id
        )
        
        # Register input dependency
        data_manager.register_input_dependency(
            "transcript_processor",
            pipeline_run_id,
            "course_context",
            pipeline_run_id
        )
        
        logger.info(f"Transcript processing results saved to {results_file}")
        
        return processing_results
    except Exception as e:
        logger.error(f"Error processing transcripts: {str(e)}")
        return {
            "status": "error",
            "message": f"Transcript processing failed: {str(e)}"
        }

def process_slides(slides_path, course_context, transcript_data):
    """
    Process slide files using course context and transcript data.
    
    Args:
        slides_path (Path): Path to the slides directory
        course_context (dict): The extracted course context
        transcript_data (dict): The processed transcript data
        
    Returns:
        dict: The processed slide data
    """
    logger.info("Processing slides with course context and transcript data...")
    
    try:
        # Create output directory for processed slides
        slide_output_dir = output_dir / "slides"
        os.makedirs(slide_output_dir, exist_ok=True)
        
        # Import and initialize the slide processor
        from core.agents.slide_processor import SlideProcessor
        
        # First check if we need to install dependencies
        try:
            import pypdf
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("Missing slide processor dependencies. Attempting to install...")
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf", "PyMuPDF"])
                logger.info("Successfully installed slide processor dependencies")
            except Exception as e:
                logger.error(f"Failed to install dependencies: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Could not process slides: missing dependencies (pypdf, PyMuPDF). Error: {str(e)}"
                }
        
        # Create the slide processor
        slide_processor = SlideProcessor()
        
        # Process all slides
        processing_results = slide_processor.process_all_slides(
            str(slides_path),
            course_context,
            transcript_data,
            str(slide_output_dir)
        )
        
        logger.info(f"Processed {processing_results.get('processed_count', 0)} slide files")
        
        if processing_results.get('error_count', 0) > 0:
            logger.warning(f"Encountered {processing_results['error_count']} errors during slide processing")
        
        # Save overall results
        results_file = output_dir / "slide_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(processing_results, f, ensure_ascii=False, indent=2)
        
        # Store the slide processing results in the data manager
        data_manager.store_agent_output(
            "slide_processor", 
            processing_results,
            pipeline_run_id
        )
        
        # Register input dependencies
        data_manager.register_input_dependency(
            "slide_processor",
            pipeline_run_id,
            "course_context",
            pipeline_run_id
        )
        
        data_manager.register_input_dependency(
            "slide_processor",
            pipeline_run_id,
            "transcript_processor",
            pipeline_run_id
        )
        
        logger.info(f"Slide processing results saved to {results_file}")
        
        return processing_results
    except Exception as e:
        logger.error(f"Error processing slides: {str(e)}")
        return {
            "status": "error",
            "message": f"Slide processing failed: {str(e)}"
        }

def generate_fused_context(course_context, transcript_data, slide_data):
    """
    Generate fused context from all data sources.
    
    Args:
        course_context (dict): The extracted course context
        transcript_data (dict): The processed transcript data
        slide_data (dict): The processed slide data
        
    Returns:
        dict: The fused context
    """
    logger.info("Generating fused context...")
    
    try:
        # Import and use the ContextFusion component
        from core.agents.context_fusion import ContextFusion
        
        # Create a temporary directory for input files
        temp_dir = output_dir / "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save input data to temporary files
        course_context_path = temp_dir / "course_context.json"
        transcript_data_path = temp_dir / "transcript_data.json"
        slide_data_path = temp_dir / "slide_data.json"
        
        with open(course_context_path, 'w', encoding='utf-8') as f:
            json.dump(course_context, f, ensure_ascii=False, indent=2)
        
        with open(transcript_data_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        
        with open(slide_data_path, 'w', encoding='utf-8') as f:
            json.dump(slide_data, f, ensure_ascii=False, indent=2)
        
        # Initialize the ContextFusion component
        context_fusion = ContextFusion()
        
        # First, load the data
        load_success = context_fusion.load_data(
            str(course_context_path),
            str(transcript_data_path),
            str(slide_data_path)
        )
        
        if not load_success:
            logger.error("Failed to load data for context fusion")
            return None
            
        # Generate the fused context
        fused_context_dir = output_dir / "fused_context"
        os.makedirs(fused_context_dir, exist_ok=True)
        
        # Now generate the fused context with just the output directory
        fused_context = context_fusion.generate_fused_context(str(fused_context_dir))
        
        # Save the fused context
        fused_context_file = fused_context_dir / "fused_context.json"
        
        with open(fused_context_file, 'w', encoding='utf-8') as f:
            json.dump(fused_context, f, ensure_ascii=False, indent=2)
        
        # Store the fused context in the data manager
        data_manager.store_agent_output(
            "context_fusion", 
            fused_context,
            pipeline_run_id
        )
        
        # Register input dependencies
        data_manager.register_input_dependency(
            "context_fusion",
            pipeline_run_id,
            "course_context",
            pipeline_run_id
        )
        
        data_manager.register_input_dependency(
            "context_fusion",
            pipeline_run_id,
            "transcript_processor",
            pipeline_run_id
        )
        
        data_manager.register_input_dependency(
            "context_fusion",
            pipeline_run_id,
            "slide_processor",
            pipeline_run_id
        )
        
        logger.info(f"Fused context generated and saved to {fused_context_file}")
        
        return fused_context
    except Exception as e:
        logger.error(f"Error generating fused context: {str(e)}")
        return {
            "status": "error",
            "message": f"Context fusion failed: {str(e)}"
        }

def supervise_outputs(agent_outputs):
    """
    Supervise and refine the outputs from all agents.
    
    Args:
        agent_outputs (dict): Outputs from all agents
        
    Returns:
        dict: Supervised and refined outputs
    """
    logger.info("Supervising and refining agent outputs...")
    
    try:
        # Import the SupervisorAgent
        from core.agents.supervisor import SupervisorAgent
        
        # Initialize the SupervisorAgent with output directory
        supervisor = SupervisorAgent({
            "output_dir": str(output_dir / "supervision")
        })
        
        # Create output directory
        supervision_results_dir = output_dir / "supervision"
        os.makedirs(supervision_results_dir, exist_ok=True)
        
        # Process each agent's output
        refined_outputs = {}
        supervision_results = {}
        
        for agent_name, content in agent_outputs.items():
            try:
                logger.info(f"Supervising output from {agent_name}...")
                
                # Validate content is a dictionary
                if not isinstance(content, dict):
                    logger.warning(f"Content from {agent_name} is not a dictionary, wrapping it")
                    if content is None:
                        content = {"data": "empty_content"}
                    else:
                        content = {"data": content}
                
                # Supervise the agent output
                result = supervisor.supervise(
                    agent_name=agent_name,
                    content=content,
                    auto_refine=True
                )
                
                # Store the result
                refined_outputs[agent_name] = result.get("refined_content", content)
                supervision_results[agent_name] = result
                
                # Store the supervision result in the data manager
                data_manager.store_agent_output(
                    f"supervisor_{agent_name}",
                    result,
                    pipeline_run_id
                )
                
                # Register input dependency
                data_manager.register_input_dependency(
                    f"supervisor_{agent_name}",
                    pipeline_run_id,
                    agent_name,
                    pipeline_run_id
                )
                
                logger.info(f"Supervision completed for {agent_name}")
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON parsing error supervising {agent_name}: {str(json_error)}")
                logger.error(f"This is likely due to a malformed response from the AI model")
                refined_outputs[agent_name] = content  # Use original content on error
                supervision_results[agent_name] = {
                    "error": f"JSON parsing error: {str(json_error)}",
                    "agent_name": agent_name,
                    "refined_content": content
                }
            except Exception as e:
                logger.error(f"Error supervising {agent_name}: {str(e)}")
                refined_outputs[agent_name] = content  # Use original content on error
                supervision_results[agent_name] = {
                    "error": str(e),
                    "agent_name": agent_name,
                    "refined_content": content
                }
        
        # Save all supervision results
        combined_results = {
            "refined_outputs": refined_outputs,
            "supervision_results": supervision_results,
            "timestamp": datetime.now().isoformat()
        }
        
        supervision_results_file = supervision_results_dir / "all_supervision_results.json"
        with open(supervision_results_file, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, ensure_ascii=False, indent=2)
        
        # Store the overall supervision results in the data manager
        data_manager.store_agent_output(
            "supervisor",
            combined_results,
            pipeline_run_id
        )
        
        logger.info(f"All supervision results saved to {supervision_results_file}")
        
        return refined_outputs
    except Exception as e:
        logger.error(f"Error supervising outputs: {str(e)}")
        return agent_outputs

def generate_knowledge_graph(fused_context):
    """
    Generate a knowledge graph from the fused context.
    
    Args:
        fused_context (dict): The fused context
        
    Returns:
        dict: The generated knowledge graph
    """
    logger.info("Generating knowledge graph...")
    
    try:
        # Import the KnowledgeGraphGenerator
        from core.pipeline.knowledge_graph import KnowledgeGraphGenerator
        
        # Initialize the KnowledgeGraphGenerator
        kg_generator = KnowledgeGraphGenerator()
        
        # Generate the knowledge graph
        knowledge_graph = kg_generator.generate_knowledge_graph(fused_context)
        
        # Save the knowledge graph
        knowledge_graph_dir = output_dir / "knowledge_graph"
        os.makedirs(knowledge_graph_dir, exist_ok=True)
        output_file = kg_generator.save_knowledge_graph(
            knowledge_graph,
            str(knowledge_graph_dir)
        )
        
        # Store the knowledge graph in the data manager
        data_manager.store_agent_output(
            "knowledge_graph", 
            knowledge_graph,
            pipeline_run_id
        )
        
        # Register input dependencies
        data_manager.register_input_dependency(
            "knowledge_graph",
            pipeline_run_id,
            "context_fusion",
            pipeline_run_id
        )
        
        logger.info(f"Knowledge graph generated and saved to {output_file}")
        return knowledge_graph
    except Exception as e:
        logger.error(f"Error generating knowledge graph: {str(e)}")
        return None

def generate_embeddings(knowledge_graph):
    """
    Generate embeddings from the knowledge graph.
    
    Args:
        knowledge_graph (dict): The knowledge graph
        
    Returns:
        dict: The embeddings
    """
    logger.info("Generating embeddings...")
    
    try:
        # Import the EmbeddingsGenerator component
        from core.pipeline.embeddings import EmbeddingsGenerator
        
        # Initialize the EmbeddingsGenerator
        embeddings_generator = EmbeddingsGenerator()
        
        # Generate embeddings
        embeddings = embeddings_generator.generate_embeddings(knowledge_graph)
        
        # Save the embeddings
        embeddings_dir = output_dir / "embeddings"
        os.makedirs(embeddings_dir, exist_ok=True)
        output_file = embeddings_generator.save_embeddings(
            embeddings,
            str(embeddings_dir)
        )
        
        # Store the embeddings in the data manager
        data_manager.store_agent_output(
            "embeddings", 
            embeddings,
            pipeline_run_id
        )
        
        # Register input dependencies
        data_manager.register_input_dependency(
            "embeddings",
            pipeline_run_id,
            "knowledge_graph",
            pipeline_run_id
        )
        
        logger.info(f"Embeddings generated and saved to {output_file}")
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        return None

def visualize_knowledge_graph(knowledge_graph):
    """
    Create visualizations of the knowledge graph.
    
    Args:
        knowledge_graph (dict): The knowledge graph to visualize
        
    Returns:
        dict: Paths to the generated visualizations
    """
    logger.info("Generating knowledge graph visualizations...")
    
    try:
        # Import the KnowledgeGraphVisualizer
        from core.pipeline.visualization import KnowledgeGraphVisualizer
        
        # Initialize the visualizer
        visualizer = KnowledgeGraphVisualizer({
            "height": "800px",
            "width": "100%",
            "bgcolor": "#ffffff",
            "node_scaling": 1.5
        })
        
        # Create output directory
        visualization_dir = output_dir / "visualizations"
        os.makedirs(visualization_dir, exist_ok=True)
        
        # Generate interactive visualization
        interactive_path = visualizer.create_interactive_visualization(
            knowledge_graph,
            str(visualization_dir),
            "knowledge_graph_interactive.html"
        )
        
        # Generate static visualization
        static_path = visualizer.create_static_visualization(
            knowledge_graph,
            str(visualization_dir),
            "knowledge_graph_static.png"
        )
        
        logger.info(f"Knowledge graph visualizations generated.")
        logger.info(f"Interactive visualization: {interactive_path}")
        logger.info(f"Static visualization: {static_path}")
        
        return {
            "interactive_visualization": interactive_path,
            "static_visualization": static_path,
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Error visualizing knowledge graph: {str(e)}")
        return {
            "status": "error",
            "message": f"Knowledge graph visualization failed: {str(e)}"
        }

def generate_pipeline_report():
    """
    Generate a report on the pipeline execution.
    
    Returns:
        dict: The pipeline report
    """
    logger.info("Generating pipeline report...")
    
    # Get all runtime data from the data manager
    runtime_data = data_manager.get_runtime_data()
    
    # Get data provenance
    data_provenance = data_manager.export_data_provenance()
    
    # Create the report
    pipeline_report = {
        "run_id": pipeline_run_id,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "execution_summary": {
            "start_time": runtime_data.get(f"pipeline_{pipeline_run_id}", {})
                           .get("metadata", {}).get("start_time", "unknown"),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": None
        },
        "agent_summary": {},
        "data_provenance": data_provenance
    }
    
    # Calculate duration if we have a start time
    start_time = runtime_data.get(f"pipeline_{pipeline_run_id}", {}) \
                           .get("metadata", {}).get("start_time")
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.now()
        duration = (end_dt - start_dt).total_seconds()
        pipeline_report["execution_summary"]["duration_seconds"] = duration
    
    # Add agent summaries
    for key, value in runtime_data.items():
        if key.startswith("pipeline_"):
            continue
        
        agent_name = key.split("_")[0]
        if agent_name not in pipeline_report["agent_summary"]:
            pipeline_report["agent_summary"][agent_name] = {
                "status": value.get("data", {}).get("status", "unknown"),
                "execution_time": value.get("metadata", {}).get("execution_time", "unknown"),
                "timestamp": value.get("metadata", {}).get("timestamp", "unknown")
            }
    
    # Save the report
    report_file = output_dir / "pipeline_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(pipeline_report, f, ensure_ascii=False, indent=2)
    
    # Store the pipeline report in the data manager
    data_manager.store_agent_output(
        "pipeline", 
        pipeline_report,
        pipeline_run_id
    )
    
    logger.info(f"Pipeline report generated and saved to {report_file}")
    
    return pipeline_report

def process_pipeline():
    """
    Run the complete material ingestion pipeline.
    """
    logger.info("Starting pipeline...")
    
    # Set up pipeline run ID using datetime
    from datetime import datetime
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Pipeline run ID: {run_id}")
    
    # Initialize pipeline results
    pipeline_results = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "status": "running",
        "steps": {}
    }
    
    # Apply template fixes if needed
    template_fixes = run_template_fixes()
    
    # Step 1: Extract course context
    course_context = extract_course_context(course_info_dir)
    pipeline_results["steps"]["course_context"] = {"status": "completed", "output": str(output_dir / "course_context")}
    if not course_context or (isinstance(course_context, dict) and course_context.get("status") == "error"):
        logger.error("Failed to extract course context, but continuing with fallback context")
    
    # Step 2: Process transcripts
    transcript_data = process_transcripts(transcripts_dir, course_context)
    pipeline_results["steps"]["transcript_processing"] = {"status": "completed", "output": str(output_dir / "transcript_processing")}
    if not transcript_data or (isinstance(transcript_data, dict) and transcript_data.get("status") == "error"):
        logger.error("Failed to process transcripts, but continuing with pipeline")
    
    # Step 3: Process slides
    slide_data = process_slides(slides_dir, course_context, transcript_data)
    pipeline_results["steps"]["slide_processing"] = {"status": "completed", "output": str(output_dir / "slide_processing")}
    if not slide_data or (isinstance(slide_data, dict) and slide_data.get("status") == "error"):
        logger.error("Failed to process slides, but continuing with pipeline")
    
    # Step 4: Generate fused context
    fused_context = generate_fused_context(course_context, transcript_data, slide_data)
    pipeline_results["steps"]["context_fusion"] = {"status": "completed", "output": str(output_dir / "fused_context")}
    if not fused_context or (isinstance(fused_context, dict) and fused_context.get("status") == "error"):
        logger.error("Failed to generate fused context")
        # Create a minimal fallback fused context
        fused_context = {
            "title": "Fallback Context",
            "concepts": [],
            "relationships": [],
            "module_structure": [],
            "metadata": {
                "generated": datetime.now().isoformat(),
                "status": "fallback"
            }
        }
    
    # Step 5: Supervise outputs
    agent_outputs = {
        "course_context": course_context if course_context else {"status": "error", "message": "Course context extraction failed"},
        "transcript_processor": transcript_data if transcript_data else {"status": "error", "message": "Transcript processing failed"},
        "slide_processor": slide_data if slide_data else {"status": "error", "message": "Slide processing failed"},
        "context_fusion": fused_context if fused_context else {"status": "error", "message": "Context fusion failed"}
    }
    
    refined_outputs = supervise_outputs(agent_outputs)
    if not refined_outputs:
        logger.error("Failed to supervise outputs")
        refined_outputs = agent_outputs
    
    pipeline_results["steps"]["supervision"] = {"status": "completed", "output": str(output_dir / "supervision")}
    
    # Use original fused context for knowledge graph generation if supervision failed
    if "context_fusion" in refined_outputs and refined_outputs["context_fusion"] != agent_outputs["context_fusion"]:
        logger.info("Using refined fused context for knowledge graph generation")
        fused_context_for_kg = refined_outputs["context_fusion"]
    else:
        logger.info("Using original fused context for knowledge graph generation")
        fused_context_for_kg = fused_context
    
    # Step 6: Generate knowledge graph
    logger.info("Generating knowledge graph...")
    knowledge_graph = generate_knowledge_graph(fused_context_for_kg)
    
    if knowledge_graph is not None:
        # Record success in pipeline results
        pipeline_results["steps"]["knowledge_graph"] = {
            "status": "completed", 
            "output": str(output_dir / "knowledge_graph")
        }
        
        # Check if the knowledge graph has entities and relationships
        entity_count = len(knowledge_graph.get("entities", []))
        relationship_count = len(knowledge_graph.get("relationships", []))
        logger.info(f"Knowledge graph has {entity_count} entities and {relationship_count} relationships")
        
        # Step 7: Visualize knowledge graph if it has content
        if entity_count > 0 or relationship_count > 0:
            logger.info("Visualizing knowledge graph...")
            visualization_results = visualize_knowledge_graph(knowledge_graph)
            
            if visualization_results and "status" in visualization_results and visualization_results["status"] == "success":
                pipeline_results["steps"]["visualizations"] = {
                    "status": "completed",
                    "output": {
                        "interactive": visualization_results.get("interactive_visualization", ""),
                        "static": visualization_results.get("static_visualization", "")
                    }
                }
            else:
                logger.warning("Knowledge graph visualization failed or was skipped")
                pipeline_results["steps"]["visualizations"] = {"status": "skipped"}
        else:
            logger.warning("Knowledge graph is empty, skipping visualization")
            pipeline_results["steps"]["visualizations"] = {"status": "skipped", "reason": "empty_graph"}
        
        # Step 8: Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = generate_embeddings(knowledge_graph)
        
        if embeddings is not None:
            pipeline_results["steps"]["embeddings"] = {
                "status": "completed", 
                "output": str(output_dir / "embeddings")
            }
        else:
            logger.error("Failed to generate embeddings")
            pipeline_results["steps"]["embeddings"] = {"status": "failed"}
    else:
        logger.error("Failed to generate knowledge graph")
        pipeline_results["steps"]["knowledge_graph"] = {"status": "failed"}
        pipeline_results["steps"]["visualizations"] = {"status": "skipped", "reason": "no_knowledge_graph"}
        pipeline_results["steps"]["embeddings"] = {"status": "skipped", "reason": "no_knowledge_graph"}
    
    # Step 9: Generate pipeline report
    logger.info("Generating pipeline report...")
    pipeline_results["status"] = "completed"
    pipeline_results["completion_timestamp"] = datetime.now().isoformat()
    
    # Save pipeline results
    pipeline_output_path = output_dir / "pipeline_report.json"
    with open(pipeline_output_path, 'w', encoding='utf-8') as f:
        json.dump(pipeline_results, f, indent=2)
    
    # Store the pipeline output in the runtime data
    data_manager.store_output("pipeline", pipeline_results)
    
    logger.info(f"Pipeline report generated and saved to {pipeline_output_path}")
    
    # Archive the data
    data_manager.archive_run_data(run_id)
    
    logger.info(f"Pipeline completed successfully (Run ID: {run_id})")
    return pipeline_results

if __name__ == "__main__":
    process_pipeline() 