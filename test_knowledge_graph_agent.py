#!/usr/bin/env python3
"""
Test Knowledge Graph Agent

This script validates that the KnowledgeGraphAgent is correctly
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
logger = logging.getLogger("test_knowledge_graph_agent")


def test_knowledge_graph_agent_import():
    """Test that KnowledgeGraphAgent can be imported."""
    logger.info("Testing KnowledgeGraphAgent import...")
    try:
        from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
        
        # Verify it's a class
        assert callable(KnowledgeGraphAgent), "KnowledgeGraphAgent should be a callable class"
        
        logger.info(f"✓ KnowledgeGraphAgent imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ KnowledgeGraphAgent import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph_agent_structure():
    """Test that KnowledgeGraphAgent has the correct structure."""
    logger.info("Testing KnowledgeGraphAgent structure...")
    try:
        from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
        
        # Check that it has the expected methods (by checking the class, not instance)
        expected_methods = ['run', 'validate_input', 'validate_output', '_init_models', 
                          '_init_memory', '_init_orchestration', '_init_reasoning', '_init_tools']
        
        for method_name in expected_methods:
            assert hasattr(KnowledgeGraphAgent, method_name), f"KnowledgeGraphAgent should have method: {method_name}"
        
        logger.info(f"✓ KnowledgeGraphAgent has all expected methods")
        
        return True
    except Exception as e:
        logger.error(f"✗ KnowledgeGraphAgent structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph_agent_inheritance():
    """Test that KnowledgeGraphAgent inherits from BaseAgent."""
    logger.info("Testing KnowledgeGraphAgent inheritance...")
    try:
        from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
        from core.agents.base_agent import BaseAgent
        
        # Verify it inherits from BaseAgent
        assert issubclass(KnowledgeGraphAgent, BaseAgent), "KnowledgeGraphAgent should inherit from BaseAgent"
        
        logger.info(f"✓ KnowledgeGraphAgent correctly inherits from BaseAgent")
        
        return True
    except Exception as e:
        logger.error(f"✗ KnowledgeGraphAgent inheritance test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph_agent_registration():
    """Test that KnowledgeGraphAgent can be registered with the pipeline."""
    logger.info("Testing KnowledgeGraphAgent pipeline registration...")
    try:
        from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        
        # Create a pipeline instance
        pipeline = MaterialIngestionPipeline(config={
            "input_dir": "input",
            "output_dir": "output"
        })
        
        # Create and register the agent
        knowledge_graph_agent = KnowledgeGraphAgent()
        pipeline.register_agent("knowledge_graph", knowledge_graph_agent)
        
        # Verify the agent was registered
        assert "knowledge_graph" in pipeline.agents, "knowledge_graph stage should be in pipeline agents"
        assert pipeline.agents["knowledge_graph"] is knowledge_graph_agent, "Registered agent should be the same instance"
        
        logger.info(f"✓ KnowledgeGraphAgent successfully registered with pipeline")
        
        return True
    except Exception as e:
        logger.error(f"✗ KnowledgeGraphAgent registration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_graph_agent_input_validation():
    """Test that KnowledgeGraphAgent properly validates input."""
    logger.info("Testing KnowledgeGraphAgent input validation...")
    try:
        from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
        
        agent = KnowledgeGraphAgent()
        
        # Test with invalid input (missing result_from_supervision)
        invalid_input = {}
        assert not agent.validate_input(invalid_input), "Should reject input without result_from_supervision"
        
        # Test with valid input structure
        valid_input = {
            "result_from_supervision": {
                "result": {
                    "context_fusion": {
                        "concepts": [],
                        "relationships": []
                    }
                }
            }
        }
        assert agent.validate_input(valid_input), "Should accept input with proper structure"
        
        logger.info(f"✓ KnowledgeGraphAgent input validation works correctly")
        
        return True
    except Exception as e:
        logger.error(f"✗ KnowledgeGraphAgent input validation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_main_py_updated():
    """Test that main.py has been updated to include KnowledgeGraphAgent."""
    logger.info("Testing main.py updates...")
    try:
        # Read main.py and check for required imports and registrations
        main_file = project_root / "main.py"
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Check for import
        assert "from core.agents.knowledge_graph_agent import KnowledgeGraphAgent" in content, \
            "main.py should import KnowledgeGraphAgent"
        
        # Check for instantiation
        assert "knowledge_graph_agent = KnowledgeGraphAgent()" in content, \
            "main.py should instantiate KnowledgeGraphAgent"
        
        # Check for registration
        assert 'pipeline.register_agent("knowledge_graph", knowledge_graph_agent)' in content, \
            "main.py should register KnowledgeGraphAgent with pipeline"
        
        # Check execution plan includes knowledge_graph
        assert '"knowledge_graph"' in content or "'knowledge_graph'" in content, \
            "main.py execution plan should include knowledge_graph stage"
        
        logger.info(f"✓ main.py has been correctly updated")
        
        return True
    except Exception as e:
        logger.error(f"✗ main.py update verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    logger.info("=" * 80)
    logger.info("Running Knowledge Graph Agent Tests")
    logger.info("=" * 80)
    
    tests = [
        ("Import Test", test_knowledge_graph_agent_import),
        ("Structure Test", test_knowledge_graph_agent_structure),
        ("Inheritance Test", test_knowledge_graph_agent_inheritance),
        ("Registration Test", test_knowledge_graph_agent_registration),
        ("Input Validation Test", test_knowledge_graph_agent_input_validation),
        ("Main.py Update Test", test_main_py_updated),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info("")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' encountered an unexpected error: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info("")
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
