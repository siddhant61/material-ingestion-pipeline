# Material Ingestion Pipeline API Documentation

This document provides comprehensive API documentation for the Material Ingestion Pipeline, detailing available endpoints, data models, authentication, and usage examples.

## 1. Introduction

The Material Ingestion Pipeline API provides programmatic access to initiate, monitor, and retrieve results from the material ingestion process. It is designed to be a robust and scalable interface for integrating with external systems that need to process various forms of data.

## 2. Base URL

The base URL for the API is typically `http://localhost:8000` during local development. In a deployed environment, this will be the domain where the API is hosted (e.g., `https://api.yourdomain.com`).

## 3. Authentication

As per security recommendations, all sensitive API endpoints **should be protected** using an API Key mechanism. Clients are expected to include an API key in the `X-API-Key` header for authenticated requests.

**Example Header:**

```
X-API-Key: your_super_secret_api_key
```

Requests without a valid API key or with an invalid key will receive a `401 Unauthorized` or `403 Forbidden` response.

## 4. Endpoints

### 4.1. Root Endpoint

*   **GET /**
*   **Description**: A simple root endpoint to confirm the API is running.
*   **Response**: `200 OK`

    ```json
    {
      "message": "Material Ingestion Pipeline API"
    }
    ```

*   **Example Request (curl)**:

    ```bash
    curl -X GET "http://localhost:8000/"
    ```

### 4.2. Health Check

*   **GET /health**
*   **Description**: Provides a detailed health status of the API, including its current operational state and a timestamp.
*   **Response**: `200 OK`

    ```json
    {
      "status": "healthy",
      "timestamp": "2023-10-27T10:00:00.123456+00:00"
    }
    ```

*   **Example Request (curl)**:

    ```bash
    curl -X GET "http://localhost:8000/health"
    ```

### 4.3. Start Pipeline Run

*   **POST /pipeline/run**
*   **Description**: Initiates a new material ingestion pipeline run asynchronously. The API returns a `runId` immediately, and the pipeline execution proceeds in the background.
*   **Request Body**: `application/json` - See `PipelineRunRequest` model below.
    *   `pipelineConfigId` (string, required): Unique identifier for the pipeline configuration to use.
    *   `inputData` (object, required): The raw input data for the pipeline (e.g., document content, URLs, file paths).
    *   `callbackUrl` (string, optional): An optional URL where the API can send status updates or webhooks during the pipeline run.
    *   `metadata` (object, optional): Optional additional metadata to associate with the run.
*   **Response**: `202 Accepted` - See `PipelineRunResponse` model below.

*   **Example Request (curl)**:

    ```bash
    curl -X POST "http://localhost:8000/pipeline/run" \
         -H "Content-Type: application/json" \
         -H "X-API-Key: your_super_secret_api_key" \
         -d '{ \
               "pipelineConfigId": "my-document-processing-config", \
               "inputData": { \
                 "document_url": "https://example.com/document.pdf", \
                 "source_system": "CRM"
               }, \
               "callbackUrl": "https://your-app.com/webhook/pipeline-status", \
               "metadata": { \
                 "user_id": "user-123", \
                 "project": "project-alpha"
               } \
             }'
    ```

*   **Example Response (202 Accepted)**:

    ```json
    {
      "runId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "PENDING",
      "message": "Pipeline run initiated successfully",
      "submittedAt": "2023-10-27T10:05:30.456789+00:00"
    }
    ```

### 4.4. Get Pipeline Status

*   **GET /pipeline/{run_id}/status**
*   **Description**: Retrieves the current detailed status of an ongoing or completed pipeline run.
*   **Path Parameters**:
    *   `run_id` (string, required): The unique identifier for the pipeline run.
*   **Response**: `200 OK` - See `PipelineStatusResponse` model below.
*   **Errors**: `404 Not Found` if the `run_id` does not exist.

*   **Example Request (curl)**:

    ```bash
    curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/status" \
         -H "X-API-Key: your_super_secret_api_key"
    ```

*   **Example Response (200 OK - Running)**:

    ```json
    {
      "runId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "RUNNING",
      "progress": 50.5,
      "currentStage": "Embedding Generation",
      "reportUrl": null,
      "visualizationUrl": null,
      "error": null,
      "lastUpdatedAt": "2023-10-27T10:06:15.987654+00:00"
    }
    ```

*   **Example Response (200 OK - Completed)**:

    ```json
    {
      "runId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "COMPLETED",
      "progress": 100.0,
      "currentStage": "Finalizing Report",
      "reportUrl": "https://example.com/reports/a1b2c3d4.json",
      "visualizationUrl": "https://example.com/visuals/a1b2c3d4.html",
      "error": null,
      "lastUpdatedAt": "2023-10-27T10:07:00.000000+00:00"
    }
    ```

*   **Example Response (200 OK - Failed)**:

    ```json
    {
      "runId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "FAILED",
      "progress": 75.0,
      "currentStage": "Data Processing",
      "reportUrl": null,
      "visualizationUrl": null,
      "error": {
        "code": "DATA_VALIDATION_ERROR",
        "message": "Input document failed schema validation.",
        "details": {
          "field": "document_content",
          "reason": "Missing required field"
        }
      },
      "lastUpdatedAt": "2023-10-27T10:06:45.111222+00:00"
    }
    ```

### 4.5. Get Pipeline Report

*   **GET /pipeline/{run_id}/report**
*   **Description**: Retrieves the final report for a completed pipeline run. If the pipeline is not yet completed or failed, this endpoint may return an error or indicate that the report is not available. The actual content or a redirect to the `reportUrl` from the status endpoint is returned.
*   **Path Parameters**:
    *   `run_id` (string, required): The unique identifier for the pipeline run.
*   **Response**: `200 OK` (JSON report content or redirect), `404 Not Found` (if run_id invalid), `409 Conflict` (if report not ready).

*   **Example Request (curl)**:

    ```bash
    curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/report" \
         -H "X-API-Key: your_super_secret_api_key"
    ```

*   **Example Response (200 OK - Conceptual JSON)**:

    ```json
    {
      "runId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "status": "COMPLETED",
      "summary": "Document processed successfully. 15 entities extracted.",
      "extractedEntities": [
        {"type": "PERSON", "value": "John Doe"},
        {"type": "ORGANIZATION", "value": "Acme Corp"}
      ],
      "processingLogs": "..."
    }
    ```

### 4.6. Get Pipeline Visualization

*   **GET /pipeline/{run_id}/visualization**
*   **Description**: Retrieves visualization data or a link to a visualization for a completed pipeline run. Similar to the report, this may return an error if the visualization is not ready.
*   **Path Parameters**:
    *   `run_id` (string, required): The unique identifier for the pipeline run.
*   **Response**: `200 OK` (JSON visualization data or redirect), `404 Not Found` (if run_id invalid), `409 Conflict` (if visualization not ready).

*   **Example Request (curl)**:

    ```bash
    curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/visualization" \
         -H "X-API-Key: your_super_secret_api_key"
    ```

*   **Example Response (200 OK - Conceptual JSON or Redirect)**:

    ```json
    {
      "runId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "visualizationType": "mermaid-flowchart",
      "data": "graph TD; A[Start] --> B{Process}; B --> C[End];"
    }
    ```

## 5. Data Models

### 5.1. `PipelineRunRequest`

Represents the payload for initiating a new pipeline run.

```json
{
  "pipelineConfigId": "string",
  "inputData": {},
  "callbackUrl": "string | null",
  "metadata": "object | null"
}
```

### 5.2. `PipelineErrorDetail`

Provides detailed information about an error that occurred during a pipeline run.

```json
{
  "code": "string",
  "message": "string",
  "details": "object | null"
}
```

### 5.3. `PipelineRunResponse`

Represents the immediate response after successfully initiating a pipeline run.

```json
{
  "runId": "string",
  "status": "PENDING | RUNNING | COMPLETED | FAILED | CANCELLED",
  "message": "string",
  "submittedAt": "datetime"
}
```

### 5.4. `PipelineStatusResponse`

Represents the detailed status of an ongoing or completed pipeline run.

```json
{
  "runId": "string",
  "status": "PENDING | RUNNING | COMPLETED | FAILED | CANCELLED",
  "progress": "float",
  "currentStage": "string | null",
  "reportUrl": "string | null",
  "visualizationUrl": "string | null",
  "error": "PipelineErrorDetail | null",
  "lastUpdatedAt": "datetime"
}
```

## 6. Error Handling

API errors are typically returned with appropriate HTTP status codes (e.g., `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `500 Internal Server Error`). For pipeline-specific failures, the `PipelineStatusResponse` will include an `error` field containing a `PipelineErrorDetail` object with a `code`, `message`, and optional `details` for more granular information.

## 7. OpenAPI / Swagger UI

This API is built using FastAPI, which automatically generates OpenAPI specification and provides an interactive Swagger UI. You can access these at:

*   **OpenAPI JSON**: `/openapi.json`
*   **Swagger UI**: `/docs`
*   **ReDoc**: `/redoc`

These interfaces provide a live, interactive way to explore the API, test endpoints, and view detailed schema definitions.