"""
Contract Validator

Validates artifacts against the shared artifact contract defined in
contracts/shared_artifacts.json. Used by the Phase 1 happy path and
any downstream tooling that needs to check contract compliance.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

_CONTRACT_PATH = Path(__file__).resolve().parent.parent / "contracts" / "shared_artifacts.json"


def load_contract(path: Path | None = None) -> Dict[str, Any]:
    """Load and return the shared artifact contract."""
    path = path or _CONTRACT_PATH
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_artifact(artifact: Dict[str, Any],
                      contract: Dict[str, Any] | None = None) -> Tuple[bool, List[str]]:
    """
    Validate a single artifact dict against the shared contract.

    Returns (is_valid, list_of_error_strings).
    """
    if contract is None:
        contract = load_contract()

    errors: List[str] = []

    artifact_type = artifact.get("artifact_type")
    if not artifact_type:
        errors.append("Missing required field: artifact_type")
        return False, errors

    spec = contract.get("artifacts", {}).get(artifact_type)
    if spec is None:
        errors.append(f"Unknown artifact_type: {artifact_type}")
        return False, errors

    # Check top-level required fields
    for field in spec.get("required_fields", []):
        if field not in artifact:
            errors.append(f"Missing required field: {field}")

    # Check nested item-level fields if present
    _nested_checks = [
        ("sources", "source_item_required_fields"),
        ("documents", "document_required_fields"),
        ("chunks", "chunk_required_fields"),
        ("nodes", "node_required_fields"),
        ("edges", "edge_required_fields"),
        ("scenes", "scene_required_fields"),
        ("assets", "asset_required_fields"),
    ]

    for list_key, fields_key in _nested_checks:
        items = artifact.get(list_key)
        required = spec.get(fields_key, [])
        if items and required:
            for idx, item in enumerate(items):
                for field in required:
                    if field not in item:
                        errors.append(
                            f"In {list_key}[{idx}]: missing required field: {field}"
                        )

    is_valid = len(errors) == 0
    if is_valid:
        logger.debug("Artifact %s (%s) is valid", artifact.get("artifact_id"), artifact_type)
    else:
        logger.warning(
            "Artifact %s (%s) has %d validation errors",
            artifact.get("artifact_id"), artifact_type, len(errors),
        )
    return is_valid, errors
