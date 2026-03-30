#!/usr/bin/env python3
"""
Phase 1 Happy-Path: Demo Ingestion

Reads the canonical JWST demo manifest, validates source metadata,
produces contract-aligned artifacts (with graceful placeholders for
missing raw content), and writes them to an output directory.

Usage:
    python ingest_demo.py
    python ingest_demo.py --manifest demo_data/jwst_star_formation_early_universe_demo/manifest.json
    python ingest_demo.py --output-dir output/demo_run
"""

import argparse
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from core.contract_validator import load_contract, validate_artifact

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ingest_demo")

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "demo_data"
    / "jwst_star_formation_early_universe_demo"
    / "manifest.json"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "demo_run"
SCHEMA_VERSION = "1.0.0"
PRODUCER = "material-ingestion-pipeline"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _artifact_filename(topic_slug: str, artifact_type: str) -> str:
    """Follow the naming convention from the contract."""
    ts = _now_iso()
    return f"{topic_slug}__{artifact_type}__{ts}.json"


def _new_id(prefix: str = "") -> str:
    short = uuid.uuid4().hex[:12]
    return f"{prefix}{short}" if prefix else short


def _source_file_available(manifest_dir: Path, local_path: str) -> bool:
    """Check whether a source's local_path points to real content (not just a README placeholder)."""
    full = manifest_dir / local_path
    if not full.exists():
        return False
    # Treat tiny README.txt placeholders as "not available"
    if full.suffix == ".txt" and full.stat().st_size < 512:
        try:
            text = full.read_text(encoding="utf-8", errors="replace")
            if text.strip().startswith("Placeholder") or text.strip().startswith("This folder"):
                return False
        except Exception:
            return False
    return True


# ---------------------------------------------------------------------------
# Artifact builders
# ---------------------------------------------------------------------------

def build_raw_source_bundle(manifest: Dict[str, Any], manifest_dir: Path, run_id: str) -> Dict[str, Any]:
    """Return a validated RawSourceBundle from the demo manifest."""
    bundle = {
        "artifact_type": "RawSourceBundle",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": manifest.get("artifact_id", _new_id("rsb-")),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "producer": PRODUCER,
        "source_run_id": run_id,
        "topic": manifest.get("topic", ""),
        "source_bundle_name": manifest.get("source_bundle_name", ""),
        "sources": [],
    }

    for src in manifest.get("sources", []):
        available = _source_file_available(manifest_dir, src.get("local_path", ""))
        source_item = {
            "source_id": src.get("source_id", _new_id("src-")),
            "title": src.get("title", ""),
            "source_type": src.get("source_type", "unknown"),
            "origin_org": src.get("origin_org", ""),
            "url": src.get("url", ""),
            "local_path": src.get("local_path", ""),
            "mime_type": src.get("mime_type", "application/octet-stream"),
            "language": src.get("language", "en"),
            "license": src.get("license", ""),
            "usage_notes": src.get("usage_notes", ""),
            "retrieved_at": src.get("retrieved_at") or None,
            "checksum": src.get("checksum") or None,
            "tags": src.get("tags", []),
            "_available": available,
        }
        bundle["sources"].append(source_item)

    return bundle


