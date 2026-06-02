# API Formalization Plan for `material-ingestion-pipeline`

## 1. Introduction
The `api.py` module currently serves as the primary interface for interacting with the Core Ingestion Pipeline. To achieve the 'ship-product' goal, it's crucial to formalize and standardize this API. This plan outlines the steps to introduce consistency, enhance security, improve performance, and ensure maintainability, directly addressing findings such as the lack of test coverage and unclear dependency edges for API components.

## 2. Core Principles
*   **Consistency**: Predictable endpoint structures, naming, and data formats.
*   **Robustness**: Comprehensive error handling and input validation.
*   **Security**: Strong authentication, authorization, and secure defaults.
*   **Observability**: Clear logging, metrics, and documentation.
*   **Performance**: Efficient handling of requests, especially for long-running operations.

## 3. Key Areas of Formalization

### 3.1. Request and Response Models
*   **Action**: Adopt a data validation library (e.g., Pydantic for Python) to define explicit schema models for all API requests and responses.
    *   **Example**: Refactor `PipelineRunRequest`, `PipelineRunResponse`, `PipelineStatusResponse` (and others like `PipelineVisualizationResponse`, `PipelineReportResponse`) into Pydantic models.
*   **Consistency**: Ensure these Python models align precisely with the `shared-api-contracts.ts` TypeScript interfaces, providing a clear contract for all consumers.
*   **Validation**: Leverage Pydantic's validation capabilities to automatically enforce data types, constraints, and required fields for incoming requests.

### 3.2. Error Handling
*   **Action**: Implement a global exception handler (e.g., using FastAPI's `RequestValidationError` and custom exception handlers) to catch and standardize API errors.
*   **Format**: All error responses must conform to the `ApiError` interface defined in `shared-api-contracts.ts`, including a `code`, `message`, and optional `details`.
*   **Codes**: Define a set of standardized error codes (e.g., `VALIDATION_ERROR`, `UNAUTHORIZED`, `NOT_FOUND`, `INTERNAL_SERVER_ERROR`, `PIPELINE_FAILED`) to provide machine-readable context.
*   **Logging**: Ensure all unhandled exceptions are logged with sufficient detail for debugging.

### 3.3. Authentication and Authorization
*   **Action**: Implement a clear strategy for securing API endpoints.
    *   **Authentication**: For service-to-service communication, implement API Key authentication. For potential future user-facing interactions, consider OAuth2/JWT tokens.
    *   **Integration**: Utilize FastAPI's `Security` dependencies for easy integration of authentication schemes.
*   **Authorization**: Implement role-based access control (RBAC) or similar mechanisms to ensure that authenticated users/services only access resources they are permitted to.
    *   **Example**: Only authorized services can call `start_pipeline_run`, while `get_pipeline_status` might have broader access.

### 3.4. Endpoint Consistency and Design
*   **Action**: Review all existing endpoints (`read_root`, `start_pipeline_run`, `get_pipeline_status`, `get_pipeline_visualization`, `get_pipeline_report`, `health_check`) for consistency.
*   **RESTful Principles**: Align endpoints with RESTful principles where appropriate (e.g., using HTTP methods correctly, consistent resource naming).
    *   `POST /pipelines/runs` for `start_pipeline_run`
    *   `GET /pipelines/runs/{run_id}/status` for `get_pipeline_status`
    *   `GET /health` for `health_check`
*   **Versioning**: Consider API versioning (e.g., `/v1/pipelines`) to manage future changes without breaking existing clients.

### 3.5. Performance Considerations
*   **Asynchronous Operations**: Ensure that long-running tasks, like `run_pipeline_in_background`, are truly non-blocking for the API endpoint. The API should return a `PipelineRunResponse` quickly with a `runId`, and the actual pipeline execution should happen in a separate worker process or thread.
*   **Database Optimization**: If API endpoints interact with a database, ensure queries are optimized and indexed.
*   **Caching**: Implement caching strategies for frequently accessed, immutable data (e.g., `get_pipeline_visualization` if the visualization is static for a given run).

### 3.6. Security Best Practices
*   **Input Validation**: Beyond Pydantic, sanitize all user-provided input to prevent injection attacks.
*   **Rate Limiting**: Implement rate limiting to protect against abuse and denial-of-service attacks.
*   **CORS**: Configure Cross-Origin Resource Sharing (CORS) policies explicitly.
*   **Secure Headers**: Ensure appropriate HTTP security headers are set (e.g., `X-Content-Type-Options`, `X-Frame-Options`).

### 3.7. Documentation
*   **Action**: Integrate OpenAPI (Swagger UI) generation directly from the API code (e.g., using FastAPI's built-in capabilities).
*   **Clarity**: Ensure all endpoints, parameters, request bodies, and responses are clearly documented within the code, which will then be reflected in the OpenAPI specification.

### 3.8. Testing
*   **Action**: Address the 'No test file for: api.py' tech debt by implementing comprehensive tests.
*   **Unit Tests**: Write unit tests for individual API functions and data models to ensure their correctness.
*   **Integration Tests**: Develop integration tests that simulate client requests to the API endpoints, verifying correct request/response handling, error scenarios, and interaction with the Core Ingestion Pipeline (mocking external dependencies as needed).
*   **Security Tests**: Include tests for authentication, authorization, and input validation to ensure security mechanisms are functioning as expected.

## 4. Implementation Steps (High-Level)
1.  **Define Pydantic Models**: Create/refactor Pydantic models for all API requests and responses, aligning with `shared-api-contracts.ts`.
2.  **Implement Global Error Handling**: Set up a centralized error handling mechanism.
3.  **Integrate Authentication/Authorization**: Choose and implement the chosen security strategy.
4.  **Refactor Endpoints**: Update `api.py` endpoints to use new models, error handling, and security.
5.  **Add Tests**: Develop comprehensive unit and integration tests for `api.py`.
6.  **Configure OpenAPI**: Ensure automatic generation of API documentation.
7.  **Review and Deploy**: Conduct a thorough review and plan for phased deployment, communicating any breaking changes.

This plan provides a roadmap to elevate the `material-ingestion-pipeline` API to a production-ready standard, enhancing its reliability, security, and usability.