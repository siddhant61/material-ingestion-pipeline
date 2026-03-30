#!/usr/bin/env python3
"""
Phase 1 Happy-Path Tests

Validates the contract validator, artifact builders, and end-to-end
demo ingestion without requiring any external dependencies or API keys.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.contract_validator import load_contract, validate_artifact
from ingest_demo import (
    build_raw_source_bundle,
    build_normalized_document_set,
    build_chunk_set,
    build_knowledge_graph_package,
    build_run_manifest,
    run_ingest,
    DEFAULT_MANIFEST,
)


class TestContractValidator(unittest.TestCase):
    """Tests for core/contract_validator.py."""

    def test_load_contract(self):
        contract = load_contract()
        self.assertIn("artifacts", contract)
        self.assertIn("RawSourceBundle", contract["artifacts"])
        self.assertIn("RunManifest", contract["artifacts"])

    def test_valid_run_manifest(self):
        rm = {
            "artifact_type": "RunManifest",
            "schema_version": "1.0.0",
            "artifact_id": "test",
            "created_at": "2026-01-01T00:00:00Z",
            "producer": "test",
            "source_run_id": "test",
            "pipeline_name": "test",
            "pipeline_stage": "test",
            "status": "completed",
            "inputs": {},
            "outputs": [],
            "metrics": {},
            "errors": [],
        }
        ok, errors = validate_artifact(rm)
        self.assertTrue(ok, f"Should be valid but got errors: {errors}")

    def test_missing_required_field(self):
        rm = {
            "artifact_type": "RunManifest",
            "schema_version": "1.0.0",
            # Missing artifact_id and others
        }
        ok, errors = validate_artifact(rm)
        self.assertFalse(ok)
        self.assertTrue(any("artifact_id" in e for e in errors))

    def test_unknown_artifact_type(self):
        art = {"artifact_type": "BogusType"}
        ok, errors = validate_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("Unknown" in e for e in errors))

    def test_missing_artifact_type(self):
        ok, errors = validate_artifact({})
        self.assertFalse(ok)
        self.assertTrue(any("artifact_type" in e for e in errors))

    def test_nested_source_item_validation(self):
        bundle = {
            "artifact_type": "RawSourceBundle",
            "schema_version": "1.0.0",
            "artifact_id": "test",
            "created_at": "2026-01-01T00:00:00Z",
            "producer": "test",
            "source_run_id": "test",
            "topic": "test",
            "source_bundle_name": "test",
            "sources": [{"source_id": "s1"}],  # missing many fields
        }
        ok, errors = validate_artifact(bundle)
        self.assertFalse(ok)
        self.assertTrue(any("title" in e for e in errors))


class TestDemoManifestExists(unittest.TestCase):
    """Verify the canonical demo scaffold is present."""

    def test_manifest_exists(self):
        self.assertTrue(DEFAULT_MANIFEST.exists(), f"Manifest not found at {DEFAULT_MANIFEST}")

    def test_manifest_is_valid_json(self):
        with open(DEFAULT_MANIFEST) as fh:
            data = json.load(fh)
        self.assertEqual(data["artifact_type"], "RawSourceBundle")
        self.assertIn("sources", data)
        self.assertGreater(len(data["sources"]), 0)


class TestArtifactBuilders(unittest.TestCase):
    """Tests for individual artifact builder functions."""

    @classmethod
    def setUpClass(cls):
        with open(DEFAULT_MANIFEST) as fh:
            cls.manifest = json.load(fh)
        cls.manifest_dir = DEFAULT_MANIFEST.parent
        cls.run_id = "test-run-001"
        cls.contract = load_contract()

    def test_build_raw_source_bundle(self):
        bundle = build_raw_source_bundle(self.manifest, self.manifest_dir, self.run_id)
        ok, errors = validate_artifact(bundle, self.contract)
        self.assertTrue(ok, f"RawSourceBundle validation errors: {errors}")
        self.assertEqual(bundle["artifact_type"], "RawSourceBundle")
        self.assertEqual(len(bundle["sources"]), len(self.manifest["sources"]))

    def test_build_normalized_document_set(self):
        bundle = build_raw_source_bundle(self.manifest, self.manifest_dir, self.run_id)
        doc_set = build_normalized_document_set(bundle, self.manifest_dir, self.run_id)
        ok, errors = validate_artifact(doc_set, self.contract)
        self.assertTrue(ok, f"NormalizedDocumentSet validation errors: {errors}")
        # One document per source
        self.assertEqual(len(doc_set["documents"]), len(bundle["sources"]))
        # All docs should be placeholders in the scaffold
        for doc in doc_set["documents"]:
            self.assertIn("placeholder", doc["metadata"])

    def test_build_chunk_set(self):
        bundle = build_raw_source_bundle(self.manifest, self.manifest_dir, self.run_id)
        doc_set = build_normalized_document_set(bundle, self.manifest_dir, self.run_id)
        chunk_set = build_chunk_set(doc_set, self.run_id)
        ok, errors = validate_artifact(chunk_set, self.contract)
        self.assertTrue(ok, f"ChunkSet validation errors: {errors}")
        self.assertGreater(len(chunk_set["chunks"]), 0)

    def test_build_knowledge_graph_package(self):
        bundle = build_raw_source_bundle(self.manifest, self.manifest_dir, self.run_id)
        bundle["_seed_entities"] = self.manifest.get("seed_entities", [])
        doc_set = build_normalized_document_set(bundle, self.manifest_dir, self.run_id)
        kg = build_knowledge_graph_package(bundle, doc_set, self.run_id)
        ok, errors = validate_artifact(kg, self.contract)
        self.assertTrue(ok, f"KnowledgeGraphPackage validation errors: {errors}")
        # Should have nodes for each seed entity
        seed_count = len(self.manifest.get("seed_entities", []))
        self.assertEqual(len(kg["nodes"]), seed_count)
        # Edges = seed_count - 1 (consecutive pairs)
        self.assertEqual(len(kg["edges"]), max(0, seed_count - 1))

    def test_build_run_manifest(self):
        rm = build_run_manifest("test-run", "test-topic", ["file1.json"], [])
        ok, errors = validate_artifact(rm, self.contract)
        self.assertTrue(ok, f"RunManifest validation errors: {errors}")


class TestEndToEndIngest(unittest.TestCase):
    """End-to-end test of the demo ingestion happy path."""

    def test_run_ingest_produces_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            summary = run_ingest(DEFAULT_MANIFEST, output_dir)

            self.assertIn("run_id", summary)
            self.assertIn(summary["status"], ("success", "completed_with_warnings"))
            self.assertEqual(len(summary["artifacts_written"]), 5)

            # Every written file should exist and be valid JSON
            for fpath in summary["artifacts_written"]:
                p = Path(fpath)
                self.assertTrue(p.exists(), f"Artifact file missing: {fpath}")
                with open(p) as fh:
                    data = json.load(fh)
                self.assertIn("artifact_type", data)

    def test_artifact_naming_convention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            summary = run_ingest(DEFAULT_MANIFEST, output_dir)

            for fpath in summary["artifacts_written"]:
                fname = Path(fpath).name
                # Convention: <topic_slug>__<ArtifactType>__<timestamp>.json
                parts = fname.split("__")
                self.assertEqual(len(parts), 3, f"Filename doesn't follow convention: {fname}")
                self.assertEqual(parts[0], "jwst_star_formation_early_universe_demo")
                self.assertTrue(parts[2].endswith(".json"))

    def test_graceful_with_missing_sources(self):
        """Even though raw files are missing, the pipeline should complete without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            summary = run_ingest(DEFAULT_MANIFEST, output_dir)
            # Should complete successfully even with scaffold-only sources
            self.assertIn(summary["status"], ("success", "completed_with_warnings"))


if __name__ == "__main__":
    unittest.main()
