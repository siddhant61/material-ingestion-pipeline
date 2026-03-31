#!/usr/bin/env python3
"""
Integration Fixture Tests

Validates that the committed fixture artifacts under
integration_fixtures/jwst/upstream/ remain contract-valid and
structurally consistent.  These tests run without API keys or heavy
dependencies (only jsonschema + python-dotenv).

Usage:
    python -m unittest test_integration_fixtures -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.contract_validator import load_contract, validate_artifact
from generate_fixtures import generate_fixtures, FIXTURE_DIR, ARTIFACT_IDS, FIXED_RUN_ID

FIXTURE_FILES = {
    "RawSourceBundle": FIXTURE_DIR / "RawSourceBundle.json",
    "NormalizedDocumentSet": FIXTURE_DIR / "NormalizedDocumentSet.json",
    "ChunkSet": FIXTURE_DIR / "ChunkSet.json",
    "KnowledgeGraphPackage": FIXTURE_DIR / "KnowledgeGraphPackage.json",
    "RunManifest": FIXTURE_DIR / "RunManifest.json",
}


class TestFixturesExist(unittest.TestCase):
    """Verify that all fixture files are present on disk."""

    def test_fixture_directory_exists(self):
        self.assertTrue(FIXTURE_DIR.is_dir(), f"Fixture dir missing: {FIXTURE_DIR}")

    def test_all_fixture_files_present(self):
        for name, path in FIXTURE_FILES.items():
            with self.subTest(artifact=name):
                self.assertTrue(path.exists(), f"Missing fixture: {path}")

    def test_fixture_files_are_valid_json(self):
        for name, path in FIXTURE_FILES.items():
            with self.subTest(artifact=name):
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                self.assertIsInstance(data, dict)


class TestFixtureContractValidity(unittest.TestCase):
    """Every committed fixture must pass contract validation."""

    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract()
        cls.fixtures = {}
        for name, path in FIXTURE_FILES.items():
            with open(path, "r", encoding="utf-8") as fh:
                cls.fixtures[name] = json.load(fh)

    def test_raw_source_bundle_valid(self):
        ok, errors = validate_artifact(self.fixtures["RawSourceBundle"], self.contract)
        self.assertTrue(ok, f"RawSourceBundle errors: {errors}")

    def test_normalized_document_set_valid(self):
        ok, errors = validate_artifact(self.fixtures["NormalizedDocumentSet"], self.contract)
        self.assertTrue(ok, f"NormalizedDocumentSet errors: {errors}")

    def test_chunk_set_valid(self):
        ok, errors = validate_artifact(self.fixtures["ChunkSet"], self.contract)
        self.assertTrue(ok, f"ChunkSet errors: {errors}")

    def test_knowledge_graph_package_valid(self):
        ok, errors = validate_artifact(self.fixtures["KnowledgeGraphPackage"], self.contract)
        self.assertTrue(ok, f"KnowledgeGraphPackage errors: {errors}")

    def test_run_manifest_valid(self):
        ok, errors = validate_artifact(self.fixtures["RunManifest"], self.contract)
        self.assertTrue(ok, f"RunManifest errors: {errors}")


class TestFixtureStructuralInvariants(unittest.TestCase):
    """Verify structural properties that downstream repos can rely on."""

    @classmethod
    def setUpClass(cls):
        cls.fixtures = {}
        for name, path in FIXTURE_FILES.items():
            with open(path, "r", encoding="utf-8") as fh:
                cls.fixtures[name] = json.load(fh)

    def test_artifact_ids_are_stable(self):
        for name, expected_id in ARTIFACT_IDS.items():
            with self.subTest(artifact=name):
                self.assertEqual(self.fixtures[name]["artifact_id"], expected_id)

    def test_run_id_consistent_across_artifacts(self):
        for name, fixture in self.fixtures.items():
            with self.subTest(artifact=name):
                self.assertEqual(fixture["source_run_id"], FIXED_RUN_ID)

    def test_raw_source_bundle_has_six_sources(self):
        sources = self.fixtures["RawSourceBundle"]["sources"]
        self.assertEqual(len(sources), 6)

    def test_normalized_document_set_has_six_documents(self):
        docs = self.fixtures["NormalizedDocumentSet"]["documents"]
        self.assertEqual(len(docs), 6)

    def test_chunk_set_has_chunks(self):
        chunks = self.fixtures["ChunkSet"]["chunks"]
        self.assertGreater(len(chunks), 0)

    def test_knowledge_graph_has_ten_nodes(self):
        nodes = self.fixtures["KnowledgeGraphPackage"]["nodes"]
        self.assertEqual(len(nodes), 10)

    def test_knowledge_graph_has_nine_edges(self):
        edges = self.fixtures["KnowledgeGraphPackage"]["edges"]
        self.assertEqual(len(edges), 9)

    def test_knowledge_graph_embeddings_null(self):
        """Fixtures document that embeddings are not yet populated."""
        self.assertIsNone(self.fixtures["KnowledgeGraphPackage"]["embeddings_index"])

    def test_chunk_set_embeddings_null(self):
        """All chunks should have null embedding fields (Phase 1 placeholder)."""
        for chunk in self.fixtures["ChunkSet"]["chunks"]:
            self.assertIsNone(chunk["embedding_model"])
            self.assertIsNone(chunk["embedding_vector_ref"])

    def test_all_documents_are_placeholders(self):
        """In the scaffold demo, all documents have placeholder=true."""
        for doc in self.fixtures["NormalizedDocumentSet"]["documents"]:
            self.assertTrue(doc["metadata"]["placeholder"])

    def test_run_manifest_status_completed(self):
        self.assertEqual(self.fixtures["RunManifest"]["status"], "completed")


class TestFixtureRegeneration(unittest.TestCase):
    """Verify fixtures can be regenerated deterministically."""

    def test_regenerated_fixtures_match_committed(self):
        """Re-run generate_fixtures into a temp dir and compare to committed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            generate_fixtures(output_dir=tmppath)

            for name, committed_path in FIXTURE_FILES.items():
                regen_path = tmppath / committed_path.name
                with self.subTest(artifact=name):
                    with open(committed_path, "r") as f1, open(regen_path, "r") as f2:
                        committed = json.load(f1)
                        regenerated = json.load(f2)
                    self.assertEqual(committed, regenerated,
                                     f"{name} fixture is stale — run: python generate_fixtures.py")


