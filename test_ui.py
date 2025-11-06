#!/usr/bin/env python3
"""
Test UI Structure

This script validates that the UI file is correctly set up and can be imported
without errors. It tests the UI structure and dependencies.
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
logger = logging.getLogger("test_ui")


def test_streamlit_import():
    """Test that Streamlit library can be imported."""
    logger.info("Testing Streamlit library import...")
    try:
        import streamlit
        logger.info(f"✓ Streamlit library imported successfully")
        logger.info(f"  - Streamlit version: {streamlit.__version__}")
        return True
    except ImportError as e:
        logger.error(f"✗ Streamlit import failed: {e}")
        logger.error("  Please install streamlit: pip install streamlit>=1.28.0")
        return False


def test_requests_import():
    """Test that requests library can be imported."""
    logger.info("Testing requests library import...")
    try:
        import requests
        logger.info(f"✓ Requests library imported successfully")
        logger.info(f"  - Requests version: {requests.__version__}")
        return True
    except ImportError as e:
        logger.error(f"✗ Requests import failed: {e}")
        return False


def test_ui_file_exists():
    """Test that the UI file exists."""
    logger.info("Testing UI file existence...")
    ui_file = project_root / "ui.py"
    
    if ui_file.exists():
        logger.info(f"✓ UI file found at: {ui_file}")
        return True
    else:
        logger.error(f"✗ UI file not found at: {ui_file}")
        return False


def test_ui_imports():
    """Test that all required imports are present in ui.py."""
    logger.info("Testing UI imports...")
    try:
        ui_file = project_root / "ui.py"
        with open(ui_file, "r") as f:
            content = f.read()
        
        required_imports = [
            "import streamlit as st",
            "import requests",
            "import time",
            "import uuid",
        ]
        
        for required_import in required_imports:
            if required_import in content:
                logger.info(f"  - ✓ Found: {required_import}")
            else:
                logger.warning(f"  - ✗ Missing: {required_import}")
                return False
        
        logger.info("✓ All required imports found in ui.py")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to check UI imports: {e}")
        return False


def test_ui_components():
    """Test that key UI components are present in ui.py."""
    logger.info("Testing UI components...")
    try:
        ui_file = project_root / "ui.py"
        with open(ui_file, "r") as f:
            content = f.read()
        
        required_components = [
            "st.set_page_config",
            "st.title",
            "st.text_input",
            "st.button",
            "st.spinner",
            "st.success",
            "st.error",
            "st.components.v1.html",
            "requests.post",
            "requests.get",
        ]
        
        for component in required_components:
            if component in content:
                logger.info(f"  - ✓ Found: {component}")
            else:
                logger.warning(f"  - ✗ Missing: {component}")
                return False
        
        logger.info("✓ All required UI components found")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to check UI components: {e}")
        return False


def test_api_endpoints_referenced():
    """Test that the UI references the correct API endpoints."""
    logger.info("Testing API endpoint references...")
    try:
        ui_file = project_root / "ui.py"
        with open(ui_file, "r") as f:
            content = f.read()
        
        required_endpoints = [
            "/health",
            "/run",
            "/status/",
            "/results/",
            "/visualization",
        ]
        
        for endpoint in required_endpoints:
            if endpoint in content:
                logger.info(f"  - ✓ Found endpoint reference: {endpoint}")
            else:
                logger.warning(f"  - ✗ Missing endpoint reference: {endpoint}")
                return False
        
        logger.info("✓ All API endpoint references found")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to check API endpoints: {e}")
        return False


def test_session_state_usage():
    """Test that Streamlit session state is used correctly."""
    logger.info("Testing session state usage...")
    try:
        ui_file = project_root / "ui.py"
        with open(ui_file, "r") as f:
            content = f.read()
        
        session_state_keys = [
            "st.session_state.run_id",
            "st.session_state.output_dir",
            "st.session_state.input_dir",
        ]
        
        for key in session_state_keys:
            if key in content:
                logger.info(f"  - ✓ Found session state usage: {key}")
            else:
                logger.warning(f"  - ✗ Missing session state usage: {key}")
                return False
        
        logger.info("✓ Session state usage validated")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to check session state: {e}")
        return False


def test_ui_config():
    """Test that UI configuration is present."""
    logger.info("Testing UI configuration...")
    try:
        ui_file = project_root / "ui.py"
        with open(ui_file, "r") as f:
            content = f.read()
        
        config_items = [
            "API_BASE_URL",
            "page_title",
            "Material Ingestion Pipeline",
        ]
        
        for item in config_items:
            if item in content:
                logger.info(f"  - ✓ Found: {item}")
            else:
                logger.warning(f"  - ✗ Missing: {item}")
                return False
        
        logger.info("✓ UI configuration validated")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to check UI config: {e}")
        return False


def main():
    """Run all UI structure tests."""
    logger.info("=" * 80)
    logger.info("Testing UI Structure")
    logger.info("=" * 80)
    
    tests = [
        ("Streamlit Import", test_streamlit_import),
        ("Requests Import", test_requests_import),
        ("UI File Exists", test_ui_file_exists),
        ("UI Imports", test_ui_imports),
        ("UI Components", test_ui_components),
        ("API Endpoints Referenced", test_api_endpoints_referenced),
        ("Session State Usage", test_session_state_usage),
        ("UI Configuration", test_ui_config),
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
