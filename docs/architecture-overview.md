# Architecture Overview: Material Ingestion Pipeline API

This document provides an overview of the core API architecture for the `material-ingestion-pipeline`, highlighting its key components, data flow, and design principles.

## High-Level Overview

The Material Ingestion Pipeline API is a FastAPI-based application designed to manage the lifecycle of material ingestion runs. It provides endpoints for initiating pipelines, monitoring their status, and retrieving reports and visualizations. The architecture emphasizes modularity, clear data contracts, secure authentication, and persistent state management.

## Key Architectural Principles

*   **Modularity**: Separation of concerns into distinct Python modules (API routes, data models, dependencies, database logic).
*   **Clear Contracts**: Strict API input/output validation using Pydantic models, aligned with shared TypeScript interfaces.
*   **Asynchronous Processing**: Long-running pipeline tasks are handled asynchronously using FastAPI's `BackgroundTasks` to maintain API responsiveness.
*   **Persistent State**: Pipeline run statuses and data are stored in a relational database using SQLAlchemy ORM, ensuring data durability and scalability.
*   **Security**: Authentication is implemented using JWTs, with a configurable secret key for token validation.

## Core Components

### `src/api/api.py`

This is the main FastAPI application file. It defines all API routes (endpoints), integrates Pydantic models for request/response handling, uses authentication dependencies, and orchestrates the initiation of background pipeline tasks. It also includes application-wide settings like title, description, and global error responses.

### `src/api/models.py`

Contains all Pydantic `BaseModel` definitions used for API request bodies and response payloads. These models enforce strict data types and structures, ensuring consistency and enabling automatic documentation. They are designed to mirror the shared TypeScript interfaces for frontend-backend contract alignment.

### `src/api/dependencies.py`

Houses reusable dependency functions for FastAPI. The most critical dependency here is `authenticate_user`, which handles JWT validation based on an environment-configured secret key. This centralizes authentication logic and allows it to be easily applied to protected endpoints.

### `src/core/db.py`

Manages the database connection and defines the SQLAlchemy ORM models. The `PipelineRun` model represents the persistent state of an ingestion pipeline run, storing its ID, material ID, status, progress, and other relevant metadata. This module provides functions for initializing the database and obtaining asynchronous database sessions.

### Background Task: `run_pipeline_in_background`

An asynchronous function (defined in `src/api/api.py`) that simulates the actual material ingestion process. When a pipeline run is initiated, this function is scheduled as a background task. It periodically updates the pipeline's status and progress in the database, ensuring the API remains responsive while complex operations are performed.

## Architecture Diagram

```mermaid
graph TD
    subgraph Client Interaction
        A[HTTP Client]
    end

    subgraph FastAPI Application (src/api)
        B[src/api/api.py]
        C[src/api/dependencies.py]
        D[src/api/models.py]
    end

    subgraph Core Services
        E[src/core/db.py]
        F[Background Task: run_pipeline_in_background]
    end

    A -- Requests --> B;

    B -- Uses --> D;
    B -- Authenticates via --> C;
    C -- Validates JWT --> B;

    B -- Initiates Pipeline (POST /pipeline/run) --> F;
    F -- Persists/Updates State --> E;

    B -- Retrieves Status/Report (GET /pipeline/{id}/status, /report) --> E;

    E -- Stores/Retrieves --> G[Database (SQLite/PostgreSQL)];

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:1px
    style D fill:#ccf,stroke:#333,stroke-width:1px
    style E fill:#bfb,stroke:#333,stroke-width:2px
    style F fill:#fbb,stroke:#333,stroke-width:1px
    style G fill:#fcf,stroke:#333,stroke-width:1px
```

## Data Flow

1.  **Client Request**: An HTTP client sends a request to the FastAPI application (`src/api/api.py`).
2.  **Authentication**: For protected endpoints, `src/api/api.py` invokes the `authenticate_user` dependency (`src/api/dependencies.py`) to validate the JWT provided in the `Authorization` header.
3.  **Validation**: Incoming request bodies are automatically validated against the Pydantic models defined in `src/api/models.py`.
4.  **Pipeline Initiation**: For `POST /pipeline/run` requests, `src/api/api.py` creates a new `PipelineRun` entry in the database via `src/core/db.py` and then schedules `run_pipeline_in_background` as a FastAPI background task.
5.  **Background Processing**: The `run_pipeline_in_background` task simulates the ingestion process, periodically updating the pipeline's status and progress in the database (`src/core/db.py`).
6.  **Status/Report Retrieval**: For `GET /pipeline/{id}/status`, `/report`, or `/visualization` requests, `src/api/api.py` queries the database (`src/core/db.py`) to retrieve the current state or completed report of the specified pipeline run.
7.  **Response**: The API constructs a response using the appropriate Pydantic model (`src/api/models.py`) and sends it back to the client.