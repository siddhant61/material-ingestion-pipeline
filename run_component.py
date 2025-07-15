#!/usr/bin/env python3
"""
Run Specific Pipeline Component

This script allows running specific components of the material ingestion pipeline
rather than the entire pipeline. This is useful for development, testing, and
when you only need to regenerate specific outputs.

Usage:
    python run_component.py [component_name]

Available components:
    - fix: Run only the fix_pipeline_issues.py script
    - context: Extract course context only
    - transcripts: Process transcripts only
    - slides: Process slides only
    - fusion: Generate fused context only
    - supervise: Supervise outputs only
    - knowledge_graph: Generate knowledge graph only
    - visualize: Create visualizations from existing knowledge graph only
    - regenerate_visualization: Regenerate visualizations with enhanced tree structure
    - multi_level_visualization: Generate a multi-level, hierarchical visualization with separate views
    - embeddings: Generate embeddings from existing knowledge graph only
    - vision_board: Prepare resources for Vision & Mood-Board pipeline
    - all: Run the complete pipeline (same as run_enhanced_pipeline.py)
"""

import os
import sys
import subprocess
import time
import webbrowser
import argparse
from pathlib import Path
import json
import importlib.util
import logging
import traceback
from typing import Dict, Any, Optional, List, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("component_runner")

