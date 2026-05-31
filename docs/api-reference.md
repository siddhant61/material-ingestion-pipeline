# Material Ingestion Pipeline API Reference

This document provides a comprehensive reference for the Material Ingestion Pipeline API, designed for managing and monitoring the ingestion process. The API is built using FastAPI, uses Pydantic for data validation, and persists pipeline states using SQLAlchemy.

## Base URL

All API endpoints are prefixed with the base URL. When running locally with `uvicorn`, this is typically:

`http://localhost:8000`

## Authentication

All protected endpoints require JWT (JSON Web Token) based authentication. A token must be provided in the `Authorization` header using the `Bearer` scheme.

**Header Example:**

`Authorization: Bearer <your_jwt_token>`

### Development/Testing Token

For local development and testing, the `src/api/dependencies.py` module is configured to accept a simple `Bearer valid-token`. In a production environment, this token would be a securely generated JWT signed with a secret key.

### JWT Secret Key

The JWT secret key is loaded from the `JWT_SECRET_KEY` environment variable. It is **critical** to set a strong, unique secret key in production environments. For local testing, a fallback `super-secret-key-not-for-production` is used, but this should never be used in production.

## Error Handling

The API follows standard HTTP status codes for error reporting and returns a consistent `ErrorResponse` model:

| Status Code | Description                               | ErrorResponse Example                               |
| :---------- | :---------------------------------------- | :-------------------------------------------------- |
| `401`       | Unauthorized (missing or invalid token)   | `{"detail": "Not authenticated"}`               |
| `404`       | Not Found (e.g., pipeline ID not found)   | `{"detail": "Pipeline run not found"}`          |
| `422`       | Unprocessable Entity (validation error)   | `{"detail": "Field required", "loc": ["body", "material_id"]}` |
| `500`       | Internal Server Error (unexpected issue)  | `{"detail": "Internal server error"}`           |

## API Endpoints

### 1. Health Check

Checks the operational status of the API.

*   **Endpoint**: `GET /health`
*   **Authentication**: None
*   **Response Model**: `HealthCheckResponse`

**Example Request:**

```bash
curl -X GET "http://localhost:8000/health"
```

**Example Response (200 OK):**

```json
{
  "status": "ok",
  "message": "API is running",
  "timestamp": "2023-10-27T10:00:00.000000+00:00",
  "dependencies": {
    "database": "ok"
  }
}
```

### 2. Initiate Pipeline Run

Starts a new material ingestion pipeline run in the background.

*   **Endpoint**: `POST /pipeline/run`
*   **Authentication**: Required
*   **Request Model**: `PipelineRunRequest`
*   **Response Model**: `PipelineRunResponse`
*   **Status Code**: `202 Accepted` (indicates the request has been accepted for processing)

**Example Request:**

```bash
curl -X POST "http://localhost:8000/pipeline/run" \
  -H "Authorization: Bearer valid-token" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "my-unique-material-id-123",
    "config": {
      "source_type": "s3",
      "parser": "json"
    }
  }'
```

**Example Response (202 Accepted):**

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "initiated",
  "message": "Pipeline run initiated successfully"
}
```

### 3. Get Pipeline Status

Retrieves the current status and progress of a specific pipeline run.

*   **Endpoint**: `GET /pipeline/{pipeline_id}/status`
*   **Authentication**: Required
*   **Path Parameters**:
    *   `pipeline_id` (string, UUID): The unique identifier of the pipeline run.
*   **Response Model**: `PipelineStatusResponse`

**Example Request:**

```bash
curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/status" \
  -H "Authorization: Bearer valid-token"
```

**Example Response (200 OK - Running):**

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "running",
  "progress": 50.0,
  "report_url": null,
  "error_details": null
}
```

**Example Response (200 OK - Completed):**

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "completed",
  "progress": 100.0,
  "report_url": "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/report",
  "error_details": null
}
```

### 4. Get Pipeline Visualization

Retrieves visualization data for a specific pipeline run. (Note: This is a placeholder endpoint and currently returns mock data.)

*   **Endpoint**: `GET /pipeline/{pipeline_id}/visualization`
*   **Authentication**: Required
*   **Path Parameters**:
    *   `pipeline_id` (string, UUID): The unique identifier of the pipeline run.
*   **Response Model**: JSON object with `visualization_data` (placeholder)

**Example Request:**

```bash
curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/visualization" \
  -H "Authorization: Bearer valid-token"
```

**Example Response (200 OK):**

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "visualization_data": {
    "nodes": ["step_a", "step_b", "step_c"],
    "edges": [["step_a", "step_b"], ["step_b", "step_c"]]
  }
}
```

### 5. Get Pipeline Report

Retrieves a detailed report for a completed pipeline run.

*   **Endpoint**: `GET /pipeline/{pipeline_id}/report`
*   **Authentication**: Required
*   **Path Parameters**:
    *   `pipeline_id` (string, UUID): The unique identifier of the pipeline run.
*   **Response Model**: `PipelineReportResponse`

**Example Request:**

```bash
curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/report" \
  -H "Authorization: Bearer valid-token"
```

**Example Response (200 OK):**

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "report_data": {
    "processed_items": 100,
    "errors": 2,
    "duration_seconds": 15.5,
    "summary": "Ingestion completed with minor warnings."
  },
  "generated_at": "2023-10-27T10:05:30.123456+00:00"
}
```

## Data Models

The API utilizes Pydantic models for strict data validation and clear contract definition. These models are defined in `src/api/models.py` and align with the shared TypeScript interfaces in `shared/api-contracts/pipeline-management.ts`.

*   `PipelineRunRequest`: Defines the input for initiating a pipeline run.
*   `PipelineRunResponse`: Defines the output after initiating a pipeline run.
*   `PipelineStatusResponse`: Defines the structure for pipeline status retrieval.
*   `PipelineReportResponse`: Defines the structure for detailed pipeline reports.
*   `ErrorResponse`: Standard error response structure.
*   `HealthCheckResponse`: Response structure for the health check endpoint.

Refer to `src/api/models.py` for full schema details, including field types, descriptions, and validation rules.