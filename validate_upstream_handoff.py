#!/usr/bin/env python3
"""
Validate the upstream handoff package for Phase 2B.

Checks that the canonical JWST upstream fixture set is complete, structurally
sound, and contract-valid so downstream repos can safely consume it.

Usage:
    python validate_upstream_handoff.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.contract_validator import load_contract, validate_artifact

UPSTREAM_DIR = PROJECT_ROOT / "integration_fixtures" / "jwst" / "upstream"
HANDOFF_MANIFEST_FILE = UPSTREAM_DIR / "handoff_manifest.json"

EXPECTED_ARTIFACTS = [
    "RawSourceBundle",
    "NormalizedDocumentSet",
    "ChunkSet",
    "KnowledgeGraphPackage",
    "RunManifest",
]

EXPECTED_SHARED_RUN_ID = "fixture-jwst-001"


def _check(label: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    line = f"  [{status}] {label}"
    if detail:
        line += f": {detail}"
    print(line)
    return passed


def validate_handoff() -> bool:
    """Run all handoff validation checks. Returns True if all pass."""
    print(f"Validating upstream handoff package: {UPSTREAM_DIR}\n")

    all_passed = True

    # 1. Handoff manifest exists and is valid JSON
    manifest_ok = HANDOFF_MANIFEST_FILE.is_file()
    all_passed &= _check("handoff_manifest.json exists", manifest_ok)
    if not manifest_ok:
        print("\nERROR: handoff_manifest.json missing — cannot continue.")
        return False

    with open(HANDOFF_MANIFEST_FILE, "r", encoding="utf-8") as fh:
        handoff = json.load(fh)
    all_passed &= _check("handoff_manifest.json parses as valid JSON", True)

    # 2. All 5 artifact files declared in handoff manifest are present
    declared = {a["filename"]: a for a in handoff.get("artifacts", [])}
    expected_filenames = {f"{name}.json" for name in EXPECTED_ARTIFACTS}
    missing_declared = expected_filenames - set(declared.keys())
    all_passed &= _check(
        "All 5 artifact types declared in handoff_manifest.json",
        not missing_declared,
        f"missing: {missing_declared}" if missing_declared else "",
    )

    # 3. All declared files exist on disk
    for filename, meta in declared.items():
        fpath = UPSTREAM_DIR / filename
        ok = fpath.is_file()
        all_passed &= _check(f"{filename} exists on disk", ok)

    # 4. Contract validation for each artifact
    contract = load_contract()
    loaded_artifacts: dict[str, dict] = {}
    for name in EXPECTED_ARTIFACTS:
        fpath = UPSTREAM_DIR / f"{name}.json"
        if not fpath.is_file():
            all_passed &= _check(f"{name} contract-valid", False, "file missing")
            continue
        with open(fpath, "r", encoding="utf-8") as fh:
            artifact = json.load(fh)
        loaded_artifacts[name] = artifact
        ok, errors = validate_artifact(artifact, contract)
        all_passed &= _check(
            f"{name} contract-valid",
            ok,
            "; ".join(errors) if errors else "",
        )

    # 5. All artifacts share the same source_run_id
    run_ids = {
        name: art.get("source_run_id")
        for name, art in loaded_artifacts.items()
    }
    consistent = all(rid == EXPECTED_SHARED_RUN_ID for rid in run_ids.values())
    mismatched = {k: v for k, v in run_ids.items() if v != EXPECTED_SHARED_RUN_ID}
    all_passed &= _check(
        f"All artifacts share source_run_id={EXPECTED_SHARED_RUN_ID!r}",
        consistent,
        str(mismatched) if not consistent else "",
    )

    # 6. RunManifest references all other artifacts
    if "RunManifest" in loaded_artifacts:
        rm_outputs = set(loaded_artifacts["RunManifest"].get("outputs", []))
        expected_outputs = {f"{n}.json" for n in EXPECTED_ARTIFACTS if n != "RunManifest"}
        missing_outputs = expected_outputs - rm_outputs
        all_passed &= _check(
            "RunManifest.outputs lists all 4 data artifact filenames",
            not missing_outputs,
            f"missing: {missing_outputs}" if missing_outputs else "",
        )

    # 7. Artifact IDs in handoff_manifest.json match artifact files
    for entry in handoff.get("artifacts", []):
        name = entry["artifact_type"]
        expected_id = entry.get("artifact_id")
        if name in loaded_artifacts and expected_id:
            actual_id = loaded_artifacts[name].get("artifact_id")
            ok = actual_id == expected_id
            all_passed &= _check(
                f"{name} artifact_id matches handoff_manifest.json",
                ok,
                f"expected={expected_id!r} actual={actual_id!r}" if not ok else "",
            )

    print()
    if all_passed:
        print("All checks passed. Upstream handoff package is ready for downstream consumption.")
    else:
        print("One or more checks FAILED. Fix the issues above before handing off to downstream repos.")

    return all_passed


def main() -> int:
    return 0 if validate_handoff() else 1


if __name__ == "__main__":
    raise SystemExit(main())
