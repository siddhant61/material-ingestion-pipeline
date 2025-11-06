# Material Ingestion Pipeline API - Usage Guide

## Overview

The Material Ingestion Pipeline API is a FastAPI-based web service that exposes the complete pipeline over HTTP. This API serves as the backend for the future User Interface and allows for programmatic pipeline execution and monitoring.

## Starting the Server

### Using uvicorn directly:

```bash
uvicorn api:app --reload
```

This will start the server on `http://localhost:8000` with auto-reload enabled for development.

### For production:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using the Python script:

```bash
python api.py
```

## API Endpoints

### 1. Root Endpoint

**GET /**

Returns API information and available endpoints.

```bash
curl http://localhost:8000/
```

Response:
```json
{
  "name": "Material Ingestion Pipeline API",
  "version": "1.0.0",
  "description": "API for running the Material Ingestion Pipeline on educational content",
  "endpoints": {
    "POST /run": "Start a new pipeline run",
    "GET /status/{run_id}": "Check the status of a pipeline run",
    "GET /results/{run_id}/visualization": "Get the interactive visualization HTML",
    "GET /results/{run_id}/report": "Get the pipeline execution report"
  }
}
```

### 2. Start Pipeline Run

**POST /run**

Starts a new pipeline run asynchronously. The pipeline runs in the background to avoid HTTP timeouts.

**Request Body:**
```json
{
  "input_dir": "./my_course/",
  "output_dir": "./my_output/"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/run \
     -H "Content-Type: application/json" \
     -d '{"input_dir": "./my_course/", "output_dir": "./my_output/"}'
```

**Response:**
```json
{
  "run_id": "run_20231106_143022_a1b2c3d4",
  "message": "Pipeline run started. Use the run_id to check status.",
  "input_dir": "./my_course/",
  "output_dir": "./my_output/"
}
```

**Note:** Save the `run_id` to check the status and retrieve results.

### 3. Check Pipeline Status

**GET /status/{run_id}**

Checks the current status of a pipeline run.

**Possible Statuses:**
- `initializing`: Pipeline is being set up
- `running`: Pipeline is currently processing
- `complete`: Pipeline has finished successfully
- `error`: Pipeline encountered an error

**Example:**
```bash
curl http://localhost:8000/status/run_20231106_143022_a1b2c3d4
```

**Response:**
```json
{
  "run_id": "run_20231106_143022_a1b2c3d4",
  "status": "running",
  "message": "Pipeline is processing...",
  "output_dir": "./my_output/"
}
```

### 4. Get Interactive Visualization

**GET /results/{run_id}/visualization**

Returns the interactive knowledge graph visualization as HTML.

**Example:**
```bash
curl http://localhost:8000/results/run_20231106_143022_a1b2c3d4/visualization \
     -o visualization.html
```

Then open `visualization.html` in a web browser to view the interactive knowledge graph.

**Response:**
- Returns HTML content directly (can be opened in a browser)
- HTTP 202: Pipeline still running, visualization not yet available
- HTTP 404: Visualization not found or pipeline failed

### 5. Get Pipeline Report

**GET /results/{run_id}/report**

Returns the detailed pipeline execution report as JSON.

**Example:**
```bash
curl http://localhost:8000/results/run_20231106_143022_a1b2c3d4/report \
     -o report.json
```

**Response:**
- Returns JSON file with complete pipeline execution details
- HTTP 202: Pipeline still running, report not yet available
- HTTP 404: Report not found or pipeline failed

### 6. Health Check

**GET /health**

Returns the health status of the API.

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Material Ingestion Pipeline API",
  "version": "1.0.0"
}
```

## Complete Workflow Example

### 1. Start a pipeline run:

```bash
curl -X POST http://localhost:8000/run \
     -H "Content-Type: application/json" \
     -d '{"input_dir": "./course_data/", "output_dir": "./results/"}' \
     | jq .
```

Save the `run_id` from the response.

### 2. Check the status periodically:

```bash
# Replace RUN_ID with your actual run_id
RUN_ID="run_20231106_143022_a1b2c3d4"

while true; do
    STATUS=$(curl -s http://localhost:8000/status/$RUN_ID | jq -r .status)
    echo "Status: $STATUS"
    
    if [ "$STATUS" = "complete" ] || [ "$STATUS" = "error" ]; then
        break
    fi
    
    sleep 10
done
```

### 3. Download the visualization:

```bash
curl http://localhost:8000/results/$RUN_ID/visualization -o visualization.html
```

### 4. Download the report:

```bash
curl http://localhost:8000/results/$RUN_ID/report -o report.json
```

## Python Client Example

```python
import requests
import time
import json

# API base URL
BASE_URL = "http://localhost:8000"

# 1. Start a pipeline run
response = requests.post(
    f"{BASE_URL}/run",
    json={
        "input_dir": "./my_course/",
        "output_dir": "./my_output/"
    }
)

run_data = response.json()
run_id = run_data["run_id"]
print(f"Pipeline run started: {run_id}")

# 2. Poll for completion
while True:
    status_response = requests.get(f"{BASE_URL}/status/{run_id}")
    status_data = status_response.json()
    status = status_data["status"]
    
    print(f"Status: {status} - {status_data['message']}")
    
    if status in ["complete", "error"]:
        break
    
    time.sleep(10)

# 3. Get results if successful
if status == "complete":
    # Get visualization
    viz_response = requests.get(f"{BASE_URL}/results/{run_id}/visualization")
    with open("visualization.html", "w") as f:
        f.write(viz_response.text)
    print("Visualization saved to visualization.html")
    
    # Get report
    report_response = requests.get(f"{BASE_URL}/results/{run_id}/report")
    with open("report.json", "w") as f:
        json.dump(report_response.json(), f, indent=2)
    print("Report saved to report.json")
else:
    print(f"Pipeline failed: {status_data['message']}")
```

## Architecture

### Background Task Processing

The API uses FastAPI's `BackgroundTasks` to run the pipeline asynchronously. This is crucial because:

1. **Avoids Timeouts**: Pipeline execution can take several minutes, which would timeout a synchronous HTTP request.
2. **Non-Blocking**: The API immediately returns a `run_id`, allowing clients to check status periodically.
3. **Scalable**: Multiple pipeline runs can be executed concurrently.

### Pipeline Execution Flow

1. **Request Received**: Client sends POST request to `/run` with directories
2. **Run ID Generated**: Unique timestamp-based UUID is created
3. **Background Task Queued**: Pipeline execution is added to background tasks
4. **Immediate Response**: API returns `run_id` to client
5. **Pipeline Runs**: Complete 9-stage pipeline executes in background
6. **Status Updates**: Client can poll `/status/{run_id}` to check progress
7. **Results Available**: Once complete, visualization and report can be downloaded

### Directory Structure

For each pipeline run, the following structure is created:

```
output_dir/
├── course_context/
├── transcripts/
├── slides/
├── fused_context/
├── knowledge_graph/
│   └── knowledge_graph.json
├── visualizations/
│   └── knowledge_graph_interactive.html
├── embeddings/
└── pipeline_report.json
```

## Error Handling

### Common Error Responses

**404 Not Found:**
- Run ID doesn't exist
- Results not available yet

**202 Accepted:**
- Pipeline is still running
- Results are being generated

**500 Internal Server Error:**
- Pipeline execution failed
- Check the error message in the status endpoint

## Integration with UI

This API is designed to be consumed by a frontend UI. The typical integration flow:

1. **UI Form**: User enters input/output directories
2. **API Call**: UI calls `/run` endpoint
3. **Progress Indicator**: UI polls `/status/{run_id}` and shows progress
4. **Results Display**: Once complete, UI embeds visualization or provides download links

## Security Considerations

For production deployments, consider:

1. **Authentication**: Add API key or OAuth authentication
2. **Rate Limiting**: Prevent abuse with rate limiting
3. **Input Validation**: Validate and sanitize directory paths
4. **CORS**: Configure CORS for web UI access
5. **HTTPS**: Use HTTPS in production

## Next Steps

1. Build a frontend UI to consume this API
2. Add authentication and authorization
3. Implement WebSocket support for real-time progress updates
4. Add endpoints for listing all runs and cleaning up old runs
5. Implement run cancellation functionality
