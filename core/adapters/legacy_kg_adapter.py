"""
Legacy Knowledge-Graph → KnowledgeGraphPackage Adapter

Converts the legacy KG format produced by the 9-stage pipeline
(entities/relationships/hierarchy/metadata) into the contract-aligned
KnowledgeGraphPackage format (nodes/edges/embeddings_index/provenance).

Field mapping:
    Legacy entity  →  Contract node
    ─────────────────────────────────
    id             →  node_id
    name           →  label
    type           →  node_type
    description    →  description
    (none)         →  aliases        (empty list)
    properties     →  attributes     (carried forward as-is)
    properties.sources → source_refs (mapped from list of strings)

    Legacy relationship  →  Contract edge
    ─────────────────────────────────────
    (generated)    →  edge_id
    source         →  source_node_id
    target         →  target_node_id
    type           →  relation_type
    properties.strength → weight
    properties.description → evidence
    properties.sources → source_refs
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0.0"
PRODUCER = "material-ingestion-pipeline"


def _new_id(prefix: str = "") -> str:
    short = uuid.uuid4().hex[:12]
    return f"{prefix}{short}" if prefix else short


def adapt_entity_to_node(entity: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single legacy entity to a contract-compliant node."""
    props = entity.get("properties", {})
    source_refs = []
    for s in props.get("sources", []):
        if isinstance(s, str):
            source_refs.append(s)

    return {
        "node_id": entity.get("id", _new_id("node-")),
        "label": entity.get("name", ""),
        "node_type": entity.get("type", "unknown"),
        "description": entity.get("description", ""),
        "aliases": [],
        "attributes": props,
        "source_refs": source_refs,
    }


def adapt_relationship_to_edge(
    rel: Dict[str, Any], index: int
) -> Dict[str, Any]:
    """Convert a single legacy relationship to a contract-compliant edge."""
    props = rel.get("properties", {})
    source_refs = []
    for s in props.get("sources", []):
        if isinstance(s, str):
            source_refs.append(s)

    return {
        "edge_id": f"edge-{index}",
        "source_node_id": rel.get("source", ""),
        "target_node_id": rel.get("target", ""),
        "relation_type": rel.get("type", "related_to"),
        "weight": props.get("strength", 0.5),
        "evidence": props.get("description", ""),
        "source_refs": source_refs,
    }


def adapt_legacy_kg(
    legacy_kg: Dict[str, Any],
    *,
    topic: str = "",
    graph_name: str = "",
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert an entire legacy knowledge-graph dict into a
    contract-valid KnowledgeGraphPackage.

    Parameters
    ----------
    legacy_kg : dict
        Legacy KG with keys: entities, relationships, hierarchy, metadata.
    topic : str
        Topic string for the artifact header.
    graph_name : str
        Human-readable graph name.
    run_id : str | None
        Source run ID.  Generated if not supplied.

    Returns
    -------
    dict
        A KnowledgeGraphPackage dict ready for contract validation.
    """
    entities = legacy_kg.get("entities", [])
    relationships = legacy_kg.get("relationships", [])
    metadata = legacy_kg.get("metadata", {})

    nodes = [adapt_entity_to_node(e) for e in entities]
    edges = [
        adapt_relationship_to_edge(r, i)
        for i, r in enumerate(relationships)
    ]

    provenance: Dict[str, Any] = {
        "method": "legacy_kg_adapter",
        "legacy_source": metadata.get("source", "unknown"),
        "legacy_entity_count": metadata.get("entity_count", len(entities)),
        "legacy_relationship_count": metadata.get(
            "relationship_count", len(relationships)
        ),
        "legacy_hierarchy_levels": metadata.get("hierarchy_levels", {}),
        "legacy_hierarchy_counts": metadata.get("hierarchy_counts", {}),
        "adapter_version": "1.0.0",
        "adapted_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "artifact_type": "KnowledgeGraphPackage",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _new_id("kg-"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "producer": PRODUCER,
        "source_run_id": run_id or _new_id("run-"),
        "topic": topic or metadata.get("source", ""),
        "graph_name": graph_name or "legacy_adapted_graph",
        "nodes": nodes,
        "edges": edges,
        "embeddings_index": None,
        "provenance": provenance,
    }
