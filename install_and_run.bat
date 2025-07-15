@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Running pipeline fixes...
python run_component.py fix

echo Running material ingestion pipeline...
python run_enhanced_pipeline.py
echo Pipeline execution complete.

echo Knowledge graph visualizations can be found in the output/visualizations directory.
echo Open the interactive visualization (output/visualizations/knowledge_graph_interactive.html) in a web browser to explore the knowledge graph.

pause 