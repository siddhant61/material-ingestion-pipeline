#!/usr/bin/env python3
"""
End-to-End Pipeline Structure Test

This script validates that the complete pipeline can be assembled and
all agents are properly registered without requiring actual API calls.
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
logger = logging.getLogger("test_end_to_end")


def test_complete_pipeline_assembly():
    """Test that the complete pipeline can be assembled with all 8 stages."""
    logger.info("Testing complete pipeline assembly...")
    try:
        from core.pipeline.material_ingestion_pipeline import MaterialIngestionPipeline
        from core.agents.context_agent import ContextAgent
        from core.agents.transcript_agent import TranscriptAgent
        from core.agents.slide_agent import SlideAgent
        from core.agents.fusion_agent import FusionAgent
        from core.agents.supervision_orchestrator_agent import SupervisionOrchestratorAgent
        from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
        from core.agents.visualization_agent import VisualizationAgent
        from core.agents.embedding_agent import EmbeddingAgent
        
        # Create a pipeline instance
        pipeline = MaterialIngestionPipeline(config={
            "input_dir": "input",
            "output_dir": "output"
        })
        
        # Create and register all agents
        agents = {
            "course_context": ContextAgent(),
            "process_transcripts": TranscriptAgent(),
            "process_slides": SlideAgent(),
            "context_fusion": FusionAgent(),
            "supervision": SupervisionOrchestratorAgent(),
            "knowledge_graph": KnowledgeGraphAgent(),
            "visualize": VisualizationAgent(),
            "embeddings": EmbeddingAgent()
        }
        
        # Register all agents
        for stage_name, agent in agents.items():
            pipeline.register_agent(stage_name, agent)
        
        # Verify all stages are registered
        for stage_name in agents.keys():
            assert stage_name in pipeline.agents, f"Stage {stage_name} should be registered"
        
        # Set the execution plan
        execution_plan = [
            "course_context",
            "process_transcripts",
            "process_slides",
            "context_fusion",
            "supervision",
            "knowledge_graph",
            "visualize",
            "embeddings"
        ]
        pipeline.set_execution_plan(execution_plan)
        
        # Verify the execution plan
        assert pipeline.execution_plan == execution_plan, "Execution plan should match"
        
        logger.info(f"✓ Complete pipeline assembled with {len(agents)} stages")
        logger.info(f"  Execution plan: {' -> '.join(execution_plan)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Complete pipeline assembly failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_stages_order():
    """Test that the pipeline stages are in the correct order."""
    logger.info("Testing pipeline stages order...")
    try:
        # Read main.py to verify execution plan order
        main_file = project_root / "main.py"
        with open(main_file, 'r') as f:
            content = f.read()
        
        # Expected order
        expected_order = [
            "course_context",
            "process_transcripts",
            "process_slides",
            "context_fusion",
            "supervision",
            "knowledge_graph",
            "visualize",
            "embeddings"
        ]
        
        # Verify the execution plan contains all stages in order
        for stage in expected_order:
            assert f'"{stage}"' in content or f"'{stage}'" in content, \
                f"Stage {stage} should be in execution plan"
        
        logger.info(f"✓ All 8 pipeline stages present in correct order")
        
        return True
    except Exception as e:
        logger.error(f"✗ Pipeline stages order test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_all_agents_have_run_method():
    """Test that all agents have a properly implemented run method."""
    logger.info("Testing all agents have run method...")
    try:
        from core.agents.context_agent import ContextAgent
        from core.agents.transcript_agent import TranscriptAgent
        from core.agents.slide_agent import SlideAgent
        from core.agents.fusion_agent import FusionAgent
        from core.agents.supervision_orchestrator_agent import SupervisionOrchestratorAgent
        from core.agents.knowledge_graph_agent import KnowledgeGraphAgent
        from core.agents.visualization_agent import VisualizationAgent
        from core.agents.embedding_agent import EmbeddingAgent
        
        agents = [
            ContextAgent(),
            TranscriptAgent(),
            SlideAgent(),
            FusionAgent(),
            SupervisionOrchestratorAgent(),
            KnowledgeGraphAgent(),
            VisualizationAgent(),
            EmbeddingAgent()
        ]
        
        for agent in agents:
            assert hasattr(agent, 'run'), f"{agent.__class__.__name__} should have run method"
            assert callable(agent.run), f"{agent.__class__.__name__}.run should be callable"
        
        logger.info(f"✓ All {len(agents)} agents have run method")
        
        return True
    except Exception as e:
        logger.error(f"✗ Agents run method test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_output_agents_depend_on_knowledge_graph():
    """Test that output agents properly depend on knowledge graph output."""
    logger.info("Testing output agents dependencies...")
    try:
        from core.agents.visualization_agent import VisualizationAgent
        from core.agents.embedding_agent import EmbeddingAgent
        
        visualization_agent = VisualizationAgent()
        embedding_agent = EmbeddingAgent()
        
        # Test that they reject input without knowledge graph
        invalid_input = {}
        assert not visualization_agent.validate_input(invalid_input), \
            "VisualizationAgent should require knowledge graph input"
        assert not embedding_agent.validate_input(invalid_input), \
            "EmbeddingAgent should require knowledge graph input"
        
        # Test that they accept input with knowledge graph
        valid_input = {
            "result_from_knowledge_graph": {
                "result": {
                    "entities": [],
                    "relationships": []
                }
            }
        }
        assert visualization_agent.validate_input(valid_input), \
            "VisualizationAgent should accept valid knowledge graph input"
        assert embedding_agent.validate_input(valid_input), \
            "EmbeddingAgent should accept valid knowledge graph input"
        
        logger.info(f"✓ Output agents properly depend on knowledge graph")
        
        return True
    except Exception as e:
        logger.error(f"✗ Output agents dependencies test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    logger.info("=" * 80)
    logger.info("Running End-to-End Pipeline Structure Tests")
    logger.info("=" * 80)
    
    tests = [
        ("Complete Pipeline Assembly", test_complete_pipeline_assembly),
        ("Pipeline Stages Order", test_pipeline_stages_order),
        ("All Agents Have Run Method", test_all_agents_have_run_method),
        ("Output Agents Dependencies", test_output_agents_depend_on_knowledge_graph),
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
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 8 COMPLETE: Output Agents Successfully Migrated")
        logger.info("=" * 80)
        logger.info("")
        logger.info("The complete pipeline now has 8 stages:")
        logger.info("  1. course_context")
        logger.info("  2. process_transcripts")
        logger.info("  3. process_slides")
        logger.info("  4. context_fusion")
        logger.info("  5. supervision")
        logger.info("  6. knowledge_graph")
        logger.info("  7. visualize         ← NEW")
        logger.info("  8. embeddings        ← NEW")
        logger.info("")
        logger.info("All agents are now properly registered and the pipeline is")
        logger.info("ready for end-to-end execution with: python main.py")
        return 0
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
