# Material Ingestion Pipeline API - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Layer                           │
│                                                                 │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐              │
│  │  Web UI    │  │  CLI Tool  │  │  Python     │              │
│  │  (Future)  │  │  (curl)    │  │  Client     │              │
│  └────────────┘  └────────────┘  └─────────────┘              │
│         │              │                 │                      │
└─────────┼──────────────┼─────────────────┼──────────────────────┘
          │              │                 │
          └──────────────┴─────────────────┘
                         │
                         ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server (api.py)                    │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                    API Endpoints                        │   │
│  │  • POST /run                                           │   │
│  │  • GET /status/{run_id}                               │   │
│  │  • GET /results/{run_id}/visualization                │   │
│  │  • GET /results/{run_id}/report                       │   │
│  │  • GET /health                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              Background Task Queue                      │   │
│  │         (FastAPI BackgroundTasks)                      │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────┐        │   │
│  │  │   run_pipeline_in_background()           │        │   │
│  │  │                                          │        │   │
│  │  │   • Update settings paths                │        │   │
│  │  │   • Setup sample files                   │        │   │
│  │  │   • Initialize pipeline                  │        │   │
│  │  │   • Register 11 agents                   │        │   │
│  │  │   • Execute pipeline                     │        │   │
│  │  │   • Update run status                    │        │   │
│  │  └──────────────────────────────────────────┘        │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Material Ingestion Pipeline Core                   │
│                (MaterialIngestionPipeline)                      │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                    Pipeline Stages                      │   │
│  │                                                        │   │
│  │  1. ContextAgent          → Extract course context    │   │
│  │  2. TranscriptAgent       → Process transcripts       │   │
│  │  3. SlideAgent            → Process slides            │   │
│  │  4. VisionAgent           → Visual analysis           │   │
│  │  5. FusionAgent           → Fuse contexts             │   │
│  │  6. SupervisionOrchestrator → Supervise content      │   │
│  │  7. KnowledgeGraphAgent   → Build knowledge graph    │   │
│  │  8. VisualizationAgent    → Create visualizations    │   │
│  │  9. EmbeddingAgent        → Generate embeddings      │   │
│  └────────────────────────────────────────────────────────┘   │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    File System (Output)                         │
│                                                                 │
│  output_dir/                                                   │
│  ├── course_context/                                          │
│  ├── transcripts/                                             │
│  ├── slides/                                                  │
│  ├── fused_context/                                           │
│  ├── knowledge_graph/                                         │
│  │   └── knowledge_graph.json ← Status check                │
│  ├── visualizations/                                          │
│  │   └── knowledge_graph_interactive.html ← Download        │
│  ├── embeddings/                                             │
│  └── pipeline_report.json ← Status check & Download         │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Starting a Pipeline Run

```
Client                 API Server              Background Task
  │                       │                          │
  │  POST /run           │                          │
  │  {input_dir,         │                          │
  │   output_dir}        │                          │
  ├─────────────────────>│                          │
  │                      │                          │
  │                      │ Generate run_id         │
  │                      │ Store in active_runs    │
  │                      │                          │
  │                      │ Queue background task   │
  │                      ├────────────────────────>│
  │                      │                          │
  │  200 OK              │                          │ Start execution
  │  {run_id, message}   │                          │
  │<─────────────────────┤                          │
  │                      │                          │ Run 9 stages
  │                      │                          │
  │                      │                          │ Update status
  │                      │                          │
```

### 2. Checking Status

```
Client                 API Server              File System
  │                       │                          │
  │  GET /status/{id}    │                          │
  ├─────────────────────>│                          │
  │                      │                          │
  │                      │ Check active_runs        │
  │                      │                          │
  │                      │ Verify output files      │
  │                      ├────────────────────────>│
  │                      │                          │
  │                      │<─────────────────────────┤
  │                      │                          │
  │  200 OK              │                          │
  │  {status, message}   │                          │
  │<─────────────────────┤                          │
  │                      │                          │
```

### 3. Retrieving Results

```
Client                 API Server              File System
  │                       │                          │
  │  GET /results/{id}/  │                          │
  │  visualization       │                          │
  ├─────────────────────>│                          │
  │                      │                          │
  │                      │ Check if file exists     │
  │                      ├────────────────────────>│
  │                      │                          │
  │                      │ Read HTML file          │
  │                      │<─────────────────────────┤
  │                      │                          │
  │  200 OK              │                          │
  │  <HTML content>      │                          │
  │<─────────────────────┤                          │
  │                      │                          │
```

