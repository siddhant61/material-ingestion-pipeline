#!/usr/bin/env python3
"""
Test API Structure

This script validates that the API is correctly set up and can be imported
without errors. It tests the API endpoint structure without running the full pipeline.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_api")


def test_fastapi_import():
    """Test that FastAPI library can be imported."""
    logger.info("Testing FastAPI library import...")
    try:
        import fastapi
        logger.info(f"✓ FastAPI library imported successfully")
        logger.info(f"  - FastAPI version: {fastapi.__version__}")
        return True
    except ImportError as e:
        logger.error(f"✗ FastAPI import failed: {e}")
        return False


def test_uvicorn_import():
    """Test that uvicorn library can be imported."""
    logger.info("Testing uvicorn library import...")
    try:
        import uvicorn
        logger.info(f"✓ Uvicorn library imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Uvicorn import failed: {e}")
        return False


def test_api_import():
    """Test that the API module can be imported."""
    logger.info("Testing API import...")
    try:
        import api
        logger.info("✓ API module imported successfully")
        
        # Check that the app exists
        if hasattr(api, 'app'):
            logger.info("  - FastAPI app instance found")
        else:
            logger.warning("  - FastAPI app instance not found")
            return False
            
        return True
    except Exception as e:
        logger.error(f"✗ API import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_models():
    """Test that the API models are correctly defined."""
    logger.info("Testing API models...")
    try:
        from api import PipelineRunRequest, PipelineRunResponse, PipelineStatusResponse
        
        # Test PipelineRunRequest
        request = PipelineRunRequest(input_dir="./test_input", output_dir="./test_output")
        assert request.input_dir == "./test_input"
        assert request.output_dir == "./test_output"
        logger.info("  - PipelineRunRequest model validated")
        
        # Test PipelineRunResponse
        response = PipelineRunResponse(
            run_id="test_run_123",
            message="Test message",
            input_dir="./test_input",
            output_dir="./test_output"
        )
        assert response.run_id == "test_run_123"
        logger.info("  - PipelineRunResponse model validated")
        
        # Test PipelineStatusResponse
        status = PipelineStatusResponse(
            run_id="test_run_123",
            status="running",
            message="Pipeline is running"
        )
        assert status.status == "running"
        logger.info("  - PipelineStatusResponse model validated")
        
        logger.info("✓ API models validated successfully")
        return True
    except Exception as e:
        logger.error(f"✗ API models validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test that the API endpoints are defined."""
    logger.info("Testing API endpoints...")
    try:
        from api import app
        
        # Get all routes
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/",
            "/run",
            "/status/{run_id}",
            "/results/{run_id}/visualization",
            "/results/{run_id}/report",
            "/health"
        ]
        
        for expected_route in expected_routes:
            if expected_route in routes:
                logger.info(f"  - ✓ Endpoint {expected_route} found")
            else:
                logger.warning(f"  - ✗ Endpoint {expected_route} not found")
                return False
        
        logger.info("✓ API endpoints validated successfully")
        return True
    except Exception as e:
        logger.error(f"✗ API endpoints validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_helper_functions():
    """Test that helper functions are defined."""
    logger.info("Testing helper functions...")
    try:
        from api import setup_sample_files, update_settings_paths, run_pipeline_in_background
        
        logger.info("  - setup_sample_files function found")
        logger.info("  - update_settings_paths function found")
        logger.info("  - run_pipeline_in_background function found")
        
        logger.info("✓ Helper functions validated successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Helper functions validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all API structure tests."""
    logger.info("=" * 80)
    logger.info("Testing API Structure")
    logger.info("=" * 80)
    
    tests = [
        ("FastAPI Import", test_fastapi_import),
        ("Uvicorn Import", test_uvicorn_import),
        ("API Import", test_api_import),
        ("API Models", test_api_models),
        ("API Endpoints", test_api_endpoints),
        ("Helper Functions", test_helper_functions),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        logger.info("-" * 80)
        results[test_name] = test_func()
        logger.info("")
    
    # Print summary
    logger.info("=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 80)
    passed = sum(results.values())
    total = len(results)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
