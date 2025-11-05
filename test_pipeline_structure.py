#!/usr/bin/env python3
"""
Test Pipeline Structure

This script validates that the pipeline structure is correctly set up
without requiring OpenAI API calls. It tests the initialization and
registration of agents with the pipeline orchestrator.
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
logger = logging.getLogger("test_pipeline_structure")


def test_config_import():
    """Test that configuration can be imported and initialized."""
    logger.info("Testing configuration import...")
    try:
        from core.config import settings
        
        # Verify settings object exists
        assert settings is not None, "Settings object should not be None"
        
        # Verify key attributes exist
        assert hasattr(settings, 'input_dir'), "Settings should have input_dir"
        assert hasattr(settings, 'output_dir'), "Settings should have output_dir"
        assert hasattr(settings, 'course_info_dir'), "Settings should have course_info_dir"
        
        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  - Input dir: {settings.input_dir}")
        logger.info(f"  - Output dir: {settings.output_dir}")
        logger.info(f"  - Course info dir: {settings.course_info_dir}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Configuration import failed: {str(e)}")
        return False


def test_pipeline_import():
    """Test that MaterialIngestionPipeline can be imported."""
    logger.info("Testing pipeline import...")
    try:
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        
        # Create a simple pipeline instance
        pipeline = MaterialIngestionPipeline()
        
        # Verify pipeline object exists and has expected methods
        assert pipeline is not None, "Pipeline should not be None"
        assert hasattr(pipeline, 'register_agent'), "Pipeline should have register_agent method"
        assert hasattr(pipeline, 'set_execution_plan'), "Pipeline should have set_execution_plan method"
        assert hasattr(pipeline, 'run'), "Pipeline should have run method"
        
        logger.info(f"✓ MaterialIngestionPipeline imported and initialized successfully")
        logger.info(f"  - Pipeline ID: {pipeline.pipeline_id}")
        logger.info(f"  - Version: {pipeline.version}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Pipeline import failed: {str(e)}")
        return False


def test_agent_structure():
    """Test that ContextAgent has the correct structure."""
    logger.info("Testing ContextAgent structure...")
    try:
        from core.agents.context_agent import ContextAgent
        from core.config import settings
        
        # Create an agent instance with configuration
        # Note: This will fail if OpenAI API key is required, but we can at least
        # test that the class can be imported and has the right structure
        logger.info("  - ContextAgent class imported successfully")
        
        # Verify it's a class
        assert callable(ContextAgent), "ContextAgent should be a callable class"
        
        # Check that it has the expected methods (by checking the class, not instance)
        expected_methods = ['run', 'validate_input', 'validate_output', '_init_models', 
                          '_init_memory', '_init_orchestration', '_init_reasoning', '_init_tools']
        
        for method in expected_methods:
            assert hasattr(ContextAgent, method), f"ContextAgent should have {method} method"
        
        logger.info(f"✓ ContextAgent has correct structure")
        logger.info(f"  - All required methods present: {', '.join(expected_methods)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ ContextAgent structure test failed: {str(e)}")
        return False


def test_pipeline_registration():
    """Test that agents can be registered with the pipeline."""
    logger.info("Testing agent registration with pipeline...")
    try:
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        
        # Create a mock agent for testing registration
        class MockAgent:
            def __init__(self):
                self.agent_name = "MockAgent"
                self.agent_id = "mock-001"
            
            def run_with_error_handling(self, input_data):
                return {"status": "success", "result": "Mock result"}
        
        # Create pipeline
        pipeline = MaterialIngestionPipeline()
        
        # Create and register mock agent
        mock_agent = MockAgent()
        pipeline.register_agent("test_stage", mock_agent)
        
        # Verify registration
        assert "test_stage" in pipeline.agents, "Agent should be registered"
        assert pipeline.agents["test_stage"] == mock_agent, "Registered agent should match"
        
        logger.info(f"✓ Agent registration works correctly")
        logger.info(f"  - Registered agent: {mock_agent.agent_name}")
        logger.info(f"  - Stage name: test_stage")
        
        return True
    except Exception as e:
        logger.error(f"✗ Agent registration test failed: {str(e)}")
        return False


def test_execution_plan():
    """Test that execution plan can be set."""
    logger.info("Testing execution plan setup...")
    try:
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        
        # Create pipeline
        pipeline = MaterialIngestionPipeline()
        
        # Set execution plan
        execution_plan = ["course_context", "transcripts", "slides"]
        pipeline.set_execution_plan(execution_plan)
        
        # Verify plan was set
        assert pipeline.execution_plan == execution_plan, "Execution plan should match"
        
        logger.info(f"✓ Execution plan set successfully")
        logger.info(f"  - Plan: {' -> '.join(execution_plan)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Execution plan test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("Testing Pipeline Structure")
    logger.info("=" * 80)
    
    tests = [
        test_config_import,
        test_pipeline_import,
        test_agent_structure,
        test_pipeline_registration,
        test_execution_plan,
    ]
    
    results = []
    for test in tests:
        logger.info("")
        result = test()
        results.append(result)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.info(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
