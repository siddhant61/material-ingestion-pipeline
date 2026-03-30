# Audit Package – material-ingestion-pipeline

> Completed: 2026-03-30  
> Scope: Phase 1 readiness assessment against shared contracts  
> Branch: `copilot/audit-repo-structure`

---

## 1. Current Entrypoints

| File | Type | Works Without API Key | Contract-Aligned | Notes |
|------|------|----------------------|------------------|-------|
| `ingest_demo.py` | Phase 1 CLI | ✅ Yes | ✅ Yes | Reads JWST demo manifest → produces 5 contract-compliant artifacts. Requires only `jsonschema`, `python-dotenv`. |
| `cli.py` | Legacy 9-stage CLI (Click) | ❌ No | ❌ No | `python cli.py run-pipeline --input-dir … --output-dir …`. Needs full `requirements.txt` + `OPENAI_API_KEY`. |
| `main.py` | Backward-compat wrapper | ❌ No | ❌ No | Wraps `cli.py` for legacy test imports. Same deps. |
| `api.py` | FastAPI server | ❌ No | ❌ No | HTTP interface over legacy pipeline. Needs FastAPI + agents. |
| `ui.py` | Streamlit dashboard | ❌ No | ❌ No | Web UI calling FastAPI on `localhost:8000`. |
| `prepare_for_vision_board.py` | Export helper | ❌ No | ❌ No | Packages KG + embeddings for downstream. Pre-dates contracts. |
| `example_api_client.py` | API demo | ❌ No | ❌ No | Shows how to call `api.py`. |

**Summary:** Only `ingest_demo.py` is contract-aligned and dependency-light. All other entrypoints need the full stack.

---

## 2. Repo Purpose as Implemented Today

The repo serves two overlapping purposes:

1. **Legacy educational-material pipeline** (pre-contract): A 9-stage agent pipeline that takes course PDFs/transcripts/slides, runs them through OpenAI, and produces a knowledge graph with visualizations and embeddings. This is the original codebase.

2. **Phase 1 contract-aligned ingestion** (new): A lightweight entry point (`ingest_demo.py`) that reads a demo manifest, validates it against `contracts/shared_artifacts.json`, and writes five JSON artifacts in the agreed naming convention. No AI, no heavy deps.

The two paths share the same repo directory and `core/` package but do not yet share data flow. The legacy pipeline does not produce contract-shaped output, and the Phase 1 path does not use the agents.

---

## 3. Mismatch vs README

The README (rewritten in the Phase 1 commit) is **mostly accurate**. Gaps:

| Claim | Accurate? | Issue |
|-------|-----------|-------|
| "Stable happy path against JWST demo" | ✅ | Verified: 16/16 tests pass, 5 artifacts validated. |
| "Tolerate missing raw files gracefully" | ✅ | Verified: placeholder text generated. |
| "Full test coverage of happy path" | ✅ | 16 tests covering validator, builders, end-to-end. |
| "Legacy pipeline preserved but not contract-aligned" | ✅ | Accurate. |
| Legacy Quick Start instructions | ⚠️ | Tells users to run `pip install -r requirements.txt` then `cli.py`, but this fails without `OPENAI_API_KEY` and ~67 heavy packages. README should note this more clearly. |
| Repo Structure diagram | ⚠️ | Doesn't list `api.py`, `ui.py`, `prepare_for_vision_board.py`, `example_api_client.py`, or legacy PHASE*.md docs. Acceptable simplification but worth noting. |
| "No embeddings in Phase 1 KG" listed as blocker | ✅ | Accurate. |

**No false claims found.** Minor clarifications recommended (see §7).

---

## 4. Mismatch vs Contracts

### 4a. `contracts/shared_artifacts.json`

**Phase 1 happy path (`ingest_demo.py`):** Fully aligned.

