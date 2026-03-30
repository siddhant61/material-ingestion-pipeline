#!/usr/bin/env python3
"""
Tests for Phase 1.5 Legacy-to-Contract Adapters

Validates:
- legacy KG → KnowledgeGraphPackage adapter
- legacy pipeline report → RunManifest adapter
- --validate-only mode
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.contract_validator import load_contract, validate_artifact
from core.adapters.legacy_kg_adapter import (
    adapt_entity_to_node,
    adapt_relationship_to_edge,
    adapt_legacy_kg,
)
from core.adapters.legacy_report_adapter import adapt_legacy_report
from ingest_demo import run_validate_only, DEFAULT_MANIFEST

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_LEGACY_ENTITY = {
    "id": "concept_42",
    "type": "concept",
    "name": "Quantum Entanglement",
    "description": "A quantum phenomenon where particles remain connected",
    "hierarchy_level": "branch",
    "properties": {
        "importance": 8,
        "keywords": ["quantum", "entanglement"],
        "category": "concept",
        "sources": ["transcript", "slide"],
        "source_type": "content",
        "enrichment_status": "enriched",
        "resources": {"visualizations": [], "references": [], "examples": []},
    },
}

SAMPLE_LEGACY_RELATIONSHIP = {
    "source": "domain_0",
    "target": "concept_42",
    "type": "contains",
    "properties": {
        "description": "Domain contains concept: Quantum Entanglement",
        "strength": 0.9,
        "hierarchical": True,
        "sources": ["module_structure"],
        "source_type": "course",
        "bidirectional": False,
    },
}

SAMPLE_LEGACY_KG = {
    "entities": [
        {
            "id": "domain_0",
            "type": "domain",
            "name": "Course Domain",
            "description": "Root domain",
            "hierarchy_level": "root",
            "properties": {
                "importance": 10,
                "keywords": [],
                "category": "domain",
                "sources": ["course"],
                "source_type": "course",
            },
        },
        SAMPLE_LEGACY_ENTITY,
    ],
    "relationships": [SAMPLE_LEGACY_RELATIONSHIP],
    "hierarchy": {"root": ["domain_0"], "branch": ["concept_42"]},
    "metadata": {
        "source": "fused_context",
        "entity_count": 2,
        "relationship_count": 1,
        "hierarchy_levels": {"root": 1, "branch": 3},
        "hierarchy_counts": {"root": 1, "branch": 1},
    },
}

SAMPLE_LEGACY_REPORT = {
    "run_id": "20250306_042550",
    "timestamp": "2025-03-06T04:25:50.516297",
    "status": "completed",
    "steps": {
        "course_context": {
            "status": "completed",
            "output": "/path/to/output/course_context",
        },
        "transcript_processing": {
            "status": "completed",
            "output": "/path/to/output/transcript_processing",
        },
        "knowledge_graph": {
            "status": "completed",
            "output": "/path/to/output/knowledge_graph",
        },
    },
    "completion_timestamp": "2025-03-06T04:57:41.905381",
}


# ---------------------------------------------------------------------------
# KG Adapter Tests
# ---------------------------------------------------------------------------


class TestLegacyKGAdapter(unittest.TestCase):
    """Tests for core/adapters/legacy_kg_adapter.py."""

    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract()

    def test_adapt_entity_to_node_fields(self):
        node = adapt_entity_to_node(SAMPLE_LEGACY_ENTITY)
        self.assertEqual(node["node_id"], "concept_42")
        self.assertEqual(node["label"], "Quantum Entanglement")
        self.assertEqual(node["node_type"], "concept")
        self.assertEqual(node["description"], "A quantum phenomenon where particles remain connected")
        self.assertIsInstance(node["aliases"], list)
        self.assertIsInstance(node["attributes"], dict)
        self.assertIn("transcript", node["source_refs"])
        self.assertIn("slide", node["source_refs"])

    def test_adapt_entity_preserves_properties_in_attributes(self):
        node = adapt_entity_to_node(SAMPLE_LEGACY_ENTITY)
        self.assertEqual(node["attributes"]["importance"], 8)
        self.assertIn("quantum", node["attributes"]["keywords"])

    def test_adapt_relationship_to_edge_fields(self):
        edge = adapt_relationship_to_edge(SAMPLE_LEGACY_RELATIONSHIP, 0)
        self.assertEqual(edge["edge_id"], "edge-0")
        self.assertEqual(edge["source_node_id"], "domain_0")
        self.assertEqual(edge["target_node_id"], "concept_42")
        self.assertEqual(edge["relation_type"], "contains")
        self.assertAlmostEqual(edge["weight"], 0.9)
        self.assertIn("module_structure", edge["source_refs"])
        self.assertIn("Domain contains concept", edge["evidence"])

    def test_adapt_legacy_kg_contract_valid(self):
        """Adapted KG must pass contract validation."""
        kg = adapt_legacy_kg(SAMPLE_LEGACY_KG, topic="test_topic")
        ok, errors = validate_artifact(kg, self.contract)
        self.assertTrue(ok, f"KG adapter output failed validation: {errors}")

    def test_adapt_legacy_kg_node_count(self):
        kg = adapt_legacy_kg(SAMPLE_LEGACY_KG)
        self.assertEqual(len(kg["nodes"]), 2)
        self.assertEqual(len(kg["edges"]), 1)

    def test_adapt_legacy_kg_provenance(self):
        kg = adapt_legacy_kg(SAMPLE_LEGACY_KG)
        prov = kg["provenance"]
        self.assertEqual(prov["method"], "legacy_kg_adapter")
        self.assertEqual(prov["legacy_entity_count"], 2)
        self.assertEqual(prov["legacy_relationship_count"], 1)

    def test_adapt_legacy_kg_with_empty_input(self):
        """Adapter handles empty legacy KG gracefully."""
        kg = adapt_legacy_kg({"entities": [], "relationships": [], "metadata": {}})
        ok, errors = validate_artifact(kg, self.contract)
        self.assertTrue(ok, f"Empty KG failed validation: {errors}")
        self.assertEqual(len(kg["nodes"]), 0)
        self.assertEqual(len(kg["edges"]), 0)

    def test_adapt_entity_missing_fields_graceful(self):
        """Adapter should not crash on entities missing optional legacy fields."""
        minimal = {"id": "x", "name": "X"}
        node = adapt_entity_to_node(minimal)
        self.assertEqual(node["node_id"], "x")
        self.assertEqual(node["label"], "X")
        self.assertEqual(node["node_type"], "unknown")

    def test_adapt_real_legacy_kg_if_available(self):
        """If the actual legacy KG file exists, verify it adapts and validates."""
        legacy_path = PROJECT_ROOT / "output" / "knowledge_graph" / "knowledge_graph.json"
        if not legacy_path.exists():
            self.skipTest("Legacy KG file not present")
        with open(legacy_path) as fh:
            legacy_kg = json.load(fh)
        kg = adapt_legacy_kg(legacy_kg, topic="legacy_course_kg")
        ok, errors = validate_artifact(kg, self.contract)
        self.assertTrue(ok, f"Real legacy KG adapter output failed validation: {errors}")
        self.assertGreater(len(kg["nodes"]), 0)


# ---------------------------------------------------------------------------
# Report Adapter Tests
# ---------------------------------------------------------------------------


class TestLegacyReportAdapter(unittest.TestCase):
    """Tests for core/adapters/legacy_report_adapter.py."""

    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract()

    def test_adapt_legacy_report_contract_valid(self):
        """Adapted report must pass contract validation."""
        rm = adapt_legacy_report(SAMPLE_LEGACY_REPORT)
        ok, errors = validate_artifact(rm, self.contract)
        self.assertTrue(ok, f"Report adapter output failed validation: {errors}")

    def test_adapt_legacy_report_fields(self):
        rm = adapt_legacy_report(SAMPLE_LEGACY_REPORT)
        self.assertEqual(rm["artifact_type"], "RunManifest")
        self.assertEqual(rm["source_run_id"], "20250306_042550")
        self.assertEqual(rm["status"], "completed")
        self.assertEqual(rm["pipeline_stage"], "legacy_full_pipeline")

    def test_adapt_legacy_report_outputs(self):
        rm = adapt_legacy_report(SAMPLE_LEGACY_REPORT)
        self.assertEqual(len(rm["outputs"]), 3)
        self.assertIn("/path/to/output/course_context", rm["outputs"])

    def test_adapt_legacy_report_metrics(self):
        rm = adapt_legacy_report(SAMPLE_LEGACY_REPORT)
        metrics = rm["metrics"]
        self.assertEqual(metrics["total_steps"], 3)
        self.assertEqual(metrics["completed_steps"], 3)
        self.assertIn("duration_seconds", metrics)
        self.assertGreater(metrics["duration_seconds"], 0)

    def test_adapt_legacy_report_with_failed_step(self):
        """Steps with non-completed status should be captured as errors."""
        report = {
            "run_id": "test_fail",
            "timestamp": "2025-01-01T00:00:00",
            "status": "partial",
            "steps": {
                "step_a": {"status": "completed", "output": "/out/a"},
                "step_b": {"status": "failed", "output": "/out/b"},
            },
        }
        rm = adapt_legacy_report(report)
        ok, errors = validate_artifact(rm, self.contract)
        self.assertTrue(ok, f"Failed-step report failed validation: {errors}")
        self.assertEqual(len(rm["errors"]), 1)
        self.assertIn("step_b", rm["errors"][0])
        self.assertEqual(rm["status"], "completed_with_errors")

    def test_adapt_legacy_report_empty_steps(self):
        """Adapter handles report with no steps."""
        report = {
            "run_id": "empty",
            "timestamp": "2025-01-01T00:00:00",
            "status": "completed",
            "steps": {},
        }
        rm = adapt_legacy_report(report)
        ok, errors = validate_artifact(rm, self.contract)
        self.assertTrue(ok, f"Empty report failed validation: {errors}")
        self.assertEqual(len(rm["outputs"]), 0)

    def test_adapt_real_legacy_report_if_available(self):
        """If the actual legacy report exists, verify it adapts and validates."""
        report_path = PROJECT_ROOT / "output" / "pipeline_report.json"
        if not report_path.exists():
            self.skipTest("Legacy pipeline_report.json not present")
        with open(report_path) as fh:
            legacy = json.load(fh)
        rm = adapt_legacy_report(legacy)
        ok, errors = validate_artifact(rm, self.contract)
        self.assertTrue(ok, f"Real legacy report adapter output failed validation: {errors}")

    def test_adapt_legacy_report_dict_outputs(self):
        """Steps with dict outputs (e.g. visualizations) extract all string values."""
        report = {
            "run_id": "dict_out",
            "timestamp": "2025-01-01T00:00:00",
            "status": "completed",
            "steps": {
                "viz": {
                    "status": "completed",
                    "output": {
                        "interactive": "/out/interactive.html",
                        "static": "/out/static.png",
                    },
                }
            },
        }
        rm = adapt_legacy_report(report)
        self.assertEqual(len(rm["outputs"]), 2)
        self.assertIn("/out/interactive.html", rm["outputs"])
        self.assertIn("/out/static.png", rm["outputs"])


# ---------------------------------------------------------------------------
# Validate-Only Mode Tests
# ---------------------------------------------------------------------------


class TestValidateOnlyMode(unittest.TestCase):
    """Tests for the --validate-only mode in ingest_demo.py."""

    def test_validate_only_returns_valid(self):
        summary = run_validate_only(DEFAULT_MANIFEST)
        self.assertEqual(summary["mode"], "validate-only")
        self.assertEqual(summary["status"], "valid")
        self.assertEqual(len(summary["validation_errors"]), 0)
        self.assertIn("RawSourceBundle", summary["artifacts_checked"])
        self.assertIn("RunManifest", summary["artifacts_checked"])

    def test_validate_only_no_files_written(self):
        """validate-only must not create any output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Ensure the default output dir doesn't exist before
            output_check = Path(tmpdir) / "should_not_exist"
            summary = run_validate_only(DEFAULT_MANIFEST)
            self.assertFalse(output_check.exists())

    def test_validate_only_cli_flag(self):
        """Test --validate-only via subprocess."""
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "ingest_demo.py"), "--validate-only"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertEqual(output["mode"], "validate-only")
        self.assertEqual(output["status"], "valid")


if __name__ == "__main__":
    unittest.main()