class TestHandoffManifest(unittest.TestCase):
    """Verify the Phase 2B handoff_manifest.json is present and consistent."""

    HANDOFF_FILE = FIXTURE_DIR / "handoff_manifest.json"
    EXPECTED_ARTIFACT_TYPES = {
        "RawSourceBundle",
        "NormalizedDocumentSet",
        "ChunkSet",
        "KnowledgeGraphPackage",
        "RunManifest",
    }

    @classmethod
    def setUpClass(cls):
        with open(cls.HANDOFF_FILE, "r", encoding="utf-8") as fh:
            cls.handoff = json.load(fh)

    def test_handoff_manifest_exists(self):
        self.assertTrue(self.HANDOFF_FILE.is_file(), f"Missing: {self.HANDOFF_FILE}")

    def test_handoff_manifest_is_valid_json(self):
        self.assertIsInstance(self.handoff, dict)

    def test_handoff_manifest_has_required_fields(self):
        required = {"handoff_format_version", "package_id", "produced_by",
                    "source_run_id", "artifacts", "contract_ref",
                    "regenerate_command", "validate_command"}
        for field in required:
            with self.subTest(field=field):
                self.assertIn(field, self.handoff)

    def test_handoff_manifest_declares_all_five_artifacts(self):
        declared = {a["artifact_type"] for a in self.handoff["artifacts"]}
        self.assertEqual(declared, self.EXPECTED_ARTIFACT_TYPES)

    def test_handoff_manifest_artifact_ids_match_fixtures(self):
        for entry in self.handoff["artifacts"]:
            name = entry["artifact_type"]
            expected_id = entry["artifact_id"]
            committed_path = FIXTURE_DIR / f"{name}.json"
            with self.subTest(artifact=name):
                with open(committed_path, "r", encoding="utf-8") as fh:
                    actual_id = json.load(fh)["artifact_id"]
                self.assertEqual(actual_id, expected_id)

    def test_handoff_manifest_source_run_id_matches_fixtures(self):
        self.assertEqual(self.handoff["source_run_id"], FIXED_RUN_ID)


if __name__ == "__main__":
    unittest.main()