All five artifact types this repo owns pass `validate_artifact()`:
- `RawSourceBundle` — 9 top-level + 13 source-item fields ✅
- `NormalizedDocumentSet` — 8 top-level + 8 document fields ✅
- `ChunkSet` — 9 top-level + 9 chunk fields ✅
- `KnowledgeGraphPackage` — 12 top-level + 7 node + 7 edge fields ✅
- `RunManifest` — 14 top-level fields ✅

Naming convention (`<topic_slug>__<ArtifactType>__<timestamp>.json`) ✅

**Legacy pipeline:** Not aligned. Specific gaps:

| Contract Artifact | Legacy Equivalent | Gap |
|-------------------|-------------------|-----|
| `RawSourceBundle` | None produced | Legacy reads files directly, no manifest-shaped bundle emitted. |
| `NormalizedDocumentSet` | `output/transcript_results.json`, `output/slide_results.json` | Different schema: `{processed_count, error_count, slides/transcripts}` vs contract's `{documents: [{document_id, source_id, …}]}`. |
| `ChunkSet` | None explicitly | Chunking happens inside agents but no standalone artifact written. |
| `KnowledgeGraphPackage` | `output/knowledge_graph/knowledge_graph.json` | Uses `{entities, relationships, hierarchy, metadata}` instead of `{nodes, edges, embeddings_index, provenance}`. Has 492 entities + 3008 relationships, but the field names and structure differ. |
| `RunManifest` | `output/pipeline_report.json` | Uses `{run_id, timestamp, status, steps, completion_timestamp}` — missing `artifact_type`, `schema_version`, `producer`, `pipeline_stage`, `inputs`, `outputs`, `metrics`, `errors`. |

### 4b. `contracts/schemas.md`

All field definitions match `shared_artifacts.json`. No extra constraints found in `schemas.md` that `shared_artifacts.json` doesn't already encode. The human-readable doc and the machine-readable JSON are consistent.

### 4c. `contracts/demo_manifest.md`

Describes the JWST demo scaffold. `demo_data/jwst_star_formation_early_universe_demo/manifest.json` matches the described structure. The scaffold is intentionally placeholder-only. The 10 seed entities listed in the manifest match the doc.

---

## 5. Happy-Path Status

### Phase 1 happy path: ✅ WORKING

```
python ingest_demo.py
→ 5 artifacts written to output/demo_run/
→ All pass contract validation
→ 16/16 tests pass in <1 second
→ No API keys, no heavy dependencies
```

Tested flows:
- Default manifest + default output dir
- Custom `--manifest` and `--output-dir` flags
- All sources missing (scaffold-only): graceful placeholders
- Contract validator catches invalid artifacts (missing fields, bad types, bad nested items)
- Naming convention followed

### Legacy pipeline happy path: ⚠️ NOT TESTABLE HERE

Requires `OPENAI_API_KEY` + full dependency install. Previous output in `output/` suggests it ran successfully at some point (492 entities, 3008 relationships, visualizations). Cannot verify in this environment.

---

## 6. Broken or Fragile Paths

| Path | Severity | Description |
|------|----------|-------------|
| **Legacy agent imports** | Medium | `cli.py`, `main.py` fail to import without heavy deps (`numpy`, `fitz`, `langchain`, `torch`, `networkx`). No graceful degradation — immediate `ModuleNotFoundError`. |
| **Legacy tests** | Medium | 8 of 9 test files (`test_cli.py`, `test_pipeline_structure.py`, etc.) fail on import because they import agents that need OpenAI/numpy. Only `test_phase1_happy_path.py` works without full deps. |
| **`core/config.py` side effect** | Low | `Settings.__init__()` creates 10+ directories on import. This is benign but means importing `core.config` always creates `input/` and `output/` trees. |
| **Output dir not isolated** | Low | Legacy outputs exist in `output/` alongside demo run. No run-isolation by default. `ingest_demo.py` uses `output/demo_run/` subdirectory, but `cli.py` writes to `output/` root. |
| **Duplicate deps in `requirements.txt`** | Low | Several packages listed twice with different version specs (e.g., `numpy==1.24.3` and `numpy>=1.20.0`; `matplotlib==3.8.0` and `matplotlib>=3.4.0`). Pip resolves this but it's confusing. |
| **No `__init__.py` in some paths** | Low | `core/agents/course_context/` has no `__init__.py`, though Python 3 namespace packages may still work. |

