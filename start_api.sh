#!/bin/bash
# Start the Material Ingestion Pipeline API server

echo "Starting Material Ingestion Pipeline API..."
echo "API will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn api:app --reload --host 0.0.0.0 --port 8000
