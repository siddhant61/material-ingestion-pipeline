# Material Ingestion Pipeline

The ingestion module of a 3-part AI workflow stack
(`material-ingestion-pipeline` → `content-research-pipeline` → `media-generation-pipeline`).

This repository owns and produces:

| Artifact | Description |
|---|---|
| **RawSourceBundle** | Validated list of raw source inputs for a topic |
| **NormalizedDocumentSet** | Uniform document representation from heterogeneous sources |
| **ChunkSet** | Fixed-size text chunks ready for embeddings |
| **KnowledgeGraphPackage** | Nodes + edges + provenance for downstream research |
| **RunManifest** | Metadata record for each pipeline run |

Shared contracts live in [`contracts/shared_artifacts.json`](contracts/shared_artifacts.json)
and [`contracts/schemas.md`](contracts/schemas.md).

---

## Phase 1 – Current Status

Phase 1 delivers a **stable happy path** against the canonical JWST demo scaffold.
The demo scaffold lives in `demo_data/jwst_star_formation_early_universe_demo/` and
contains a manifest + directory structure with placeholder source references
(raw NASA/ESA assets are not bundled).

### What works today

- Read the demo manifest and validate it against the shared contract.
- Tolerate missing raw files gracefully (placeholder text is generated).
- Produce all five contract-aligned artifacts and write them with the
  agreed naming convention (`<topic_slug>__<ArtifactType>__<timestamp>.json`).
- Validate every produced artifact against the contract before writing.
- Full test coverage of the happy path (no API keys or heavy dependencies required).

### What is not yet implemented

- Downloading or scraping raw source content (NASA / ESA pages).
- AI-powered extraction, chunking, or graph enrichment (requires OpenAI key + full deps).
- The legacy 9-stage agent pipeline (`cli.py` / `main.py`) is preserved but not yet
  aligned with the shared contract.

---

## Quick Start – Phase 1 Demo Ingestion

```bash
# 1. Clone and enter the repo
git clone https://github.com/siddhant61/material-ingestion-pipeline.git
cd material-ingestion-pipeline

# 2. Install lightweight dependencies (no GPU / API key needed)
pip install jsonschema python-dotenv

# 3. Run the Phase 1 happy path
python ingest_demo.py

# 4. Inspect output artifacts
ls output/demo_run/
```

The output directory will contain five JSON files:

```
output/demo_run/
  jwst_star_formation_early_universe_demo__RawSourceBundle__<ts>.json
  jwst_star_formation_early_universe_demo__NormalizedDocumentSet__<ts>.json
  jwst_star_formation_early_universe_demo__ChunkSet__<ts>.json
  jwst_star_formation_early_universe_demo__KnowledgeGraphPackage__<ts>.json
  jwst_star_formation_early_universe_demo__RunManifest__<ts>.json
```

### Options

```bash
python ingest_demo.py --help
python ingest_demo.py --manifest path/to/manifest.json --output-dir path/to/output
```

### Running tests

```bash
python -m unittest test_phase1_happy_path -v
```

---

## Legacy Pipeline (Full 9-Stage)

> **Note:** The legacy pipeline is functional but **not yet contract-aligned**.
> Its outputs use different field names and schemas than the shared contract
> (e.g., `entities`/`relationships` instead of `nodes`/`edges` in the knowledge graph).
> Bridging adapters are planned for Phase 1 Sprint 2.
> See [`AUDIT.md`](AUDIT.md) for the full gap analysis.

The original AI-powered pipeline requires the full dependency set (~67 packages)
plus an `OPENAI_API_KEY`:

```bash
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
python cli.py run-pipeline --input-dir ./input --output-dir ./output
```

See [QUICKSTART.md](QUICKSTART.md), [API_USAGE.md](API_USAGE.md), and
[PIPELINE_FLOW.md](PIPELINE_FLOW.md) for details on the full pipeline.

---

## Repository Structure

```
.
├── contracts/                  # Shared cross-repo artifact contracts
│   ├── shared_artifacts.json   # Machine-readable contract
│   ├── schemas.md              # Human-readable contract
│   └── demo_manifest.md        # Canonical demo description
├── demo_data/                  # Demo scaffold (JWST topic)
│   └── jwst_star_formation_early_universe_demo/
│       ├── manifest.json       # RawSourceBundle seed manifest
│       └── sources/            # Placeholder source directories
├── core/                       # Core pipeline modules
│   ├── contract_validator.py   # Contract validation against shared_artifacts.json
│   ├── config.py               # Centralized configuration
│   ├── pipeline/               # Pipeline orchestrator
│   ├── agents/                 # Agent implementations (legacy + future)
│   └── utils/                  # Shared utilities
├── ingest_demo.py              # Phase 1 happy-path entry point
├── cli.py                      # Legacy full-pipeline CLI
├── main.py                     # Legacy compatibility wrapper
├── test_phase1_happy_path.py   # Phase 1 tests
├── test_pipeline_structure.py  # Legacy structure tests
└── requirements.txt            # Full dependency list
```

## Cross-Repo Contracts

Artifact naming convention: `<topic_slug>__<ArtifactType>__<timestamp>.json`

See [`contracts/schemas.md`](contracts/schemas.md) for full field definitions.

### Compatibility rules

- **Backward-compatible**: add optional fields, add new artifact types.
- **Breaking**: remove/rename required fields, change artifact semantics (requires version bump).

---

## Blockers & Known Issues

| Issue | Status |
|---|---|
| Raw JWST content not bundled (NASA/ESA assets) | By design – scaffold only |
| Legacy pipeline not contract-aligned | Planned for Phase 1 Sprint 2 |
| No embeddings in Phase 1 KG | Requires model access |
| Legacy KG uses `entities`/`relationships` not `nodes`/`edges` | Adapter planned |

## Audit & Phase 1 Plan

See [`AUDIT.md`](AUDIT.md) for the complete audit package including:
gap analysis, prioritized backlog, implementation order, and validation plan.

## License

MIT – see [LICENSE](LICENSE).