---

## 7. Highest-Leverage Phase 1 Changes

Ranked by impact÷effort:

### P0 — Already done
- [x] Contract validator (`core/contract_validator.py`)
- [x] Phase 1 entry point (`ingest_demo.py`)
- [x] Phase 1 tests (`test_phase1_happy_path.py`) — 16 tests
- [x] README rewrite
- [x] Demo manifest + scaffold

### P1 — Should do next (small, high value)

1. **Bridge legacy KG output → `KnowledgeGraphPackage` contract shape**  
   The legacy pipeline already produces 492 entities and 3008 relationships. Writing a thin adapter (`entities` → `nodes`, `relationships` → `edges`, add required provenance fields) would make existing legacy runs contract-compliant retroactively. This is the single highest-leverage change because it unlocks downstream `content-research-pipeline` consumption without requiring a full pipeline re-run.

2. **Bridge legacy pipeline report → `RunManifest` contract shape**  
   Similarly, `output/pipeline_report.json` has the core info but wrong shape. A small adapter adds `artifact_type`, `schema_version`, `producer`, etc.

3. **Add `--validate-only` flag to `ingest_demo.py`**  
   Let users validate an existing manifest without producing artifacts. Useful for CI and cross-repo checks.

### P2 — Should do in Phase 1 (medium effort)

4. **Legacy pipeline contract wrapper**  
   Wrap `MaterialIngestionPipeline.save_results()` or add a post-processing step that converts all legacy outputs to contract shape. This would make the full 9-stage pipeline contract-aware without rewriting agents.

5. **Unified test runner**  
   Add a `Makefile` or `scripts/test.sh` that separates "lightweight tests" (Phase 1, no API key) from "full tests" (requires API key). Currently there's no way to run just the safe tests.

### P3 — Phase 2 scope (defer)

6. Connect `ingest_demo.py` to real source retrieval (NASA/ESA pages)
7. Make agents emit contract-shaped intermediate artifacts
8. Replace fixed-char chunking with semantic chunking
9. Add embedding vectors to KG nodes

---

## 8. Proposed Implementation Order

```
Phase 1 Sprint 1 (this PR):
  ✅ Audit package (this document)
  ✅ Contract validator
  ✅ Phase 1 happy path (ingest_demo.py)
  ✅ Phase 1 tests (16/16 passing)
  ✅ README update

Phase 1 Sprint 2 (next PR):
  → Legacy KG → KnowledgeGraphPackage adapter
  → Legacy pipeline report → RunManifest adapter
  → --validate-only flag for ingest_demo.py
  → Lightweight test runner script

Phase 1 Sprint 3 (follow-up PR):
  → Contract wrapper around MaterialIngestionPipeline
  → Separate requirements-phase1.txt (minimal deps)
  → Document cross-repo handoff procedure

Phase 2 (separate planning):
  → Real source retrieval
  → Agent-level contract awareness
  → Semantic chunking
  → Embedding integration
```

---

## 9. Validation Plan

### What is validated today

