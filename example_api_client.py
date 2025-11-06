#!/usr/bin/env python3
"""
Example API Client

This script demonstrates how to use the Material Ingestion Pipeline API
to start a pipeline run, monitor its progress, and retrieve results.

Usage:
    python example_api_client.py

Prerequisites:
    - The API server must be running: uvicorn api:app --reload
    - Install requests: pip install requests
"""

import requests
import time
import json
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
INPUT_DIR = "./input"
OUTPUT_DIR = "./output_api_test"
POLL_INTERVAL = 10  # seconds


def start_pipeline_run(input_dir: str, output_dir: str) -> dict:
    """
    Start a new pipeline run.
    
    Args:
        input_dir: Path to input directory with course materials
        output_dir: Path to output directory for results
        
    Returns:
        Dictionary with run information including run_id
    """
    print(f"\n{'='*80}")
    print("Starting Pipeline Run")
    print(f"{'='*80}")
    print(f"Input Directory: {input_dir}")
    print(f"Output Directory: {output_dir}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/run",
            json={
                "input_dir": input_dir,
                "output_dir": output_dir
            },
            timeout=10
        )
        response.raise_for_status()
        
        run_data = response.json()
        print(f"\n✓ Pipeline run started successfully!")
        print(f"Run ID: {run_data['run_id']}")
        print(f"Message: {run_data['message']}")
        
        return run_data
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Failed to start pipeline run: {e}")
        sys.exit(1)


def check_pipeline_status(run_id: str) -> dict:
    """
    Check the status of a pipeline run.
    
    Args:
        run_id: Unique identifier for the pipeline run
        
    Returns:
        Dictionary with status information
    """
    try:
        response = requests.get(f"{API_BASE_URL}/status/{run_id}", timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Failed to check status: {e}")
        return None


def wait_for_completion(run_id: str, poll_interval: int = 10) -> dict:
    """
    Poll the API until the pipeline run completes.
    
    Args:
        run_id: Unique identifier for the pipeline run
        poll_interval: Seconds to wait between status checks
        
    Returns:
        Final status information
    """
    print(f"\n{'='*80}")
    print("Monitoring Pipeline Progress")
    print(f"{'='*80}")
    print(f"Polling every {poll_interval} seconds...")
    print("Press Ctrl+C to stop monitoring (pipeline will continue running)")
    
    start_time = time.time()
    
    try:
        while True:
            status_data = check_pipeline_status(run_id)
            
            if status_data is None:
                print("\n✗ Lost connection to API")
                sys.exit(1)
            
            status = status_data["status"]
            message = status_data["message"]
            elapsed = int(time.time() - start_time)
            
            # Print status update
            status_symbol = {
                "initializing": "⏳",
                "running": "🔄",
                "complete": "✓",
                "error": "✗"
            }.get(status, "?")
            
            print(f"\r{status_symbol} Status: {status:12} | Elapsed: {elapsed:4}s | {message}", end="")
            
            # Check if complete or failed
            if status == "complete":
                print(f"\n\n✓ Pipeline completed successfully!")
                print(f"Total execution time: {elapsed} seconds")
                return status_data
                
            elif status == "error":
                print(f"\n\n✗ Pipeline failed!")
                print(f"Error: {message}")
                return status_data
            
            # Wait before next check
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠ Monitoring stopped (pipeline continues in background)")
        print(f"You can check status later with: curl {API_BASE_URL}/status/{run_id}")
        sys.exit(0)


def download_visualization(run_id: str, output_path: str = "visualization.html"):
    """
    Download the visualization HTML file.
    
    Args:
        run_id: Unique identifier for the pipeline run
        output_path: Local path to save the visualization
    """
    print(f"\nDownloading visualization...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/results/{run_id}/visualization", timeout=30)
        response.raise_for_status()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        print(f"✓ Visualization saved to: {output_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download visualization: {e}")
        return False


def download_report(run_id: str, output_path: str = "pipeline_report.json"):
    """
    Download the pipeline execution report.
    
    Args:
        run_id: Unique identifier for the pipeline run
        output_path: Local path to save the report
    """
    print(f"Downloading report...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/results/{run_id}/report", timeout=30)
        response.raise_for_status()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, indent=2)
        
        print(f"✓ Report saved to: {output_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download report: {e}")
        return False


def check_api_health():
    """Check if the API is running and healthy."""
    print(f"\n{'='*80}")
    print("Checking API Health")
    print(f"{'='*80}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        
        health_data = response.json()
        print(f"✓ API is healthy")
        print(f"Service: {health_data['service']}")
        print(f"Version: {health_data['version']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ API is not responding: {e}")
        print(f"\nPlease start the API server with: uvicorn api:app --reload")
        return False


def main():
    """Main execution flow."""
    print(f"\n{'='*80}")
    print("Material Ingestion Pipeline - API Client Example")
    print(f"{'='*80}")
    
    # Check API health
    if not check_api_health():
        sys.exit(1)
    
    # Start pipeline run
    run_data = start_pipeline_run(INPUT_DIR, OUTPUT_DIR)
    run_id = run_data["run_id"]
    
    # Wait for completion
    final_status = wait_for_completion(run_id, POLL_INTERVAL)
    
    # Download results if successful
    if final_status["status"] == "complete":
        print(f"\n{'='*80}")
        print("Downloading Results")
        print(f"{'='*80}")
        
        download_visualization(run_id, "api_visualization.html")
        download_report(run_id, "api_pipeline_report.json")
        
        print(f"\n{'='*80}")
        print("Pipeline Run Complete!")
        print(f"{'='*80}")
        print(f"Run ID: {run_id}")
        print(f"Output Directory: {final_status['output_dir']}")
        print(f"\nYou can view the visualization by opening: api_visualization.html")
        print(f"Full pipeline report available in: api_pipeline_report.json")
    
    else:
        print(f"\n{'='*80}")
        print("Pipeline Run Failed")
        print(f"{'='*80}")
        print(f"Run ID: {run_id}")
        print(f"Check the API logs for more details")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
