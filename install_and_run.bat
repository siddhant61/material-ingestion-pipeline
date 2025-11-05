@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Running material ingestion pipeline...
python cli.py run-pipeline --input-dir ./input --output-dir ./output
echo Pipeline execution complete.

echo Knowledge graph visualizations can be found in the output/visualizations directory.
echo Open the interactive visualization (output/visualizations/knowledge_graph_interactive.html) in a web browser to explore the knowledge graph.

pause