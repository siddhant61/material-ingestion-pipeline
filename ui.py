#!/usr/bin/env python3
"""
Material Ingestion Pipeline - Streamlit UI

Web-based dashboard for the Material Ingestion Pipeline that interacts with the FastAPI backend.

Usage:
    streamlit run ui.py
    
Prerequisites:
    - Start the API server first: uvicorn api:app --reload
    - The API should be running on http://localhost:8000
"""

import streamlit as st
import requests
import time
import uuid
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
MAX_TIMEOUT_MINUTES = 30
POLL_INTERVAL_SECONDS = 5
VISUALIZATION_HEIGHT = 800

# Page configuration
st.set_page_config(
    page_title="Material Ingestion Pipeline",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("📚 Material Ingestion Pipeline")
st.markdown("---")

# Description
st.markdown("""
Welcome to the Material Ingestion Pipeline dashboard! This interface allows you to:
- Start new pipeline runs on educational content
- Monitor pipeline execution status in real-time
- View interactive knowledge graph visualizations
- Download pipeline reports

**Prerequisites:** Make sure the API server is running on `http://localhost:8000`
""")

st.markdown("---")

# ================================================================================
# Sidebar - API Health Check
# ================================================================================

with st.sidebar:
    st.header("⚙️ System Status")
    
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if health_response.status_code == 200:
            st.success("✓ API Server is running")
            health_data = health_response.json()
            st.caption(f"Version: {health_data.get('version', 'N/A')}")
        else:
            st.error("✗ API Server returned an error")
    except requests.exceptions.RequestException:
        st.error("✗ API Server is not reachable")
        st.caption(f"Cannot connect to {API_BASE_URL}")
        st.caption("Please start the API server first:")
        st.code("uvicorn api:app --reload", language="bash")
    
    st.markdown("---")
    st.header("📖 Quick Guide")
    st.markdown("""
    1. Enter input and output directories
    2. Click "Start Pipeline Run"
    3. Wait for processing to complete
    4. View the interactive visualization
    """)

# ================================================================================
# Main Content - Pipeline Configuration
# ================================================================================

st.header("1️⃣ Configure Pipeline Run")

# Input fields for directories
col1, col2 = st.columns(2)

with col1:
    input_dir = st.text_input(
        "📁 Input Directory",
        value="./input/course_material",
        help="Path to the directory containing course materials (course_info, transcripts, slides)"
    )

with col2:
    output_dir_base = st.text_input(
        "📂 Base Output Directory",
        value="./output/runs",
        help="Base directory where pipeline outputs will be saved. A unique run subdirectory will be created."
    )

# Show directory info
if input_dir:
    input_path = Path(input_dir)
    if input_path.exists():
        st.success(f"✓ Input directory exists")
    else:
        st.warning(f"⚠️ Input directory does not exist. It will be created with sample files.")

st.markdown("---")

# ================================================================================
# Start Pipeline Run Button
# ================================================================================

st.header("2️⃣ Execute Pipeline")

if st.button("🚀 Start Pipeline Run", type="primary", use_container_width=True):
    # Generate unique run ID
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    output_dir = f"{output_dir_base}/{run_id}"
    
    st.info(f"🔄 Starting pipeline run: **{run_id}**")
    
    with st.spinner(f"Initializing pipeline run {run_id}..."):
        try:
            # Make POST request to start pipeline
            response = requests.post(
                f"{API_BASE_URL}/run",
                json={
                    "input_dir": input_dir,
                    "output_dir": output_dir
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store run info in session state
                st.session_state.run_id = data["run_id"]
                st.session_state.output_dir = data["output_dir"]
                st.session_state.input_dir = data["input_dir"]
                
                st.success(f"✓ Pipeline run started successfully!")
                st.success(f"Run ID: **{data['run_id']}**")
                st.rerun()
            else:
                st.error(f"Failed to start pipeline: {response.status_code}")
                st.error(response.text)
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to API: {str(e)}")
            st.error("Make sure the API server is running on http://localhost:8000")

# ================================================================================
# Status Polling and Results Display
# ================================================================================

if "run_id" in st.session_state:
    st.markdown("---")
    st.header("3️⃣ Pipeline Status")
    
    # Display run information
    st.info(f"**Run ID:** {st.session_state.run_id}")
    st.info(f"**Input Directory:** {st.session_state.input_dir}")
    st.info(f"**Output Directory:** {st.session_state.output_dir}")
    
    # Create a placeholder for status updates
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    message_placeholder = st.empty()
    
    # Poll for status
    max_polls = (MAX_TIMEOUT_MINUTES * 60) // POLL_INTERVAL_SECONDS  # 30 minutes max
    poll_count = 0
    current_status = None  # Initialize to avoid undefined variable
    
    while poll_count < max_polls:
        try:
            # Get current status
            status_response = requests.get(
                f"{API_BASE_URL}/status/{st.session_state.run_id}",
                timeout=5
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data["status"]
                message = status_data["message"]
                
                # Update progress based on status
                if current_status == "initializing":
                    progress_bar.progress(10)
                    status_placeholder.info(f"⏳ Status: **{current_status.upper()}**")
                    message_placeholder.write(message)
                    
                elif current_status == "running":
                    # Simulate progress (we don't have exact progress from API)
                    progress_value = min(10 + (poll_count * 2), 90)
                    progress_bar.progress(progress_value)
                    status_placeholder.warning(f"⚙️ Status: **{current_status.upper()}**")
                    message_placeholder.write(message)
                    
                elif current_status == "complete":
                    progress_bar.progress(100)
                    status_placeholder.success(f"✅ Status: **{current_status.upper()}**")
                    message_placeholder.write(message)
                    
                    st.markdown("---")
                    st.header("4️⃣ Results")
                    
                    # Get visualization
                    st.subheader("📊 Interactive Knowledge Graph Visualization")
                    
                    try:
                        viz_response = requests.get(
                            f"{API_BASE_URL}/results/{st.session_state.run_id}/visualization",
                            timeout=10
                        )
                        
                        if viz_response.status_code == 200:
                            html_content = viz_response.text
                            st.components.v1.html(html_content, height=VISUALIZATION_HEIGHT, scrolling=True)
                            st.success("✓ Visualization loaded successfully!")
                        else:
                            st.error("Failed to load visualization")
                            st.error(f"Status code: {viz_response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error fetching visualization: {str(e)}")
                    
                    # Provide download link for report
                    st.markdown("---")
                    st.subheader("📥 Download Report")
                    report_url = f"{API_BASE_URL}/results/{st.session_state.run_id}/report"
                    st.markdown(f"[Download Pipeline Report (JSON)]({report_url})")
                    
                    # Option to start a new run
                    if st.button("🔄 Start New Pipeline Run"):
                        # Clear session state
                        del st.session_state.run_id
                        del st.session_state.output_dir
                        del st.session_state.input_dir
                        st.rerun()
                    
                    break  # Exit polling loop
                    
                elif current_status == "error":
                    progress_bar.progress(0)
                    status_placeholder.error(f"❌ Status: **{current_status.upper()}**")
                    message_placeholder.error(message)
                    
                    st.error("Pipeline execution failed. Please check the logs and try again.")
                    
                    # Option to start a new run
                    if st.button("🔄 Try Again with New Run"):
                        # Clear session state
                        del st.session_state.run_id
                        del st.session_state.output_dir
                        del st.session_state.input_dir
                        st.rerun()
                    
                    break  # Exit polling loop
                
            else:
                st.error(f"Error checking status: {status_response.status_code}")
                break
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to API: {str(e)}")
            break
        
        # Wait before next poll
        if current_status in ["initializing", "running"]:
            time.sleep(POLL_INTERVAL_SECONDS)
            poll_count += 1
        else:
            break
    
    if poll_count >= max_polls:
        st.error("Pipeline is taking longer than expected. Please check the API logs.")

# ================================================================================
# Footer
# ================================================================================

st.markdown("---")
st.caption("Material Ingestion Pipeline v1.0.0 | Phase 13 Complete")