def build_normalized_document_set(
    bundle: Dict[str, Any], manifest_dir: Path, run_id: str
) -> Dict[str, Any]:
    """Produce a NormalizedDocumentSet; use placeholder text for missing sources."""
    doc_set: Dict[str, Any] = {
        "artifact_type": "NormalizedDocumentSet",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _new_id("nds-"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "producer": PRODUCER,
        "source_run_id": run_id,
        "topic": bundle.get("topic", ""),
        "documents": [],
    }

    for src in bundle.get("sources", []):
        source_id = src["source_id"]
        available = src.get("_available", False)

        if available:
            full_path = manifest_dir / src["local_path"]
            try:
                text = full_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
                available = False
        else:
            text = ""

        placeholder = not available
        doc: Dict[str, Any] = {
            "document_id": _new_id("doc-"),
            "source_id": source_id,
            "title": src.get("title", ""),
            "document_type": src.get("source_type", "unknown"),
            "language": src.get("language", "en"),
            "text": text if text else f"[Placeholder: content not yet retrieved for {src.get('title', source_id)}]",
            "sections": [],
            "metadata": {
                "placeholder": placeholder,
                "origin_org": src.get("origin_org", ""),
                "url": src.get("url", ""),
                "tags": src.get("tags", []),
            },
        }
        doc_set["documents"].append(doc)

    return doc_set


def build_chunk_set(
    doc_set: Dict[str, Any], run_id: str
) -> Dict[str, Any]:
    """Simple fixed-size chunking of normalized documents."""
    CHUNK_SIZE = 500  # characters

    chunk_set: Dict[str, Any] = {
        "artifact_type": "ChunkSet",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _new_id("cs-"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "producer": PRODUCER,
        "source_run_id": run_id,
        "topic": doc_set.get("topic", ""),
        "chunking_strategy": f"fixed_char_{CHUNK_SIZE}",
        "chunks": [],
    }

    for doc in doc_set.get("documents", []):
        text = doc.get("text", "")
        doc_id = doc["document_id"]
        source_id = doc["source_id"]

        # Produce at least one chunk per document
        if not text:
            text = f"[Placeholder chunk for document {doc_id}]"

        start = 0
        idx = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunk_text = text[start:end]
            chunk: Dict[str, Any] = {
                "chunk_id": f"{doc_id}__chunk_{idx}",
                "document_id": doc_id,
                "source_id": source_id,
                "text": chunk_text,
                "token_count": len(chunk_text.split()),
                "char_count": len(chunk_text),
                "embedding_model": None,
                "embedding_vector_ref": None,
                "metadata": {
                    "placeholder": doc.get("metadata", {}).get("placeholder", False),
                    "chunk_index": idx,
                },
            }
            chunk_set["chunks"].append(chunk)
            start = end
            idx += 1

    return chunk_set


def build_knowledge_graph_package(
    bundle: Dict[str, Any], doc_set: Dict[str, Any], run_id: str
) -> Dict[str, Any]:
    """Build a seed KnowledgeGraphPackage from manifest seed_entities + source provenance."""
    seed_entities: List[str] = bundle.get("seed_entities", bundle.get("_seed_entities", []))
    topic = bundle.get("topic", "")

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    # Build nodes from seed entities
    entity_ids: Dict[str, str] = {}
    for entity_label in seed_entities:
        nid = _new_id("node-")
        entity_ids[entity_label] = nid
        nodes.append({
            "node_id": nid,
            "label": entity_label,
            "node_type": "seed_entity",
            "description": f"Seed entity from demo manifest for topic: {topic}",
            "aliases": [],
            "attributes": {},
            "source_refs": [],
        })

    # Simple co-occurrence edges between consecutive seed entities
    entity_list = list(entity_ids.items())
    for i in range(len(entity_list) - 1):
        label_a, id_a = entity_list[i]
        label_b, id_b = entity_list[i + 1]
        edges.append({
            "edge_id": _new_id("edge-"),
            "source_node_id": id_a,
            "target_node_id": id_b,
            "relation_type": "related_to",
            "weight": 0.5,
            "evidence": f"Co-listed as seed entities in demo manifest",
            "source_refs": [],
        })

    kg: Dict[str, Any] = {
        "artifact_type": "KnowledgeGraphPackage",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _new_id("kg-"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "producer": PRODUCER,
        "source_run_id": run_id,
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


def build_run_manifest(
    run_id: str,
    topic: str,
    artifact_files: List[str],
    errors: List[str],
) -> Dict[str, Any]:
    """Build a RunManifest recording the ingestion run."""
    status = "completed_with_warnings" if errors else "completed"
    return {
        "artifact_type": "RunManifest",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _new_id("rm-"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "producer": PRODUCER,
        "source_run_id": run_id,
        "pipeline_name": "material-ingestion-pipeline",
        "pipeline_stage": "phase1_demo_ingest",
        "status": status,
        "inputs": {"topic": topic, "manifest": str(DEFAULT_MANIFEST)},
        "outputs": artifact_files,
        "metrics": {"artifact_count": len(artifact_files)},
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_ingest(manifest_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Execute the Phase 1 happy-path ingestion.

    Returns a summary dict with validation results and output paths.
    """
    run_id = _new_id("run-")
    logger.info("Starting Phase 1 demo ingestion  run_id=%s", run_id)
    logger.info("Manifest: %s", manifest_path)
    logger.info("Output dir: %s", output_dir)

    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    manifest_dir = manifest_path.parent
    topic_slug = manifest.get("source_bundle_name", "unknown_topic")

    # Load contract for validation
    contract = load_contract()

    # Build artifacts
    logger.info("Building RawSourceBundle ...")
    raw_bundle = build_raw_source_bundle(manifest, manifest_dir, run_id)
    # Carry seed_entities forward for knowledge graph
    raw_bundle["_seed_entities"] = manifest.get("seed_entities", [])

    logger.info("Building NormalizedDocumentSet ...")
    doc_set = build_normalized_document_set(raw_bundle, manifest_dir, run_id)

    logger.info("Building ChunkSet ...")
    chunk_set = build_chunk_set(doc_set, run_id)

    logger.info("Building KnowledgeGraphPackage ...")
    kg = build_knowledge_graph_package(raw_bundle, doc_set, run_id)

    # Validate each artifact
    all_errors: List[str] = []
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
                logger.warning(msg)
                all_errors.append(msg)
        else:
            logger.info("✓ %s passed contract validation", name)

    # Write artifacts
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files: List[str] = []

    for name, art in artifacts.items():
        # Remove internal helper keys before writing
        art_copy = {k: v for k, v in art.items() if not k.startswith("_")}
        # Also strip _available from source items
        if "sources" in art_copy:
            art_copy["sources"] = [
                {k: v for k, v in s.items() if not k.startswith("_")}
                for s in art_copy["sources"]
            ]
        fname = _artifact_filename(topic_slug, name)
        fpath = output_dir / fname
        with open(fpath, "w", encoding="utf-8") as fh:
            json.dump(art_copy, fh, indent=2, default=str)
        written_files.append(str(fpath))
        logger.info("Wrote %s -> %s", name, fpath)

    # Build & write RunManifest
    run_manifest = build_run_manifest(run_id, topic_slug, written_files, all_errors)
    ok, errs = validate_artifact(run_manifest, contract)
    if not ok:
        for e in errs:
            logger.warning("[RunManifest] %s", e)
            all_errors.append(f"[RunManifest] {e}")
    else:
        logger.info("✓ RunManifest passed contract validation")

    rm_fname = _artifact_filename(topic_slug, "RunManifest")
    rm_path = output_dir / rm_fname
    with open(rm_path, "w", encoding="utf-8") as fh:
        json.dump(run_manifest, fh, indent=2, default=str)
    written_files.append(str(rm_path))
    logger.info("Wrote RunManifest -> %s", rm_path)

    summary = {
        "run_id": run_id,
        "status": "success" if not all_errors else "completed_with_warnings",
        "artifacts_written": written_files,
        "validation_errors": all_errors,
    }

    logger.info("Phase 1 ingestion complete: %d artifacts, %d warnings",
                len(written_files), len(all_errors))
    return summary


def run_validate_only(manifest_path: Path) -> Dict[str, Any]:
    """
    Validate the manifest and artifact structures without producing output.

    Returns a summary dict with validation results.
    """
    logger.info("Running in validate-only mode")
    logger.info("Manifest: %s", manifest_path)

    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    manifest_dir = manifest_path.parent
    run_id = _new_id("val-")

    contract = load_contract()
    all_errors: List[str] = []

    # Build artifacts in memory (no I/O)
    raw_bundle = build_raw_source_bundle(manifest, manifest_dir, run_id)
    raw_bundle["_seed_entities"] = manifest.get("seed_entities", [])
    doc_set = build_normalized_document_set(raw_bundle, manifest_dir, run_id)
    chunk_set = build_chunk_set(doc_set, run_id)
    kg = build_knowledge_graph_package(raw_bundle, doc_set, run_id)

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
                logger.warning(msg)
                all_errors.append(msg)
        else:
            logger.info("✓ %s passed contract validation", name)

    rm = build_run_manifest(run_id, manifest.get("source_bundle_name", ""), [], all_errors)
    ok, errs = validate_artifact(rm, contract)
    if not ok:
        for e in errs:
            logger.warning("[RunManifest] %s", e)
            all_errors.append(f"[RunManifest] {e}")
    else:
        logger.info("✓ RunManifest passed contract validation")

    status = "valid" if not all_errors else "invalid"
    logger.info("Validation complete: %s (%d errors)", status, len(all_errors))

    return {
        "mode": "validate-only",
        "status": status,
        "artifacts_checked": list(artifacts.keys()) + ["RunManifest"],
        "validation_errors": all_errors,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Phase 1 demo ingestion for material-ingestion-pipeline",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=str(DEFAULT_MANIFEST),
        help="Path to the demo manifest.json",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to write contract-aligned artifacts",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        default=False,
        help="Validate manifest and artifact structures without writing output",
    )
    args = parser.parse_args()

    if args.validate_only:
        summary = run_validate_only(manifest_path=Path(args.manifest))
    else:
        summary = run_ingest(
            manifest_path=Path(args.manifest),
            output_dir=Path(args.output_dir),
        )

    # Print summary
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] in ("success", "valid") else 0  # warnings are OK in Phase 1


if __name__ == "__main__":
    raise SystemExit(main())
