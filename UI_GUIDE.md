# Material Ingestion Pipeline - User Interface Guide

## Overview

The Material Ingestion Pipeline now includes a complete web-based interface built with Streamlit. This provides an intuitive way to interact with the pipeline without using the command line.

The system consists of two components:
1. **Backend API (FastAPI)** - Handles pipeline execution and processing
2. **Frontend UI (Streamlit)** - Provides the user interface

## Quick Start

### Prerequisites

1. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your `.env` file with required API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

### Starting the Application

You need to run TWO servers in TWO separate terminals:

#### Terminal 1: Start the API Server

**On Linux/Mac:**
```bash
./start_api.sh
```

**On Windows:**
```cmd
start_api.bat
```

**Or manually:**
```bash
uvicorn api:app --reload
```

The API will be available at: `http://localhost:8000`

#### Terminal 2: Start the UI Server

**On Linux/Mac:**
```bash
./start_ui.sh
```

**On Windows:**
```cmd
start_ui.bat
```

**Or manually:**
```bash
streamlit run ui.py
```

The UI will be available at: `http://localhost:8501`

## Using the Interface

### 1. Check System Status

The sidebar shows the API server connection status:
- ✅ **Green**: API server is running and accessible
- ❌ **Red**: API server is not reachable (start it first!)

### 2. Configure Your Pipeline Run

Enter the directories for your course materials:

- **Input Directory**: Path to folder containing your course materials
  - Default: `./input/course_material`
  - Should contain subdirectories: `course_info/`, `transcripts/`, `slides/`
  - If empty, sample files will be automatically created

- **Base Output Directory**: Where results will be saved
  - Default: `./output/runs`
  - A unique run subdirectory will be created for each run

### 3. Start Processing

Click the **"🚀 Start Pipeline Run"** button to begin processing.

The UI will:
1. Generate a unique run ID (e.g., `run_a1b2c3d4`)
2. Send the request to the API server
3. Start monitoring the pipeline status automatically

### 4. Monitor Progress

The UI polls the API every 5 seconds to check status:

- **⏳ Initializing**: Setting up the pipeline
- **⚙️ Running**: Processing your course materials
- **✅ Complete**: Pipeline finished successfully
- **❌ Error**: Something went wrong (check logs)

A progress bar provides visual feedback during execution.

### 5. View Results

When the pipeline completes successfully:

#### Interactive Visualization
- An embedded, interactive knowledge graph appears on the page
- Explore the hierarchical structure of your educational content
- Click nodes to see details
- Zoom and pan to navigate the graph

#### Download Report
- Click the download link to get the full JSON report
- Contains detailed information about all extracted entities and relationships

#### Start New Run
- Click **"🔄 Start New Pipeline Run"** to process different content

## Features

### Real-Time Status Updates
- Automatic polling every 5 seconds
- Visual progress indicators
- Clear status messages

### Error Handling
- Connection errors are clearly displayed
- Pipeline failures show error messages
- Option to retry after errors

### Session Management
- Your current run is remembered during the session
- Refresh the page to check on a running pipeline
- Session state persists across page interactions

## Troubleshooting

### "API Server is not reachable"

**Problem**: The UI cannot connect to the API server.

**Solutions**:
1. Make sure the API server is running in another terminal
2. Verify the API is accessible at `http://localhost:8000`
3. Check that port 8000 is not blocked by a firewall
4. Try restarting the API server

### "Pipeline is taking longer than expected"

**Problem**: The pipeline has been running for more than 30 minutes.

**Solutions**:
1. Check the API server logs for errors
2. Verify your OpenAI API key is valid and has credits
3. Check that input files are not corrupted
4. Large courses may take 10-20 minutes to process

### "Visualization file not found"

**Problem**: The pipeline completed but the visualization is missing.

**Solutions**:
1. Check the output directory for the `visualizations/` folder
2. Look at the pipeline report for errors in the visualization stage
3. Verify all dependencies are installed (`pip install -r requirements.txt`)

### UI won't start / Port already in use

**Problem**: Streamlit won't start because port 8501 is in use.

**Solutions**:
1. Stop any other Streamlit apps running
2. Use a different port:
   ```bash
   streamlit run ui.py --server.port 8502
   ```

## Architecture

### Component Overview

```
┌─────────────────┐         ┌──────────────────┐
│  Streamlit UI   │ ◄────► │  FastAPI Server  │
│  (Frontend)     │  HTTP   │  (Backend)       │
│  Port 8501      │         │  Port 8000       │
└─────────────────┘         └──────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  Pipeline       │
                            │  Orchestrator   │
                            └─────────────────┘
```

### Communication Flow

1. **User Action**: User clicks "Start Pipeline Run" in the UI
2. **HTTP Request**: UI sends POST request to `/run` endpoint
3. **Background Task**: API queues the pipeline for background execution
4. **Immediate Response**: API returns a `run_id` to the UI
5. **Status Polling**: UI periodically checks `/status/{run_id}`
6. **Results Retrieval**: When complete, UI fetches `/results/{run_id}/visualization`

### Why Two Servers?

- **FastAPI (Backend)**: 
  - Handles heavy computational tasks
  - Manages background pipeline execution
  - Provides RESTful API endpoints
  - Can handle multiple simultaneous requests

- **Streamlit (Frontend)**:
  - Provides user-friendly interface
  - Real-time status updates
  - Interactive visualizations
  - Session state management

## Advanced Usage

### Running in Production

For production deployment, use proper WSGI/ASGI servers:

**API Server:**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

**UI Server:**
```bash
streamlit run ui.py --server.port 8501 --server.address 0.0.0.0
```

### Custom API URL

If your API is running on a different host/port, edit `ui.py`:

```python
# Change this line:
API_BASE_URL = "http://localhost:8000"

# To your custom URL:
API_BASE_URL = "http://your-server:8000"
```

### Using with Docker

You can containerize both services:

```dockerfile
# Dockerfile example for the complete stack
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expose both ports
EXPOSE 8000 8501

# Start both servers (use a process manager like supervisord)
CMD ["bash", "-c", "uvicorn api:app --host 0.0.0.0 --port 8000 & streamlit run ui.py --server.port 8501 --server.address 0.0.0.0"]
```

## API Endpoints Reference

The UI uses these API endpoints:

- `GET /health` - Check API server health
- `POST /run` - Start a new pipeline run
- `GET /status/{run_id}` - Check pipeline status
- `GET /results/{run_id}/visualization` - Get interactive visualization HTML
- `GET /results/{run_id}/report` - Download pipeline report JSON

For complete API documentation, visit: `http://localhost:8000/docs` (when API is running)

## Support

For issues, questions, or feature requests:
1. Check the API logs for detailed error messages
2. Review the `QUICKSTART.md` for basic troubleshooting
3. Consult `API_USAGE.md` for API-specific issues
4. Check the main `README.md` for configuration help

## Summary

The Material Ingestion Pipeline UI provides a complete web-based interface for processing educational content. By running both the API and UI servers, you get:

✅ Easy-to-use web interface  
✅ Real-time progress monitoring  
✅ Interactive knowledge graph visualization  
✅ No command-line required  
✅ Professional production-ready architecture  

Start both servers and access the UI at `http://localhost:8501` to begin!
