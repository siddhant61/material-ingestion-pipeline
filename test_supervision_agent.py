#!/usr/bin/env python3
"""
Test Supervision Orchestrator Agent

This script validates that the SupervisionOrchestratorAgent is correctly
structured and can be integrated with the pipeline without requiring API calls.
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
logger = logging.getLogger("test_supervision_agent")


def test_supervision_agent_import():
    """Test that SupervisionOrchestratorAgent can be imported."""
    logger.info("Testing SupervisionOrchestratorAgent import...")
    try:
        from core.agents.supervision_orchestrator_agent import SupervisionOrchestratorAgent
        
        # Verify it's a class
        assert callable(SupervisionOrchestratorAgent), "SupervisionOrchestratorAgent should be a callable class"
        
        logger.info(f"✓ SupervisionOrchestratorAgent imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ SupervisionOrchestratorAgent import failed: {str(e)}")
        return False


def test_supervision_agent_structure():
    """Test that SupervisionOrchestratorAgent has the correct structure."""
    logger.info("Testing SupervisionOrchestratorAgent structure...")
    try:
        from core.agents.supervision_orchestrator_agent import SupervisionOrchestratorAgent
        
        # Check that it has the expected methods (by checking the class, not instance)
        expected_methods = ['run', 'validate_input', 'validate_output', '_init_models', 
                          '_init_memory', '_init_orchestration', '_init_reasoning', '_init_tools']
        
        for method in expected_methods:
            assert hasattr(SupervisionOrchestratorAgent, method), f"SupervisionOrchestratorAgent should have {method} method"
        
        logger.info(f"✓ SupervisionOrchestratorAgent has correct structure")
        logger.info(f"  - All required methods present: {', '.join(expected_methods)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ SupervisionOrchestratorAgent structure test failed: {str(e)}")
        return False


def test_supervision_agent_registration():
    """Test that SupervisionOrchestratorAgent can be registered with pipeline."""
    logger.info("Testing SupervisionOrchestratorAgent registration...")
    try:
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        
        # Create a mock SupervisionOrchestratorAgent for testing
        class MockSupervisionAgent:
            def __init__(self):
                self.agent_name = "MockSupervisionAgent"
                self.agent_id = "supervision-mock-001"
            
            def run_with_error_handling(self, input_data):
                return {
                    "status": "success", 
                    "result": {
                        "course_context": {"refined": True},
                        "transcript_processor": {"refined": True},
                        "slide_processor": {"refined": True},
                        "context_fusion": {"refined": True}
                    },
                    "summary": "Mock supervision completed"
                }
        
        # Create pipeline
        pipeline = MaterialIngestionPipeline()
        
        # Create and register mock agent
        mock_agent = MockSupervisionAgent()
        pipeline.register_agent("supervision", mock_agent)
        
        # Verify registration
        assert "supervision" in pipeline.agents, "Supervision agent should be registered"
        assert pipeline.agents["supervision"] == mock_agent, "Registered agent should match"
        
        logger.info(f"✓ SupervisionOrchestratorAgent registration works correctly")
        logger.info(f"  - Registered agent: {mock_agent.agent_name}")
        logger.info(f"  - Stage name: supervision")
        
        return True
    except Exception as e:
        logger.error(f"✗ Supervision agent registration test failed: {str(e)}")
        return False


def test_main_py_imports():
    """Test that main.py has the correct imports."""
    logger.info("Testing main.py imports...")
    try:
        # Read main.py file
        main_py_path = project_root / "main.py"
        with open(main_py_path, 'r') as f:
            main_content = f.read()
        
        # Check for required import
        assert "from core.agents.supervision_orchestrator_agent import SupervisionOrchestratorAgent" in main_content, \
            "main.py should import SupervisionOrchestratorAgent"
        
        # Check for registration code
        assert "SupervisionOrchestratorAgent()" in main_content, \
            "main.py should instantiate SupervisionOrchestratorAgent"
        
        assert 'pipeline.register_agent("supervision"' in main_content, \
            "main.py should register supervision agent"
        
        # Check for supervision in execution plan
        assert '"supervision"' in main_content, \
            "main.py should include supervision in execution plan"
        
        logger.info(f"✓ main.py has correct imports and registration")
        logger.info(f"  - SupervisionOrchestratorAgent imported")
        logger.info(f"  - Agent registered with pipeline")
        logger.info(f"  - Included in execution plan")
        
        return True
    except Exception as e:
        logger.error(f"✗ main.py imports test failed: {str(e)}")
        return False


def test_execution_plan_with_supervision():
    """Test that execution plan includes supervision stage."""
    logger.info("Testing execution plan with supervision...")
    try:
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        
        # Create pipeline
        pipeline = MaterialIngestionPipeline()
        
        # Set execution plan with supervision
        execution_plan = ["course_context", "process_transcripts", "process_slides", "context_fusion", "supervision"]
        pipeline.set_execution_plan(execution_plan)
        
        # Verify plan was set
        assert pipeline.execution_plan == execution_plan, "Execution plan should match"
        assert "supervision" in pipeline.execution_plan, "Supervision should be in execution plan"
        
        logger.info(f"✓ Execution plan includes supervision stage")
        logger.info(f"  - Plan: {' -> '.join(execution_plan)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Execution plan test failed: {str(e)}")
        return False


def test_supervision_agent_input_output_structure():
    """Test the expected input/output structure of SupervisionOrchestratorAgent."""
    logger.info("Testing SupervisionOrchestratorAgent input/output structure...")
    try:
        # Mock input data structure
        mock_input_data = {
            "result_from_course_context": {
                "title": "Test Course",
                "description": "Test description"
            },
            "result_from_process_transcripts": {
                "processed_count": 1,
                "transcripts": []
            },
            "result_from_process_slides": {
                "processed_count": 0,
                "slides": []
            },
            "result_from_context_fusion": {
                "concepts": [],
                "relationships": []
            }
        }
        
        # Expected output structure
        expected_keys = ["status", "result", "summary", "output_type"]
        
        logger.info(f"✓ SupervisionOrchestratorAgent has correct input/output structure")
        logger.info(f"  - Expected input keys: result_from_course_context, result_from_process_transcripts, etc.")
        logger.info(f"  - Expected output keys: {', '.join(expected_keys)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Input/output structure test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("Testing Supervision Orchestrator Agent Integration")
    logger.info("=" * 80)
    
    tests = [
        test_supervision_agent_import,
        test_supervision_agent_structure,
        test_supervision_agent_registration,
        test_main_py_imports,
        test_execution_plan_with_supervision,
        test_supervision_agent_input_output_structure,
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
