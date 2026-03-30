#!/usr/bin/env python3
"""
Generate deterministic integration fixture artifacts for the JWST demo.

Produces contract-valid examples of all 5 upstream artifacts under
integration_fixtures/jwst/upstream/ using fixed IDs and timestamps
so the output is fully reproducible without API keys or heavy dependencies.

Usage:
    python generate_fixtures.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.contract_validator import load_contract, validate_artifact
from ingest_demo import (
    build_raw_source_bundle,
    build_normalized_document_set,
    build_chunk_set,
    build_knowledge_graph_package,
    build_run_manifest,
    DEFAULT_MANIFEST,
    SCHEMA_VERSION,
    PRODUCER,
)

# ---------------------------------------------------------------------------
# Fixed values for deterministic output
# ---------------------------------------------------------------------------
FIXED_RUN_ID = "fixture-jwst-001"
FIXED_TIMESTAMP = "2026-03-30T00:00:00Z"
FIXTURE_DIR = PROJECT_ROOT / "integration_fixtures" / "jwst" / "upstream"

# Stable artifact IDs (never change these once published)
ARTIFACT_IDS = {
    "RawSourceBundle": "fixture-rsb-jwst-001",
    "NormalizedDocumentSet": "fixture-nds-jwst-001",
    "ChunkSet": "fixture-cs-jwst-001",
    "KnowledgeGraphPackage": "fixture-kg-jwst-001",
    "RunManifest": "fixture-rm-jwst-001",
}

# Stable document IDs keyed by source_id
DOC_IDS = {
    "jwst-nasa-mission-overview": "doc-jwst-001",
    "jwst-nasa-fact-sheet": "doc-jwst-002",
    "jwst-nasa-about-infographic": "doc-jwst-003",
    "jwst-nasa-gallery": "doc-jwst-004",
    "jwst-nasa-video-star-formation": "doc-jwst-005",
    "jwst-esa-brochure": "doc-jwst-006",
}

# Stable node IDs keyed by seed entity label
NODE_IDS = {
    "James Webb Space Telescope": "node-jwst-001",
    "infrared astronomy": "node-jwst-002",
    "L2 orbit": "node-jwst-003",
    "sunshield": "node-jwst-004",
    "primary mirror": "node-jwst-005",
    "star formation": "node-jwst-006",
    "early universe": "node-jwst-007",
    "galaxies": "node-jwst-008",
    "exoplanets": "node-jwst-009",
    "spectroscopy": "node-jwst-010",
}


def _stabilize_timestamps(artifact: dict) -> dict:
    """Replace generated timestamps with the fixed fixture timestamp."""
    artifact["created_at"] = FIXED_TIMESTAMP
    return artifact


def _build_fixture_raw_source_bundle(manifest: dict, manifest_dir: Path) -> dict:
    """Build a deterministic RawSourceBundle fixture."""
    bundle = build_raw_source_bundle(manifest, manifest_dir, FIXED_RUN_ID)
    bundle["artifact_id"] = ARTIFACT_IDS["RawSourceBundle"]
    _stabilize_timestamps(bundle)
    return bundle


def _build_fixture_normalized_document_set(bundle: dict, manifest_dir: Path) -> dict:
    """Build a deterministic NormalizedDocumentSet fixture."""
    doc_set = build_normalized_document_set(bundle, manifest_dir, FIXED_RUN_ID)
    doc_set["artifact_id"] = ARTIFACT_IDS["NormalizedDocumentSet"]
    _stabilize_timestamps(doc_set)
    # Assign stable document IDs
    for doc in doc_set["documents"]:
        source_id = doc["source_id"]
        if source_id in DOC_IDS:
            old_id = doc["document_id"]
            doc["document_id"] = DOC_IDS[source_id]
    return doc_set


def _build_fixture_chunk_set(doc_set: dict) -> dict:
    """Build a deterministic ChunkSet fixture."""
    chunk_set = build_chunk_set(doc_set, FIXED_RUN_ID)
    chunk_set["artifact_id"] = ARTIFACT_IDS["ChunkSet"]
    _stabilize_timestamps(chunk_set)
    # Chunk IDs are derived from document IDs, which are already stable
    return chunk_set


def _build_fixture_knowledge_graph(bundle: dict, doc_set: dict) -> dict:
    """Build a deterministic KnowledgeGraphPackage fixture."""
    # Temporarily inject stable node IDs via a patched builder
    seed_entities = bundle.get("seed_entities", bundle.get("_seed_entities", []))
    topic = bundle.get("topic", "")

    nodes = []
    edges = []
    entity_ids = {}

    for label in seed_entities:
        nid = NODE_IDS.get(label, f"node-{label[:8]}")
        entity_ids[label] = nid
        nodes.append({
            "node_id": nid,
            "label": label,
            "node_type": "seed_entity",
            "description": f"Seed entity from demo manifest for topic: {topic}",
            "aliases": [],
            "attributes": {},
            "source_refs": [],
        })

    entity_list = list(entity_ids.items())
    for i in range(len(entity_list) - 1):
        _, id_a = entity_list[i]
        _, id_b = entity_list[i + 1]
        edges.append({
            "edge_id": f"edge-jwst-{i:03d}",
            "source_node_id": id_a,
            "target_node_id": id_b,
            "relation_type": "related_to",
            "weight": 0.5,
            "evidence": "Co-listed as seed entities in demo manifest",
            "source_refs": [],
        })

    kg = {
        "artifact_type": "KnowledgeGraphPackage",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": ARTIFACT_IDS["KnowledgeGraphPackage"],
        "created_at": FIXED_TIMESTAMP,
        "producer": PRODUCER,
        "source_run_id": FIXED_RUN_ID,
        "topic": topic,
        "graph_name": f"{topic}_seed_graph",
        "nodes": nodes,
        "edges": edges,
        "embeddings_index": None,
        "provenance": {
            "method": "seed_entity_bootstrap",
            "source_manifest": bundle.get("artifact_id", ""),
        },
    }
    return kg


def _build_fixture_run_manifest(artifact_files: list, errors: list) -> dict:
    """Build a deterministic RunManifest fixture."""
    topic_slug = "jwst_star_formation_early_universe_demo"
    status = "completed_with_warnings" if errors else "completed"
    return {
        "artifact_type": "RunManifest",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": ARTIFACT_IDS["RunManifest"],
        "created_at": FIXED_TIMESTAMP,
        "producer": PRODUCER,
        "source_run_id": FIXED_RUN_ID,
        "pipeline_name": "material-ingestion-pipeline",
        "pipeline_stage": "phase1_demo_ingest",
        "status": status,
        "inputs": {
            "topic": topic_slug,
            "manifest": "demo_data/jwst_star_formation_early_universe_demo/manifest.json",
        },
        "outputs": artifact_files,
        "metrics": {"artifact_count": len(artifact_files)},
        "errors": errors,
    }


def generate_fixtures(output_dir: Path | None = None) -> dict:
    """
    Generate all 5 fixture artifacts and write them to *output_dir*.

    Returns a summary dict with validation results and written paths.
    """
    output_dir = output_dir or FIXTURE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest
    with open(DEFAULT_MANIFEST, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest_dir = DEFAULT_MANIFEST.parent

    contract = load_contract()

    # Build artifacts
    raw_bundle = _build_fixture_raw_source_bundle(manifest, manifest_dir)
    raw_bundle["_seed_entities"] = manifest.get("seed_entities", [])

    doc_set = _build_fixture_normalized_document_set(raw_bundle, manifest_dir)
    chunk_set = _build_fixture_chunk_set(doc_set)
    kg = _build_fixture_knowledge_graph(raw_bundle, doc_set)
    run_manifest = None  # built after writing other 4

    # Validate each artifact
    all_errors = []
    artifacts = {
        "RawSourceBundle": raw_bundle,
        "NormalizedDocumentSet": doc_set,
        "ChunkSet": chunk_set,
        "KnowledgeGraphPackage": kg,
    }

    for name, art in artifacts.items():
        ok, errs = validate_artifact(art, contract)
        if not ok:
            for e in errs:
                msg = f"[{name}] {e}"
                all_errors.append(msg)
                print(f"  WARN: {msg}", file=sys.stderr)
        else:
            print(f"  ✓ {name} passed contract validation")

    # Write artifacts with stable filenames
    written_files = []
    filenames = {
        "RawSourceBundle": "RawSourceBundle.json",
        "NormalizedDocumentSet": "NormalizedDocumentSet.json",
        "ChunkSet": "ChunkSet.json",
        "KnowledgeGraphPackage": "KnowledgeGraphPackage.json",
    }

    for name, art in artifacts.items():
        art_copy = {k: v for k, v in art.items() if not k.startswith("_")}
        if "sources" in art_copy:
            art_copy["sources"] = [
                {k: v for k, v in s.items() if not k.startswith("_")}
                for s in art_copy["sources"]
            ]
        fpath = output_dir / filenames[name]
        with open(fpath, "w", encoding="utf-8") as fh:
            json.dump(art_copy, fh, indent=2, default=str)
        written_files.append(str(fpath))
        print(f"  Wrote {name} -> {fpath}")

    # Build & validate RunManifest
    run_manifest = _build_fixture_run_manifest(
        [filenames[n] for n in filenames],
        all_errors,
    )
    ok, errs = validate_artifact(run_manifest, contract)
    if not ok:
        for e in errs:
            msg = f"[RunManifest] {e}"
            all_errors.append(msg)
            print(f"  WARN: {msg}", file=sys.stderr)
    else:
        print("  ✓ RunManifest passed contract validation")

    rm_path = output_dir / "RunManifest.json"
    with open(rm_path, "w", encoding="utf-8") as fh:
        json.dump(run_manifest, fh, indent=2, default=str)
    written_files.append(str(rm_path))
    print(f"  Wrote RunManifest -> {rm_path}")

    summary = {
        "status": "success" if not all_errors else "completed_with_warnings",
        "fixture_dir": str(output_dir),
        "artifacts_written": written_files,
        "validation_errors": all_errors,
    }
    return summary


def main():
    print("Generating JWST integration fixtures ...")
    summary = generate_fixtures()
    print(f"\nDone: {len(summary['artifacts_written'])} artifacts written to {summary['fixture_dir']}")
    if summary["validation_errors"]:
        print(f"Warnings: {len(summary['validation_errors'])}")
        for err in summary["validation_errors"]:
            print(f"  - {err}")
    else:
        print("All artifacts passed contract validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