def print_colored(text, color="green"):
    """Print colored text in the terminal."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def run_fix():
    """Run all the pipeline fixes from the consolidated pipeline_fixes module."""
    print_colored("Applying pipeline fixes...", "cyan")
    try:
        from core.pipeline.pipeline_fixes import apply_all_fixes
        if apply_all_fixes():
            print_colored("Pipeline fixes applied successfully", "green")
        else:
            print_colored("Some pipeline fixes were not successful, check the logs for details", "yellow")
    except Exception as e:
        print_colored(f"Error applying pipeline fixes: {str(e)}", "red")

def import_module_function(file_path, function_name):
    """Import a function from a Python file."""
    module_name = Path(file_path).stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)

def run_extract_course_context():
    """Run only the extract_course_context function."""
    print_colored("Extracting course context...", "cyan")
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "extract_course_context")
    
    # Execute the function
    from pathlib import Path
    script_dir = Path(__file__).parent.absolute()
    input_dir = script_dir / "input"
    course_info_dir = input_dir / "course_material" / "course_info"
    
    result = run_enhanced_pipeline(course_info_dir)
    
    print_colored("Course context extraction completed", "green")
    return result

def run_process_transcripts():
    """Run only the process_transcripts function."""
    print_colored("Processing transcripts...", "cyan")
    
    # First get the course context
    course_context = run_extract_course_context()
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "process_transcripts")
    
    # Execute the function
    from pathlib import Path
    script_dir = Path(__file__).parent.absolute()
    input_dir = script_dir / "input"
    transcripts_dir = input_dir / "course_material" / "transcripts"
    
    result = run_enhanced_pipeline(transcripts_dir, course_context)
    
    print_colored("Transcript processing completed", "green")
    return result

def run_process_slides():
    """Run only the process_slides function."""
    print_colored("Processing slides...", "cyan")
    
    # First get the course context and transcript data
    course_context = run_extract_course_context()
    transcript_data = run_process_transcripts()
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "process_slides")
    
    # Execute the function
    from pathlib import Path
    script_dir = Path(__file__).parent.absolute()
    input_dir = script_dir / "input"
    slides_dir = input_dir / "course_material" / "slides"
    
    result = run_enhanced_pipeline(slides_dir, course_context, transcript_data)
    
    print_colored("Slide processing completed", "green")
    return result

def run_generate_fused_context():
    """Run only the generate_fused_context function."""
    print_colored("Generating fused context...", "cyan")
    
    # First get the necessary inputs
    course_context = run_extract_course_context()
    transcript_data = run_process_transcripts()
    slide_data = run_process_slides()
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "generate_fused_context")
    
    # Execute the function
    result = run_enhanced_pipeline(course_context, transcript_data, slide_data)
    
    print_colored("Fused context generation completed", "green")
    return result

def run_supervise_outputs():
    """Run only the supervise_outputs function."""
    print_colored("Supervising outputs...", "cyan")
    
    # First get the necessary inputs
    course_context = run_extract_course_context()
    transcript_data = run_process_transcripts()
    slide_data = run_process_slides()
    fused_context = run_generate_fused_context()
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "supervise_outputs")
    
    # Execute the function
    agent_outputs = {
        "course_context": course_context,
        "transcript_processor": transcript_data,
        "slide_processor": slide_data,
        "context_fusion": fused_context
    }
    
    result = run_enhanced_pipeline(agent_outputs)
    
    print_colored("Output supervision completed", "green")
    return result

def run_generate_knowledge_graph():
    """Run only the generate_knowledge_graph function."""
    print_colored("Generating knowledge graph...", "cyan")
    
    # Try to load existing fused context first
    script_dir = Path(__file__).parent.absolute()
    fused_context_path = script_dir / "output" / "fused_context" / "fused_context.json"
    
    if fused_context_path.exists():
        try:
            with open(fused_context_path, 'r', encoding='utf-8') as f:
                fused_context = json.load(f)
            print_colored("Loaded existing fused context from file", "yellow")
        except Exception as e:
            print_colored(f"Error loading fused context: {str(e)}", "red")
            print_colored("Generating fused context from scratch...", "yellow")
            fused_context = run_generate_fused_context()
    else:
        print_colored("No existing fused context found, generating from scratch...", "yellow")
        fused_context = run_generate_fused_context()
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "generate_knowledge_graph")
    
    # Execute the function
    result = run_enhanced_pipeline(fused_context)
    
    print_colored("Knowledge graph generation completed", "green")
    return result

def run_visualize_knowledge_graph():
    """Run only the visualize_knowledge_graph function."""
    print_colored("Generating knowledge graph visualizations...", "cyan")
    
    # Try to load existing knowledge graph first
    script_dir = Path(__file__).parent.absolute()
    kg_path = script_dir / "output" / "knowledge_graph" / "knowledge_graph.json"
    
    if kg_path.exists():
        try:
            with open(kg_path, 'r', encoding='utf-8') as f:
                knowledge_graph = json.load(f)
            print_colored("Loaded existing knowledge graph from file", "yellow")
        except Exception as e:
            print_colored(f"Error loading knowledge graph: {str(e)}", "red")
            print_colored("Generating knowledge graph from scratch...", "yellow")
            knowledge_graph = run_generate_knowledge_graph()
    else:
        print_colored("No existing knowledge graph found, generating from scratch...", "yellow")
        knowledge_graph = run_generate_knowledge_graph()
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "visualize_knowledge_graph")
    
    # Execute the function
    result = run_enhanced_pipeline(knowledge_graph)
    
    # Open the visualization
    vis_path = script_dir / "output" / "visualizations" / "knowledge_graph_interactive.html"
    if vis_path.exists():
        print_colored(f"Opening visualization: {vis_path}", "cyan")
        webbrowser.open(vis_path.as_uri())
    
    print_colored("Knowledge graph visualization completed", "green")
    return result

def run_generate_embeddings():
    """Run only the generate_embeddings function."""
    print_colored("Generating embeddings...", "cyan")
    
    # Try to load existing knowledge graph first
    script_dir = Path(__file__).parent.absolute()
    kg_path = script_dir / "output" / "knowledge_graph" / "knowledge_graph.json"
    
    if kg_path.exists():
        try:
            with open(kg_path, 'r', encoding='utf-8') as f:
                knowledge_graph = json.load(f)
            print_colored("Loaded existing knowledge graph from file", "yellow")
        except Exception as e:
            print_colored(f"Error loading knowledge graph: {str(e)}", "red")
            print_colored("Generating knowledge graph from scratch...", "yellow")
            knowledge_graph = run_generate_knowledge_graph()
    else:
        print_colored("No existing knowledge graph found, generating from scratch...", "yellow")
        knowledge_graph = run_generate_knowledge_graph()
    
    run_enhanced_pipeline = import_module_function("run_enhanced_pipeline.py", "generate_embeddings")
    
    # Execute the function
    result = run_enhanced_pipeline(knowledge_graph)
    
    print_colored("Embeddings generation completed", "green")
    return result

def run_prepare_vision_board():
    """Run the prepare_for_vision_board.py script to create resources for the Vision & Mood-Board pipeline."""
    print_colored("Preparing resources for Vision & Mood-Board Creation...", "blue")
    
    try:
        subprocess.run([sys.executable, "prepare_for_vision_board.py"], check=True)
        print_colored("Resources prepared successfully!", "green")
        
        # Display the path to the vision board input
        script_dir = Path(__file__).parent.absolute()
        vb_input_path = script_dir / "output" / "vision_board_input" / "vision_board_input.json"
        
        if vb_input_path.exists():
            print_colored(f"Vision & Mood-Board input file created: {vb_input_path}", "white")
            print_colored(f"This file contains a structured resource pool optimized for the Vision & Mood-Board Creation pipeline.", "white")
            print_colored(f"It includes hierarchical knowledge structure, key entities, visual resources, conceptual maps, and temporal progression.", "white")
        
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"Error preparing Vision & Mood-Board resources: {str(e)}", "red")
        return False

def run_all_pipeline():
    """Run the complete pipeline."""
    print_colored("Running the complete pipeline...", "cyan")
    subprocess.run([sys.executable, "run_enhanced_pipeline.py"], check=True)
    print_colored("Complete pipeline execution finished", "green")

def run_regenerate_visualization():
    """Regenerate knowledge graph visualizations with enhanced tree structure without regenerating the knowledge graph."""
    print_colored("Regenerating enhanced tree-like knowledge graph visualization...", "cyan")
    
    # Try to load existing knowledge graph
    script_dir = Path(__file__).parent.absolute()
    kg_path = script_dir / "output" / "knowledge_graph" / "knowledge_graph.json"
    
    if not kg_path.exists():
        print_colored("No existing knowledge graph found. Please run the knowledge graph generation first.", "red")
        return None
    
    try:
        with open(kg_path, 'r', encoding='utf-8') as f:
            knowledge_graph = json.load(f)
        print_colored("Loaded existing knowledge graph from file", "yellow")
    except Exception as e:
        print_colored(f"Error loading knowledge graph: {str(e)}", "red")
        return None
    
    # Import the KnowledgeGraphVisualizer directly from the module
    try:
        from core.pipeline.visualization import KnowledgeGraphVisualizer
        
        # Create visualizer with enhanced tree layout configuration
        visualizer = KnowledgeGraphVisualizer()
        output_dir = script_dir / "output" / "visualizations"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate interactive HTML visualization
        print_colored("Generating enhanced tree-like interactive visualization...", "blue")
        interactive_path = visualizer.create_interactive_visualization(
            knowledge_graph, 
            str(output_dir),
            filename="knowledge_graph_interactive.html"
        )
        
        # Generate static PNG visualization
        print_colored("Generating static visualization...", "blue")
        static_path = visualizer.create_static_visualization(
            knowledge_graph, 
            str(output_dir),
            filename="knowledge_graph_static.png"
        )
        
        # Open the visualization
        vis_path = output_dir / "knowledge_graph_interactive.html"
        if vis_path.exists():
            print_colored(f"Opening visualization: {vis_path}", "cyan")
            webbrowser.open(vis_path.as_uri())
        
        print_colored("Enhanced tree-like visualization regenerated successfully", "green")
        print_colored(f"- Interactive visualization: {interactive_path}", "green")
        print_colored(f"- Static visualization: {static_path}", "green")
        
        return {
            "interactive": interactive_path,
            "static": static_path
        }
        
    except Exception as e:
        print_colored(f"Error regenerating visualization: {str(e)}", "red")
        traceback.print_exc()
        return None

def run_multi_level_visualization():
    """
    Run the multi-level visualization component.
    
    This creates a hierarchical visualization of the knowledge graph with different
    levels of detail:
    - Overview level showing domains and main modules
    - Module level showing modules and their topics
    - Topic level showing detailed views of individual topics
    
    Returns:
        Path to the main visualization file if successful, None otherwise
    """
    print_colored("Generating multi-level hierarchical knowledge graph visualization...", "blue")
    
    # Load existing knowledge graph if available
    script_dir = Path(__file__).resolve().parent
    kg_path = script_dir / "output" / "knowledge_graph" / "knowledge_graph.json"
    
    if not kg_path.exists():
        print_colored("No existing knowledge graph found. Please run the knowledge graph generation first.", "red")
        return None
    
    try:
        with open(kg_path, 'r', encoding='utf-8') as f:
            knowledge_graph = json.load(f)
        print_colored("Loaded existing knowledge graph from file", "yellow")
    except Exception as e:
        print_colored(f"Error loading knowledge graph: {str(e)}", "red")
        return None
    
    # Import the KnowledgeGraphVisualizer directly from the module
    try:
        from core.pipeline.visualization import KnowledgeGraphVisualizer
        
        # Create visualizer with default configuration
        visualizer = KnowledgeGraphVisualizer()
        output_dir = script_dir / "output" / "visualizations"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate multi-level interactive HTML visualizations
        print_colored("Generating multi-level interactive visualizations...", "blue")
        output_file = visualizer.create_interactive_visualization(
            knowledge_graph, 
            str(output_dir),
            filename="knowledge_graph.html",
            height="800px",
            width="100%",
            layout_type="hierarchical",
            multi_level=True
        )
        
        # Open the overview visualization
        if output_file:
            print_colored(f"Multi-level visualization generated successfully:", "green")
            print_colored(f"Overview visualization: {output_file}", "green")
            print_colored(f"You can find all visualizations in: {os.path.dirname(output_file)}", "green")
            return output_file
        else:
            print_colored("Failed to generate multi-level visualization.", "red")
            return None
    except Exception as e:
        print_colored(f"Error generating multi-level visualization: {str(e)}", "red")
        traceback.print_exc()
        return None

def main():
    """Parse arguments and run the appropriate component."""
    parser = argparse.ArgumentParser(description="Run specific components of the material ingestion pipeline")
    parser.add_argument("component", choices=[
        "fix", "context", "transcripts", "slides", "fusion", "supervise", 
        "knowledge_graph", "visualize", "regenerate_visualization", "multi_level_visualization", "embeddings", "vision_board", "all"
    ], help="The component to run")
    
    args = parser.parse_args()
    
    # Execute the appropriate component
    components = {
        "fix": run_fix,
        "context": run_extract_course_context,
        "transcripts": run_process_transcripts,
        "slides": run_process_slides,
        "fusion": run_generate_fused_context,
        "supervise": run_supervise_outputs,
        "knowledge_graph": run_generate_knowledge_graph,
        "visualize": run_visualize_knowledge_graph,
        "regenerate_visualization": run_regenerate_visualization,
        "multi_level_visualization": run_multi_level_visualization,
        "embeddings": run_generate_embeddings,
        "vision_board": run_prepare_vision_board,
        "all": run_all_pipeline
    }
    
    try:
        if args.component in components:
            components[args.component]()
        else:
            print_colored(f"Unknown component: {args.component}", "red")
            print_colored(f"Available components: {', '.join(components.keys())}", "yellow")
    except Exception as e:
        print_colored(f"Error running component '{args.component}': {str(e)}", "red")
        traceback.print_exc()

if __name__ == "__main__":
    main() 