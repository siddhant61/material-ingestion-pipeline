#!/usr/bin/env python3
"""
Test Visualization and Embedding Agents

This script validates that the VisualizationAgent and EmbeddingAgent are correctly
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
logger = logging.getLogger("test_output_agents")


def test_visualization_agent_import():
    """Test that VisualizationAgent can be imported."""
    logger.info("Testing VisualizationAgent import...")
    try:
        from core.agents.visualization_agent import VisualizationAgent
        
        # Verify it's a class
        assert callable(VisualizationAgent), "VisualizationAgent should be a callable class"
        
        logger.info(f"✓ VisualizationAgent imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ VisualizationAgent import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_agent_import():
    """Test that EmbeddingAgent can be imported."""
    logger.info("Testing EmbeddingAgent import...")
    try:
        from core.agents.embedding_agent import EmbeddingAgent
        
        # Verify it's a class
        assert callable(EmbeddingAgent), "EmbeddingAgent should be a callable class"
        
        logger.info(f"✓ EmbeddingAgent imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ EmbeddingAgent import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agents_structure():
    """Test that both agents have the correct structure."""
    logger.info("Testing agents structure...")
    try:
        from core.agents.visualization_agent import VisualizationAgent
        from core.agents.embedding_agent import EmbeddingAgent
        
        # Check that they have the expected methods
        expected_methods = ['run', 'validate_input', 'validate_output', '_init_models', 
                          '_init_memory', '_init_orchestration', '_init_reasoning', '_init_tools']
        
        for agent_class in [VisualizationAgent, EmbeddingAgent]:
            for method_name in expected_methods:
                assert hasattr(agent_class, method_name), f"{agent_class.__name__} should have method: {method_name}"
        
        logger.info(f"✓ Both agents have all expected methods")
        
        return True
    except Exception as e:
        logger.error(f"✗ Agents structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agents_inheritance():
    """Test that both agents inherit from BaseAgent."""
    logger.info("Testing agents inheritance...")
    try:
        from core.agents.visualization_agent import VisualizationAgent
        from core.agents.embedding_agent import EmbeddingAgent
        from core.agents.base_agent import BaseAgent
        
        # Verify they inherit from BaseAgent
        assert issubclass(VisualizationAgent, BaseAgent), "VisualizationAgent should inherit from BaseAgent"
        assert issubclass(EmbeddingAgent, BaseAgent), "EmbeddingAgent should inherit from BaseAgent"
        
        logger.info(f"✓ Both agents correctly inherit from BaseAgent")
        
        return True
    except Exception as e:
        logger.error(f"✗ Agents inheritance test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agents_registration():
    """Test that both agents can be registered with the pipeline."""
    logger.info("Testing agents pipeline registration...")
    try:
        from core.agents.visualization_agent import VisualizationAgent
        from core.agents.embedding_agent import EmbeddingAgent
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        
        # Create a pipeline instance
        pipeline = MaterialIngestionPipeline(config={
            "input_dir": "input",
            "output_dir": "output"
        })
        
        # Create and register the agents
        visualization_agent = VisualizationAgent()
        embedding_agent = EmbeddingAgent()
        
        pipeline.register_agent("visualize", visualization_agent)
        pipeline.register_agent("embeddings", embedding_agent)
        
        # Verify the agents were registered
        assert "visualize" in pipeline.agents, "visualize stage should be in pipeline agents"
        assert "embeddings" in pipeline.agents, "embeddings stage should be in pipeline agents"
        assert pipeline.agents["visualize"] is visualization_agent, "Registered visualization agent should be the same instance"
        assert pipeline.agents["embeddings"] is embedding_agent, "Registered embedding agent should be the same instance"
        
        logger.info(f"✓ Both agents successfully registered with pipeline")
        
        return True
    except Exception as e:
        logger.error(f"✗ Agents registration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agents_input_validation():
    """Test that both agents properly validate input."""
    logger.info("Testing agents input validation...")
    try:
        from core.agents.visualization_agent import VisualizationAgent
        from core.agents.embedding_agent import EmbeddingAgent
        
        visualization_agent = VisualizationAgent()
        embedding_agent = EmbeddingAgent()
        
        # Test with invalid input (missing result_from_knowledge_graph)
        invalid_input = {}
        assert not visualization_agent.validate_input(invalid_input), "VisualizationAgent should reject input without result_from_knowledge_graph"
        assert not embedding_agent.validate_input(invalid_input), "EmbeddingAgent should reject input without result_from_knowledge_graph"
        
        # Test with valid input structure
        valid_input = {
            "result_from_knowledge_graph": {
                "result": {
                    "entities": [],
                    "relationships": []
                }
            }
        }
        assert visualization_agent.validate_input(valid_input), "VisualizationAgent should accept input with proper structure"
        assert embedding_agent.validate_input(valid_input), "EmbeddingAgent should accept input with proper structure"
        
        logger.info(f"✓ Both agents input validation works correctly")
        
        return True
    except Exception as e:
        logger.error(f"✗ Agents input validation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_main_py_updated():
    """Test that main.py has been updated to include both agents."""
    logger.info("Testing main.py updates...")
    try:
        # Read main.py and check for required imports and registrations
        main_file = project_root / "main.py"
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Check for imports
        assert "from core.agents.visualization_agent import VisualizationAgent" in content, \
            "main.py should import VisualizationAgent"
        assert "from core.agents.embedding_agent import EmbeddingAgent" in content, \
            "main.py should import EmbeddingAgent"
        
        # Check for instantiation
        assert "visualization_agent = VisualizationAgent()" in content, \
            "main.py should instantiate VisualizationAgent"
        assert "embedding_agent = EmbeddingAgent()" in content, \
            "main.py should instantiate EmbeddingAgent"
        
        # Check for registration
        assert 'pipeline.register_agent("visualize", visualization_agent)' in content, \
            "main.py should register VisualizationAgent with pipeline"
        assert 'pipeline.register_agent("embeddings", embedding_agent)' in content, \
            "main.py should register EmbeddingAgent with pipeline"
        
        # Check execution plan includes both stages
        assert '"visualize"' in content or "'visualize'" in content, \
            "main.py execution plan should include visualize stage"
        assert '"embeddings"' in content or "'embeddings'" in content, \
            "main.py execution plan should include embeddings stage"
        
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
    logger.info("Running Output Agents Tests (Visualization & Embedding)")
    logger.info("=" * 80)
    
    tests = [
        ("VisualizationAgent Import Test", test_visualization_agent_import),
        ("EmbeddingAgent Import Test", test_embedding_agent_import),
        ("Agents Structure Test", test_agents_structure),
        ("Agents Inheritance Test", test_agents_inheritance),
        ("Agents Registration Test", test_agents_registration),
        ("Agents Input Validation Test", test_agents_input_validation),
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
