@echo off
REM Start the Material Ingestion Pipeline UI (Streamlit)

echo Starting Material Ingestion Pipeline UI...
echo UI will be available at http://localhost:8501
echo.
echo IMPORTANT: Make sure the API server is running first!
echo To start the API: start_api.bat (in another terminal)
echo.
echo Press Ctrl+C to stop the UI
echo.

streamlit run ui.py