## Data Models

### PipelineRunRequest
```json
{
  "input_dir": "string",
  "output_dir": "string"
}
```

### PipelineRunResponse
```json
{
  "run_id": "run_20231106_143022_a1b2c3d4",
  "message": "Pipeline run started. Use the run_id to check status.",
  "input_dir": "./my_course/",
  "output_dir": "./my_output/"
}
```

### PipelineStatusResponse
```json
{
  "run_id": "run_20231106_143022_a1b2c3d4",
  "status": "running",  // initializing | running | complete | error
  "message": "Pipeline is processing...",
  "output_dir": "./my_output/"
}
```

## State Management

### Active Runs Dictionary

```python
active_runs = {
    "run_20231106_143022_a1b2c3d4": {
        "run_id": "run_20231106_143022_a1b2c3d4",
        "input_dir": "./my_course/",
        "output_dir": "./my_output/",
        "status": "running",  // initializing | running | complete | error
        "message": "Pipeline is processing...",
        "started_at": "2023-11-06T14:30:22.123456"
    }
}
```

### Status Transitions

```
initializing → running → complete
                      ↘ error
```

- **initializing**: Run has been queued but not yet started
- **running**: Pipeline is actively processing
- **complete**: All stages completed successfully
- **error**: Pipeline encountered an error

## Concurrency Model

### Multiple Concurrent Runs

The API supports multiple concurrent pipeline runs:

```
Run 1: input_dir_1 → output_dir_1  [Status: running]
Run 2: input_dir_2 → output_dir_2  [Status: complete]
Run 3: input_dir_3 → output_dir_3  [Status: running]
```

Each run:
- Has a unique run_id
- Operates on independent directories
- Runs in its own background task
- Maintains separate status tracking

### Thread Safety

- FastAPI handles concurrent requests safely
- Each background task runs independently
- File system operations are isolated by directory
- No shared state between runs (except active_runs dict)

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful operation
- **202 Accepted**: Request accepted, processing in progress
- **404 Not Found**: Run ID or resource not found
- **500 Internal Server Error**: Pipeline execution failed

### Error Response Format

```json
{
  "detail": "Pipeline run run_12345 not found"
}
```

## Security Considerations

### Current Implementation

- No authentication (development mode)
- No rate limiting
- No input sanitization
- Direct file system access

### Production Recommendations

1. **Authentication**: Add API key or OAuth
2. **Authorization**: Role-based access control
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Sanitize directory paths
5. **CORS**: Configure for web UI
6. **HTTPS**: Use TLS in production
7. **File System**: Restrict directory access
8. **Secrets**: Use environment variables for sensitive data

## Scalability Considerations

### Current Limitations

- In-memory state (active_runs dictionary)
- Single server instance
- No distributed processing
- No database persistence

### Future Enhancements

1. **Database**: Persist run state to database
2. **Message Queue**: Use Celery/RabbitMQ for task queue
3. **Load Balancer**: Support multiple API instances
4. **Caching**: Cache results for repeated requests
5. **WebSockets**: Real-time progress updates
6. **Pagination**: List all runs with pagination
7. **Cleanup**: Auto-delete old runs after retention period

## Monitoring and Observability

### Logging

- All operations logged with timestamps
- Run ID included in log messages
- Error tracebacks captured

### Metrics (Recommended)

- Total runs started
- Active concurrent runs
- Success/failure rates
- Average execution time
- API response times

### Health Check

```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "healthy",
  "service": "Material Ingestion Pipeline API",
  "version": "1.0.0"
}
```

## Integration with Future UI

### Expected UI Flow

1. **Dashboard**: Show active and completed runs
2. **Start Run Form**: Input/output directory selection
3. **Progress Page**: Real-time status updates
4. **Results Page**: View/download visualization and report
5. **History**: List all past runs with filtering

### UI → API Communication

- **RESTful**: Standard HTTP requests
- **Polling**: Check status every N seconds
- **Downloads**: Direct file serving via API
- **Errors**: Clear error messages for user display

## Development Workflow

### Starting the Server

```bash
# Development mode with auto-reload
uvicorn api:app --reload

# Production mode
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

```bash
# Run structure tests
python test_api.py

# Manual testing with curl
curl http://localhost:8000/health

# Python client example
python example_api_client.py
```

### Interactive Documentation

FastAPI provides automatic interactive documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
