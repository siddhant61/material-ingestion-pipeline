# Integration Fixtures — JWST Demo

## Overview

The `integration_fixtures/jwst/upstream/` directory contains stable,
contract-valid fixture artifacts produced by the Phase 1 lightweight
ingestion path.  Downstream repositories (`content-research-pipeline`,
`media-generation-pipeline`) can consume these files directly as
upstream inputs without running the full ingestion pipeline.

## Fixture Artifacts

| File | Artifact Type | Artifact ID |
|------|--------------|-------------|
| `RawSourceBundle.json` | RawSourceBundle | `fixture-rsb-jwst-001` |
| `NormalizedDocumentSet.json` | NormalizedDocumentSet | `fixture-nds-jwst-001` |
| `ChunkSet.json` | ChunkSet | `fixture-cs-jwst-001` |
| `KnowledgeGraphPackage.json` | KnowledgeGraphPackage | `fixture-kg-jwst-001` |
| `RunManifest.json` | RunManifest | `fixture-rm-jwst-001` |

All fixtures share:
- **`source_run_id`**: `fixture-jwst-001`
- **`schema_version`**: `1.0.0`
- **`created_at`**: `2026-03-30T00:00:00Z` (fixed for determinism)

## Regenerating Fixtures

```bash
python generate_fixtures.py
```

This requires only lightweight Phase 1 dependencies (`jsonschema`,
`python-dotenv`) — no API keys or heavy ML packages.

## Validating Fixtures

```bash
python -m unittest test_integration_fixtures -v
```

The test suite verifies:
- All 5 files exist and parse as valid JSON
- Every artifact passes contract validation against `contracts/shared_artifacts.json`
- Structural invariants (counts, stable IDs, null embeddings) hold
- Regenerated output matches the committed fixtures byte-for-byte

## Known Limitations

These fixtures are produced from the scaffold-only JWST demo manifest.
Downstream consumers should be aware of the following:

### 1. Placeholder Content

All document text in `NormalizedDocumentSet.json` is placeholder content
(e.g., `"[Placeholder: content not yet retrieved for …]"`).
Every document carries `metadata.placeholder: true`.
Real content will be populated when raw source retrieval is implemented.

### 2. Null Embeddings

- `ChunkSet.json`: every chunk has `embedding_model: null` and
  `embedding_vector_ref: null`.
- `KnowledgeGraphPackage.json`: `embeddings_index` is `null`.

Embedding generation requires model access and is not part of Phase 1.

### 3. Partial Provenance Fidelity

- **KnowledgeGraphPackage**: nodes are bootstrapped from the 10 seed
  entities listed in the demo manifest, not extracted from actual
  source content.  Edges are simple consecutive-pair "related_to"
  relationships with `weight: 0.5`.  `source_refs` on nodes and edges
  are empty.
- **RawSourceBundle**: `retrieved_at` and `checksum` are `null` for
  all sources (files were never actually fetched).
- **RunManifest**: `outputs` lists fixture filenames, not timestamped
  artifact paths.

### 4. No Sections

`NormalizedDocumentSet.json` documents have empty `sections: []`.
Section extraction requires actual content.

### 5. Fixed-Size Chunking Only

`ChunkSet.json` uses `fixed_char_500` chunking strategy — a simple
500-character split.  Semantic or token-aware chunking is not
implemented in Phase 1.

## Phase 2B — Upstream Handoff Package

As of Phase 2B, this fixture set is the **canonical upstream handoff package**
for the other two repos in the workflow stack.

### What downstream repos should consume

Downstream repos (`content-research-pipeline`, `media-generation-pipeline`)
should point to the files in this directory:

```
integration_fixtures/jwst/upstream/
├── RawSourceBundle.json          # consumed by content-research-pipeline
├── NormalizedDocumentSet.json    # consumed by content-research-pipeline
├── ChunkSet.json                 # consumed by content-research-pipeline
├── KnowledgeGraphPackage.json    # consumed by both downstream repos
├── RunManifest.json              # consumed by both downstream repos
└── handoff_manifest.json         # machine-readable package descriptor
```

The `handoff_manifest.json` file provides a machine-readable description of
the package: which artifacts are included, their IDs, which downstream repo
needs each file, the contract reference, and commands to regenerate or
validate the package.

### Validating the handoff package

Run the dedicated validation script to confirm the full package is
complete, contract-valid, and internally consistent before handing off:

```bash
python validate_upstream_handoff.py
```

This checks every artifact against `contracts/shared_artifacts.json`, verifies
all files declared in `handoff_manifest.json` exist on disk, and confirms that
all artifacts share the same `source_run_id`.

### How to regenerate

```bash
python generate_fixtures.py   # regenerates the 5 artifact files
```

`handoff_manifest.json` is a static descriptor that does not need to be
regenerated unless the artifact IDs or downstream mapping changes.

### Cross-repo implications

- **Artifact IDs are stable** — downstream repos can use them as primary keys.
- **`source_run_id = fixture-jwst-001`** — all artifacts belong to the same
  logical run.
- **Shared contract**: `contracts/shared_artifacts.json` v1.0.0.  Do not
  redefine these contracts locally in downstream repos.

## Contract Reference

These fixtures conform to `contracts/shared_artifacts.json` v1.0.0.
See `contracts/schemas.md` for the full human-readable specification.
