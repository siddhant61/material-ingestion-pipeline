# Quickstart Guide: Material Ingestion Pipeline API

This guide will help you set up and run the Material Ingestion Pipeline API locally, and demonstrate how to interact with its core functionalities.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.9+**
*   **pip** (Python package installer)
*   **uvicorn** (ASGI server, will be installed via `requirements.txt`)
*   **curl** (for command-line API interaction, or any HTTP client like Postman/Insomnia)

## 1. Setup

Follow these steps to get the API running on your local machine:

### 1.1. Clone the Repository

```bash
git clone https://github.com/siddhant61/material-ingestion-pipeline.git
cd material-ingestion-pipeline
```

### 1.2. Create and Activate a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 1.3. Install Dependencies

Install the required Python packages. If `requirements.txt` doesn't exist, create one with the following content:

**`requirements.txt`:**

```
fastapi==0.104.1
uvicorn[standard]==0.24.0.post1
pydantic==2.4.2
sqlalchemy[asyncio]==2.0.22
aiosqlite==0.19.0
python-jose[cryptography]==3.3.0
```

Then install:

```bash
pip install -r requirements.txt
```

## 2. Configuration

The API uses environment variables for sensitive information and database connection details.

### 2.1. JWT Secret Key

For authentication, the API expects a `JWT_SECRET_KEY`. For local development, you can set a simple one. **Never use this in production.**

```bash
export JWT_SECRET_KEY="my-dev-secret-key"
# On Windows (Command Prompt):
# set JWT_SECRET_KEY="my-dev-secret-key"
# On Windows (PowerShell):
# $env:JWT_SECRET_KEY="my-dev-secret-key"
```

### 2.2. Database URL

The API uses SQLite by default for local development. The database file `test.db` will be created in the project root. You can configure a different database using `DATABASE_URL`.

```bash
# Default (SQLite):
# export DATABASE_URL="sqlite+aiosqlite:///./test.db"
# Example (PostgreSQL - requires 'asyncpg' instead of 'aiosqlite' in requirements.txt):
# export DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname"
```

## 3. Run the API

Start the FastAPI application using Uvicorn. The `--reload` flag is useful for development as it restarts the server on code changes.

```bash
uvicorn src.api.api:app --reload
```

You should see output indicating the server is running, typically on `http://127.0.0.1:8000`.

## 4. Interact with the API

Now that the API is running, you can interact with it using `curl`.

### 4.1. Health Check (GET /health)

This endpoint does not require authentication.

```bash
curl -X GET "http://localhost:8000/health"
```

Expected Output:

```json
{
  "status": "ok",
  "message": "API is running",
  "timestamp": "...",
  "dependencies": {
    "database": "ok"
  }
}
```

### 4.2. Initiate a Pipeline Run (POST /pipeline/run)

This endpoint requires authentication. For development, use `Bearer valid-token`.

```bash
curl -X POST "http://localhost:8000/pipeline/run" \
  -H "Authorization: Bearer valid-token" \
  -H "Content-Type: application/json" \
  -d '{
    "material_id": "my-first-material",
    "config": {
      "processor_version": "1.0",
      "priority": 1
    }
  }'
```

Note the `pipeline_id` from the response; you'll need it for subsequent calls.

Expected Output (example):

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "initiated",
  "message": "Pipeline run initiated successfully"
}
```

### 4.3. Get Pipeline Status (GET /pipeline/{pipeline_id}/status)

Replace `a1b2c3d4-e5f6-7890-1234-567890abcdef` with the actual `pipeline_id` you received.

```bash
curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/status" \
  -H "Authorization: Bearer valid-token"
```

Expected Output (example):

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "pending",
  "progress": 0.0,
  "report_url": null,
  "error_details": null
}
```

Wait a few seconds and try again; the `status` and `progress` fields will update as the background task simulates work.

### 4.4. Get Pipeline Report (GET /pipeline/{pipeline_id}/report)

Once the pipeline status is `completed`, you can fetch its report.

```bash
curl -X GET "http://localhost:8000/pipeline/a1b2c3d4-e5f6-7890-1234-567890abcdef/report" \
  -H "Authorization: Bearer valid-token"
```

Expected Output (example):

```json
{
  "pipeline_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "report_data": {
    "processed_items": 100,
    "errors": 0,
    "duration_seconds": 5.12,
    "summary": "Material processed successfully."
  },
  "generated_at": "2023-10-27T10:05:30.123456+00:00"
}
```

## Next Steps

*   Explore the `src/api/api.py` file to understand the endpoint definitions.
*   Review `src/api/models.py` for the exact data structures.
*   Examine `src/api/dependencies.py` for authentication logic.
*   Look into `src/core/db.py` to see how pipeline states are persisted.