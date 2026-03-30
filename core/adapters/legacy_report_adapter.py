"""
Legacy Pipeline Report → RunManifest Adapter

Converts the legacy pipeline_report.json format
(run_id/timestamp/status/steps/completion_timestamp) into the
contract-aligned RunManifest.

Field mapping:
    Legacy field          →  Contract field
    ───────────────────────────────────────
    run_id                →  source_run_id
    (generated)           →  artifact_id
    timestamp             →  created_at
    status                →  status
    steps                 →  (decomposed into inputs/outputs/metrics/errors)
    completion_timestamp  →  metrics.completion_timestamp

Fields that cannot be cleanly mapped from legacy:
    - pipeline_stage: defaults to "legacy_full_pipeline"
    - inputs: inferred from step presence (not exact paths)
    - errors: only steps with status != "completed" are captured
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


def adapt_legacy_report(
    legacy_report: Dict[str, Any],
    *,
    pipeline_stage: str = "legacy_full_pipeline",
    pipeline_name: str = "material-ingestion-pipeline",
) -> Dict[str, Any]:
    """
    Convert a legacy pipeline_report.json dict into a
    contract-valid RunManifest.

    Parameters
    ----------
    legacy_report : dict
        Legacy report with keys: run_id, timestamp, status, steps,
        completion_timestamp.
    pipeline_stage : str
        Value for the ``pipeline_stage`` field.
    pipeline_name : str
        Value for the ``pipeline_name`` field.

    Returns
    -------
    dict
        A RunManifest dict ready for contract validation.
    """
    steps = legacy_report.get("steps", {})

    # Build outputs list from step output paths
    outputs: List[str] = []
    for step_name, step_data in steps.items():
        out = step_data.get("output")
        if isinstance(out, str):
            outputs.append(out)
        elif isinstance(out, dict):
            for v in out.values():
                if isinstance(v, str):
                    outputs.append(v)

    # Build errors from non-completed steps
    errors: List[str] = []
    for step_name, step_data in steps.items():
        step_status = step_data.get("status", "unknown")
        if step_status not in ("completed", "skipped"):
            errors.append(f"Step '{step_name}' had status: {step_status}")

    # Build inputs from step names (best-effort; legacy format doesn't
    # record actual input paths)
    inputs: Dict[str, Any] = {
        "legacy_steps": list(steps.keys()),
    }

    # Build metrics
    total_steps = len(steps)
    completed_steps = sum(
        1 for s in steps.values() if s.get("status") == "completed"
    )
    metrics: Dict[str, Any] = {
        "total_steps": total_steps,
        "completed_steps": completed_steps,
    }
    if legacy_report.get("completion_timestamp"):
        metrics["completion_timestamp"] = legacy_report["completion_timestamp"]
    if legacy_report.get("timestamp") and legacy_report.get("completion_timestamp"):
        try:
            start = datetime.fromisoformat(legacy_report["timestamp"])
            end = datetime.fromisoformat(legacy_report["completion_timestamp"])
            metrics["duration_seconds"] = round((end - start).total_seconds(), 2)
        except (ValueError, TypeError):
            pass

    # Map legacy status to contract status
    legacy_status = legacy_report.get("status", "unknown")
    if errors:
        status = "completed_with_errors"
    elif legacy_status == "completed":
        status = "completed"
    else:
        status = legacy_status

    # Use legacy timestamp for created_at, falling back to now
    created_at = legacy_report.get("timestamp")
    if not created_at:
        created_at = datetime.now(timezone.utc).isoformat()

    return {
        "artifact_type": "RunManifest",
        "schema_version": SCHEMA_VERSION,
        "artifact_id": _new_id("rm-"),
        "created_at": created_at,
        "producer": PRODUCER,
        "source_run_id": legacy_report.get("run_id", _new_id("run-")),
        "pipeline_name": pipeline_name,
        "pipeline_stage": pipeline_stage,
        "status": status,
        "inputs": inputs,
        "outputs": outputs,
        "metrics": metrics,
        "errors": errors,
    }
