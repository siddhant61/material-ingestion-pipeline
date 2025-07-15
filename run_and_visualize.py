#!/usr/bin/env python3
"""
Run Pipeline and Open Visualization

This script runs the material ingestion pipeline and automatically opens
the generated knowledge graph visualization in a web browser when finished.

Usage:
    python run_and_visualize.py [--prepare-vision-board]
"""

import os
import sys
import subprocess
import time
import webbrowser
import argparse
from pathlib import Path

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
        "end": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['end']}")

def run_pipeline():
    """Run the complete pipeline."""
    print_colored("Running material ingestion pipeline...", "blue")
    
    # Run the pipeline
    try:
        subprocess.run([sys.executable, "run_enhanced_pipeline.py"], check=True)
        print_colored("Pipeline execution completed successfully!", "green")
        return True
    except subprocess.CalledProcessError:
        print_colored("Pipeline execution failed. Check the logs for details.", "red")
        return False

def open_visualization():
    """Open the knowledge graph visualization in a web browser."""
    script_dir = Path(__file__).parent.absolute()
    vis_path = script_dir / "output" / "visualizations" / "knowledge_graph_interactive.html"
    
    if vis_path.exists():
        vis_path_str = str(vis_path)
        print_colored(f"Opening visualization: {vis_path_str}", "green")
        
        # Open the visualization in the default web browser
        webbrowser.open(f"file://{vis_path_str}")
        print_colored("Visualization opened in your default web browser", "green")
        return True
    else:
        print_colored(f"Visualization file not found: {vis_path}", "red")
        return False

def show_additional_outputs():
    """Display paths to additional outputs."""
    script_dir = Path(__file__).parent.absolute()
    kg_path = script_dir / "output" / "knowledge_graph" / "knowledge_graph.json"
    static_vis_path = script_dir / "output" / "visualizations" / "knowledge_graph_static.png"
    embeddings_path = script_dir / "output" / "embeddings" / "embeddings.json"
    pipeline_report_path = script_dir / "output" / "pipeline_report.json"
    
    print_colored("Additional Outputs:", "yellow")
    print_colored(f"- Knowledge Graph JSON: {kg_path}", "white")
    print_colored(f"- Static Visualization: {static_vis_path}", "white")
    print_colored(f"- Embeddings: {embeddings_path}", "white")
    print_colored(f"- Pipeline Report: {pipeline_report_path}", "white")

def prepare_vision_board_resources():
    """Prepare resources for the Vision & Mood-Board Creation pipeline."""
    print_colored("\nPreparing resources for Vision & Mood-Board Creation...", "blue")
    
    try:
        subprocess.run([sys.executable, "prepare_for_vision_board.py"], check=True)
        print_colored("Resources prepared successfully!", "green")
        
        # Show the path to the vision board input
        script_dir = Path(__file__).parent.absolute()
        vb_input_path = script_dir / "output" / "vision_board_input" / "vision_board_input.json"
        
        if vb_input_path.exists():
            print_colored(f"Vision & Mood-Board input file: {vb_input_path}", "white")
            
        return True
    except subprocess.CalledProcessError:
        print_colored("Failed to prepare Vision & Mood-Board resources. Check the logs for details.", "red")
        return False

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run pipeline and open visualization")
    parser.add_argument("--prepare-vision-board", action="store_true", 
                        help="Prepare resources for Vision & Mood-Board Creation after running the pipeline")
    args = parser.parse_args()
    
    # Print header
    print_colored("=" * 80, "blue")
    print_colored("Material Ingestion Pipeline with Visualization", "cyan")
    print_colored("=" * 80, "blue")
    
    # Run the pipeline
    if not run_pipeline():
        return
    
    # Wait a moment for files to be properly saved
    time.sleep(1)
    
    # Open the visualization
    open_visualization()
    
    # Show additional outputs
    show_additional_outputs()
    
    # Prepare Vision & Mood-Board resources if requested
    if args.prepare_vision_board:
        prepare_vision_board_resources()
    
    print_colored("Process completed successfully!", "green")
    print_colored("=" * 80, "blue")

if __name__ == "__main__":
    main() 