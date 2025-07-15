#!/usr/bin/env python3
"""
Prepare for Vision & Mood-Board Creation

This script prepares the outputs from the material ingestion pipeline for the
Vision & Mood-Board Creation pipeline by generating an optimized resource pool.

Usage:
    python prepare_for_vision_board.py [--kg_path PATH] [--emb_path PATH] [--output_dir PATH]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vision_board_preparation")

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import from the core module
from core.pipeline import PipelineIntegrator, create_vision_board_input


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


def prepare_resources(kg_path=None, emb_path=None, output_dir=None):
    """Prepare resources for the Vision & Mood-Board Creation pipeline.
    
    Args:
        kg_path: Path to the knowledge graph JSON file
        emb_path: Path to the embeddings JSON file
        output_dir: Directory to save the output
        
    Returns:
        Path to the created resource pool file
    """
    # Set default paths if not provided
    if kg_path is None:
        kg_path = os.path.join(project_root, "output", "knowledge_graph", "knowledge_graph.json")
    
    if emb_path is None:
        emb_path = os.path.join(project_root, "output", "embeddings", "embeddings.json")
    
    if output_dir is None:
        output_dir = os.path.join(project_root, "output", "vision_board_input")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if input files exist
    if not os.path.exists(kg_path):
        logger.error(f"Knowledge graph file not found: {kg_path}")
        return None
        
    if not os.path.exists(emb_path):
        logger.error(f"Embeddings file not found: {emb_path}")
        return None
    
    print_colored(f"Creating resource pool for Vision & Mood-Board Creation...", "blue")
    
    try:
        # Generate the resource pool
        output_path = create_vision_board_input(
            knowledge_graph_path=kg_path,
            embeddings_path=emb_path,
            output_dir=output_dir
        )
        
        print_colored(f"Resource pool created successfully: {output_path}", "green")
        print_colored("\nThis file contains:", "yellow")
        print_colored("1. Hierarchical knowledge structure", "white")
        print_colored("2. Key entity identification", "white")
        print_colored("3. Visual resource index", "white")
        print_colored("4. Conceptual relationships map", "white")
        print_colored("5. Temporal progression of concepts", "white")
        print_colored("6. Complete knowledge graph data", "white")
        print_colored("7. Entity embeddings for semantic search", "white")
        
        print_colored("\nThe Vision & Mood-Board Creation pipeline can now use this", "cyan")
        print_colored("resource pool as input to generate mood boards.", "cyan")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error preparing resources: {str(e)}")
        return None


def main():
    """Main function to parse arguments and prepare resources."""
    parser = argparse.ArgumentParser(description="Prepare resources for Vision & Mood-Board Creation")
    
    parser.add_argument("--kg_path", type=str, 
                        help="Path to the knowledge graph JSON file")
    parser.add_argument("--emb_path", type=str, 
                        help="Path to the embeddings JSON file")
    parser.add_argument("--output_dir", type=str, 
                        help="Directory to save the output")
    
    args = parser.parse_args()
    
    # Call the prepare_resources function with the provided arguments
    output_path = prepare_resources(
        kg_path=args.kg_path,
        emb_path=args.emb_path,
        output_dir=args.output_dir
    )
    
    # Return success code if successful
    if output_path:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main() 