| Check | Method | Result |
|-------|--------|--------|
| Contract validator logic | `test_phase1_happy_path.py::TestContractValidator` (5 tests) | ✅ Pass |
| Demo manifest exists and is valid | `test_phase1_happy_path.py::TestDemoManifestExists` (2 tests) | ✅ Pass |
| Each artifact builder produces contract-valid output | `test_phase1_happy_path.py::TestArtifactBuilders` (5 tests) | ✅ Pass |
| End-to-end ingestion produces 5 valid artifacts | `test_phase1_happy_path.py::TestEndToEndIngest` (3 tests) | ✅ Pass |
| Naming convention compliance | `test_phase1_happy_path.py::test_artifact_naming_convention` | ✅ Pass |
| Graceful handling of missing sources | `test_phase1_happy_path.py::test_graceful_with_missing_sources` | ✅ Pass |
| Manual CLI run | `python ingest_demo.py` | ✅ Pass |

### What should be validated next (Phase 1 Sprint 2)

| Check | Proposed Method |
|-------|----------------|
| Legacy KG adapter produces valid `KnowledgeGraphPackage` | Unit test with sample legacy KG data |
| Legacy report adapter produces valid `RunManifest` | Unit test with sample legacy report |
| `--validate-only` flag exits without writing | CLI integration test |
| All Phase 1 tests pass in CI without API key | GitHub Actions workflow (lightweight only) |

### Validation commands

```bash
# Phase 1 tests (no deps beyond jsonschema + python-dotenv)
python -m unittest test_phase1_happy_path -v

# Phase 1 happy path run
python ingest_demo.py

# Inspect output
ls output/demo_run/
python -c "
import json
from core.contract_validator import load_contract, validate_artifact
contract = load_contract()
import glob
for f in sorted(glob.glob('output/demo_run/*.json')):
    with open(f) as fh:
        art = json.load(fh)
    ok, errs = validate_artifact(art, contract)
    print(f'{'✅' if ok else '❌'} {art[\"artifact_type\"]}: {len(errs)} errors')
"
```

---

## 10. Cross-Repo Implications

### What this repo produces for downstream consumers

| Artifact | Consumer | Status |
|----------|----------|--------|
| `RawSourceBundle` | `content-research-pipeline` | ✅ Produced by `ingest_demo.py` |
| `NormalizedDocumentSet` | `content-research-pipeline` | ✅ Produced (placeholder content) |
| `ChunkSet` | `content-research-pipeline` | ✅ Produced (placeholder content) |
| `KnowledgeGraphPackage` | `content-research-pipeline`, `media-generation-pipeline` | ✅ Produced (seed entities only) |
| `RunManifest` | All pipelines (metadata) | ✅ Produced |

### Contract tensions

1. **Placeholder vs real content**: Phase 1 artifacts have correct schema but placeholder text. Downstream repos must tolerate `metadata.placeholder == true` documents gracefully. This should be documented as a contract expectation.

2. **`seed_entities` field**: The demo manifest includes `seed_entities` (10 JWST topics) which `ingest_demo.py` uses to populate the KG. This field is NOT in the `RawSourceBundle` required fields per the contract. Currently handled as an extra field (backward-compatible), but downstream repos should not depend on it being present in all bundles.

3. **`_available` internal field**: `ingest_demo.py` uses `_available` internally on source items during processing but strips it before writing. This is correct behavior — no contract violation.

4. **`embeddings_index: null`**: The KG artifact sets `embeddings_index` to `null` because Phase 1 doesn't generate embeddings. The contract requires the field to be present (it is), but downstream consumers must handle `null` gracefully.

5. **`provenance` shape**: The contract requires `provenance` in `KnowledgeGraphPackage` but doesn't specify its internal structure. Phase 1 uses `{method, source_manifest}`. This should be documented as an informal convention until the contract specifies it.

### Recommended cross-repo coordination

- `content-research-pipeline` should handle `metadata.placeholder == true` in `NormalizedDocumentSet` and `ChunkSet`.
- `content-research-pipeline` should handle `embeddings_index == null` in `KnowledgeGraphPackage`.
- All repos should agree on `provenance` internal structure before Phase 2.
- `seed_entities` in the manifest should either be added to the `RawSourceBundle` contract as an optional field, or removed from the ingestion flow.
