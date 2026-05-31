# Shared Directory Structure Recommendation

## Context
To support the API stabilization efforts, especially the definition of shared TypeScript interfaces for API contracts, a clear and consistent directory structure for shared components is essential. This ensures discoverability, maintainability, and proper separation of concerns.

## Recommendation

We recommend establishing a top-level `shared/` directory within the `material-ingestion-pipeline` repository (or a dedicated `api-contracts` repository if cross-repo sharing becomes extensive).

### Proposed Structure:

```
material-ingestion-pipeline/
├── src/
│   ├── api/
│   │   ├── api.py           # FastAPI application and endpoint definitions
│   │   ├── models.py        # Pydantic models for API requests/responses
│   │   └── dependencies.py  # Authentication, authorization, and other API dependencies
│   ├── core/
│   │   └── pipeline/        # Core pipeline logic
│   ├── agents/              # Business logic agents
│   └── ...
├── shared/
│   ├── api-contracts/
│   │   ├── pipeline-management.ts  # TypeScript interfaces for API requests/responses
│   │   └── index.ts                # Export all contracts
│   ├── utils/                      # Shared utility functions (e.g., date formatting, common helpers)
│   └── types/                      # Other shared TypeScript types not directly API related
├── tests/
│   ├── api/
│   │   └── test_api.py      # API integration tests
│   └── ...
├── docs/
│   ├── adrs/
│   │   └── adr-001-api-stabilization-security.md # Architectural Decision Records
│   └── ...
└── ...
```

### Rationale:
*   **`shared/api-contracts/`**: This dedicated directory will house all TypeScript interface definitions that represent the API's input and output data structures. This makes it easy for frontend teams or other API consumers to find and use these contracts.
*   **`src/api/models.py`**: Pydantic models on the backend will mirror the TypeScript interfaces, ensuring consistency.
*   **`docs/adrs/`**: A dedicated place for Architectural Decision Records to document significant architectural choices and their rationale.
*   **Clear Separation**: Distinguishes between core application logic (`src/`), shared definitions (`shared/`), documentation (`docs/`), and tests (`tests/`).

### Integration with Frontend/Other Consumers:
*   The `shared/api-contracts/` directory can be published as a separate npm package or directly consumed by frontend projects if they reside in the same monorepo or are linked via tools like `npm link` or `yarn workspaces`.
*   Alternatively, a build step could generate client SDKs from the OpenAPI specification, but defining explicit TypeScript interfaces upfront provides a stronger contract.

This structure promotes modularity, reusability, and maintainability, which are crucial for stabilizing the API and supporting future development.
