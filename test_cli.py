#!/usr/bin/env python3
"""
Test CLI Structure

This script validates that the CLI is correctly set up and can be imported
without errors. It tests the CLI command structure without running the full pipeline.
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
logger = logging.getLogger("test_cli")


def test_cli_import():
    """Test that CLI module can be imported."""
    logger.info("Testing CLI import...")
    try:
        import cli
        
        # Verify cli module exists
        assert cli is not None, "CLI module should not be None"
        
        # Verify main CLI function exists
        assert hasattr(cli, 'cli'), "CLI should have cli function"
        assert hasattr(cli, 'run_pipeline'), "CLI should have run_pipeline command"
        
        logger.info("✓ CLI module imported successfully")
        return True
    except Exception as e:
        logger.error(f"✗ CLI import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_click_import():
    """Test that click library is available."""
    logger.info("Testing click library import...")
    try:
        import click
        
        # Verify click module exists
        assert click is not None, "Click module should not be None"
        
        logger.info("✓ Click library imported successfully")
        logger.info(f"  - Click version: {click.__version__}")
        return True
    except Exception as e:
        logger.error(f"✗ Click library import failed: {str(e)}")
        return False


def test_settings_update():
    """Test that settings can be updated with custom paths."""
    logger.info("Testing settings update functionality...")
    try:
        from cli import update_settings_paths
        from core.config import settings
        
        # Get original paths
        original_input_dir = settings.input_dir
        original_output_dir = settings.output_dir
        
        # Test updating paths
        test_input = "/tmp/test_cli_input"
        test_output = "/tmp/test_cli_output"
        
        update_settings_paths(test_input, test_output)
        
        # Verify paths were updated
        assert str(settings.input_dir) == test_input, f"Input dir should be {test_input}, got {settings.input_dir}"
        assert str(settings.output_dir) == test_output, f"Output dir should be {test_output}, got {settings.output_dir}"
        
        # Verify dependent paths were updated correctly
        assert str(settings.course_info_dir) == f"{test_input}/course_material/course_info"
        assert str(settings.transcripts_dir) == f"{test_input}/course_material/transcripts"
        assert str(settings.knowledge_graph_dir) == f"{test_output}/knowledge_graph"
        
        logger.info("✓ Settings update functionality works correctly")
        logger.info(f"  - Input dir updated to: {settings.input_dir}")
        logger.info(f"  - Output dir updated to: {settings.output_dir}")
        logger.info(f"  - Course info dir: {settings.course_info_dir}")
        logger.info(f"  - Knowledge graph dir: {settings.knowledge_graph_dir}")
        
        # Restore original paths
        update_settings_paths(str(original_input_dir), str(original_output_dir))
        
        return True
    except Exception as e:
        logger.error(f"✗ Settings update test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("Testing CLI Structure")
    logger.info("=" * 80)
    
    tests = [
        ("Click Import", test_click_import),
        ("CLI Import", test_cli_import),
        ("Settings Update", test_settings_update),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        logger.info("-" * 80)
        results[test_name] = test_func()
        logger.info("")
    
    # Summary
    logger.info("=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 80)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
