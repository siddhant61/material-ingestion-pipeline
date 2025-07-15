"""
Knowledge Graph Visualization

This module provides functionality for visualizing hierarchical knowledge graphs.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from pathlib import Path
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import colorsys
import uuid
import math
import random
import tempfile
import base64
from io import BytesIO
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

class KnowledgeGraphVisualizer:
    """
    Visualizes hierarchical knowledge graphs generated from educational content.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the KnowledgeGraphVisualizer.
        
        Args:
            config (Dict[str, Any], optional): Configuration for the visualizer
        """
        self.config = config or {}
        self.default_height = self.config.get("height", "800px")
        self.default_width = self.config.get("width", "100%")
        self.bgcolor = self.config.get("bgcolor", "#ffffff")
        self.node_scaling = self.config.get("node_scaling", 1.0)
        
        # Configure visualization settings
        self.hierarchical = self.config.get("hierarchical", True)
        self.physics_enabled = self.config.get("physics_enabled", True)
        self.direction = self.config.get("direction", "UD")  # UD = Up->Down, DU = Down->Up, LR = Left->Right, RL = Right->Left
        
        # Multi-level visualization settings
        self.max_nodes_per_level = self.config.get("max_nodes_per_level", 25)
        self.max_relationships_per_node = self.config.get("max_relationships_per_node", 8)
        self.fibonacci_sequence = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        
        # Set up color schemes
        self._setup_color_schemes()
        
        logger.info("Initialized KnowledgeGraphVisualizer with hierarchical layout support")
    
    def _setup_color_schemes(self):
        """Set up color schemes for different visualizations"""
        # Source-based color mapping (course, transcript, slide, rag, visual_rag, external)
        self.source_colors = {
            "course": "#4285F4",        # Google Blue
            "transcript": "#34A853",    # Google Green
            "slide": "#FBBC05",         # Google Yellow
            "rag": "#EA4335",           # Google Red
            "visual_rag": "#8523D2",    # Purple
            "external": "#555555"       # Dark Gray
        }
        
        # Hierarchy level colors
        self.hierarchy_colors = {
            "root": "#003366",       # Dark blue for root/foundation
            "trunk": "#336699",      # Medium blue for trunk/major theories
            "branch": "#66A3D2",     # Light blue for branches/methods
            "leaf": "#99CC99",       # Green for leaves/applications
            "resource": "#D6A5C9"    # Violet for resources/supporting elements
        }
        
        # Time period colors - creating a gradient from old (warm) to new (cool)
        self.period_colors = {
            "Ancient": "#8B4513",      # Brown
            "Medieval": "#A0522D",     # Sienna
            "Renaissance": "#CD853F",  # Peru
            "Classical": "#DAA520",    # Goldenrod
            "Modern": "#6495ED",       # Cornflower Blue
            "Contemporary": "#4682B4", # Steel Blue
            "Recent": "#1E90FF"        # Dodger Blue
        }
    
    def load_knowledge_graph(self, kg_path: str) -> Dict[str, Any]:
        """
        Load a knowledge graph from a file.
        
        Args:
            kg_path (str): Path to the knowledge graph JSON file
            
        Returns:
            Dict[str, Any]: The loaded knowledge graph
        """
        try:
            with open(kg_path, 'r', encoding='utf-8') as f:
                knowledge_graph = json.load(f)
            logger.info(f"Loaded knowledge graph from {kg_path}")
            return knowledge_graph
        except Exception as e:
            logger.error(f"Error loading knowledge graph: {str(e)}")
            raise
    
    def create_interactive_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        output_dir: Optional[str] = None,
        filename: Optional[str] = None,
        height: Optional[str] = None,
        width: Optional[str] = None,
        title: Optional[str] = None,
        layout_type: str = "standard",
        show_tooltips: bool = True,
        show_edge_labels: bool = True,
        colorize_by: Optional[str] = None,
        multi_level: bool = False
    ) -> str:
        """
        Create an interactive visualization of the knowledge graph.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph to visualize
            output_dir (Optional[str]): Directory to save the visualization (defaults to self.output_dir)
            filename (Optional[str]): Filename for the HTML file (defaults to "knowledge_graph.html")
            height (Optional[str]): Height of the visualization (defaults to "800px")
            width (Optional[str]): Width of the visualization (defaults to "100%")
            title (Optional[str]): Title for the visualization
            layout_type (str): Layout type ("hierarchical", "standard", "radial", "force")
            show_tooltips (bool): Whether to show tooltips
            show_edge_labels (bool): Whether to show edge labels
            colorize_by (Optional[str]): Entity property to use for coloring nodes
            multi_level (bool): Whether to create a multi-level visualization
            
        Returns:
            str: Path to the generated HTML file, or the main overview file in case of multi-level
        """
        if layout_type == "hierarchical":
            self.hierarchical = True
        else:
            self.hierarchical = False
        
        # Set output directory and filename
        if output_dir is None:
            output_dir = self.output_dir
        
        if filename is None:
            filename = "knowledge_graph.html"
        
        # Create multi-level visualization if requested
        if multi_level:
            output_files = self.create_multi_level_visualization(
                knowledge_graph=knowledge_graph,
                output_dir=os.path.join(output_dir, "multi_level"),
                height=height,
                width=width
            )
            # Return the overview file path
            return output_files.get("overview", "")
        
        # Create a standard single-file visualization
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, filename)
        
        # Create a NetworkX graph from the knowledge graph
        G = self._create_networkx_graph(knowledge_graph)
        
        # Create a Pyvis network
        net = Network(
            height=height or self.default_height,
            width=width or self.default_width,
            bgcolor="#FFFFFF",
            font_color="#000000",
            directed=True,
            notebook=False
        )
        
        # Add the NetworkX graph to the Pyvis network
        net.from_nx(G)
        
        # Apply layout-specific options
        if self.hierarchical:
            self._set_hierarchical_options(net)
        else:
            # Set physics options for other layouts
            physics_options = self._get_layout_options(layout_type)
            net.set_options(physics_options)
        
        # Apply node and edge styling
        self._style_nodes_and_edges(net, knowledge_graph)
        
        # Add a title if provided
        if title:
            title_html = f"<h1 style='text-align:center; color:#003366;'>{title}</h1>"
            net.html = title_html + net.html
        
        # Save to HTML file
        try:
            net.save_graph(output_file)
            logger.info(f"Saved visualization to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error saving visualization: {str(e)}")
            raise
    
    def _find_entity_by_id(self, knowledge_graph: Dict[str, Any], entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an entity in the knowledge graph by its ID.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph
            entity_id (str): The ID of the entity to find
            
        Returns:
            Optional[Dict[str, Any]]: The entity or None if not found
        """
        for entity in knowledge_graph.get("entities", []):
            if entity.get("id") == entity_id:
                return entity
        return None
    
    def _append_legend_to_html(self, html_file: str, legend_html: str) -> None:
        """
        Append the legend HTML to an existing HTML file.
        
        Args:
            html_file (str): Path to the HTML file
            legend_html (str): HTML content for the legend
        """
        self._append_html_to_file(html_file, legend_html, "legend")
    
    def _add_fallback_relationships(self, G: nx.DiGraph, knowledge_graph: Dict[str, Any]) -> None:
        """
        Add fallback relationships to ensure the graph has visible connections.
        
        Args:
            G (nx.DiGraph): The NetworkX graph
            knowledge_graph (Dict[str, Any]): The knowledge graph data
        """
        if "entities" not in knowledge_graph:
            logger.warning("Knowledge graph missing entities section!")
            return
            
        # Get entities by hierarchy level
        entities_by_level = {
            "root": [],
            "trunk": [],
            "branch": [],
            "leaf": [],
            "resource": []
        }
        
        for entity in knowledge_graph["entities"]:
            level = entity.get("hierarchy_level", "branch")
            if level in entities_by_level:
                entities_by_level[level].append(entity)
        
        # Create hierarchical relationships between levels
        relationships = []
        
        # Connect root to trunk entities
        for root in entities_by_level["root"]:
            for trunk in entities_by_level["trunk"][:3]:  # Limit connections to prevent cluttering
                rel = {
                    "source": root["id"],
                    "target": trunk["id"],
                    "type": "contains",
                    "properties": {
                        "description": f"{root['name']} contains {trunk['name']}",
                        "strength": 0.9,
                        "hierarchical": True
                    }
                }
                relationships.append(rel)
                G.add_edge(root["id"], trunk["id"], type="contains", weight=0.9)
        
        # Connect trunk to branch entities
        for trunk in entities_by_level["trunk"]:
            for branch in entities_by_level["branch"][:3]:  # Limit connections
                rel = {
                    "source": trunk["id"],
                    "target": branch["id"],
                    "type": "implements",
                    "properties": {
                        "description": f"{branch['name']} implements concepts from {trunk['name']}",
                        "strength": 0.85,
                        "hierarchical": True
                    }
                }
                relationships.append(rel)
                G.add_edge(trunk["id"], branch["id"], type="implements", weight=0.85)
        
        # Connect branch to leaf entities
        for branch in entities_by_level["branch"]:
            for leaf in entities_by_level["leaf"][:3]:  # Limit connections
                rel = {
                    "source": branch["id"],
                    "target": leaf["id"],
                    "type": "applies",
                    "properties": {
                        "description": f"{leaf['name']} applies {branch['name']}",
                        "strength": 0.8,
                        "hierarchical": True
                    }
                }
                relationships.append(rel)
                G.add_edge(branch["id"], leaf["id"], type="applies", weight=0.8)
        
        # Update the knowledge graph with these relationships
        if "relationships" not in knowledge_graph:
            knowledge_graph["relationships"] = []
        
        knowledge_graph["relationships"].extend(relationships)
        logger.info(f"Added {len(relationships)} fallback relationships to ensure graph connectivity")
    
    def _create_enhanced_node_tooltip(self, entity: Dict[str, Any]) -> str:
        """
        Create a rich, enhanced HTML tooltip for a node with comprehensive information.
        
        Args:
            entity (Dict[str, Any]): The entity data
            
        Returns:
            str: HTML tooltip content
        """
        # Extract entity properties
        name = entity.get("name", "")
        entity_type = entity.get("type", "")
        hierarchy_level = entity.get("hierarchy_level", "")
        description = entity.get("description", "")
        
        # Get additional metadata
        properties = entity.get("properties", {})
        importance = properties.get("importance", 5)
        keywords = properties.get("keywords", [])
        category = properties.get("category", "")
        sources = properties.get("sources", [])
        source_type = properties.get("source_type", "")
        created_at = properties.get("created_at", "")
        updated_at = properties.get("updated_at", "")
        definition = properties.get("definition", "")
        temporal = properties.get("temporal", {})
        
        # Check for resources (visualizations, examples, references)
        resources = properties.get("resources", [])
        
        # Create visual indicators for importance
        importance_stars = "★" * min(importance, 5)
        importance_empty = "☆" * (5 - min(importance, 5))
        importance_display = f"{importance_stars}{importance_empty}"
        
        # Determine the hierarchy color
        hierarchy_colors = {
            "root": "#003366",
            "trunk": "#336699",
            "branch": "#66A3D2",
            "leaf": "#99CC99",
            "resource": "#D6A5C9"
        }
        color = hierarchy_colors.get(hierarchy_level, "#d2e5ff")
        
        # Create the HTML tooltip with a more sophisticated layout
        tooltip = f"""
        <div style="max-width: 450px; padding: 15px; background: white; border-left: 5px solid {color}; border-radius: 5px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <h3 style="margin-top: 0; color: {color}; border-bottom: 1px solid #eee; padding-bottom: 5px; flex-grow: 1;">{name}</h3>
                <div style="margin-left: 10px; color: #ffc107; white-space: nowrap;">{importance_display}</div>
            </div>
            
            <div style="margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 5px;">
                <span style="background: {color}; color: white; border-radius: 3px; padding: 2px 6px; font-size: 12px;">
                    {entity_type}
                </span>
                <span style="background: #f8f9fa; border-radius: 3px; padding: 2px 6px; font-size: 12px;">
                    {hierarchy_level}
                </span>
                {f'<span style="background: #e9ecef; border-radius: 3px; padding: 2px 6px; font-size: 12px;">{category}</span>' if category else ''}
            </div>"""
        
        # Add description with improved formatting
        if description:
            tooltip += f"""
            <div style="margin-bottom: 15px; line-height: 1.4;">
                <p style="margin: 0;">{description}</p>
            </div>"""
        
        # Add definition in a highlighted box if available
        if definition:
            tooltip += f"""
            <div style="background: #f0f7ff; padding: 10px; border-radius: 4px; margin-bottom: 15px; border-left: 3px solid {color};">
                <h4 style="margin-top: 0; margin-bottom: 5px; color: {color};">Definition</h4>
                <p style="margin: 0;">{definition}</p>
            </div>"""
        
        # Add temporal information if available
        if temporal and isinstance(temporal, dict) and (temporal.get("period") or temporal.get("year")):
            period = temporal.get("period", "")
            year = temporal.get("year", "")
            tooltip += f"""
            <div style="background: #f9f9f9; padding: 8px; border-radius: 4px; margin-bottom: 10px;">
                <h4 style="margin-top: 0; margin-bottom: 5px; font-size: 14px;">Temporal Information</h4>
                {f'<div><strong>Period:</strong> {period}</div>' if period else ''}
                {f'<div><strong>Year:</strong> {year}</div>' if year else ''}
            </div>"""
        
        # Create tabbed interface for additional information
        tooltip += """
            <div class="tab-container" style="margin-top: 15px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden;">
                <div class="tab-header" style="display: flex; background: #f5f5f5; border-bottom: 1px solid #ddd;">
                    <div class="tab active" onclick="switchTab(this, 'keywords')" style="padding: 8px 12px; cursor: pointer; font-weight: bold; border-bottom: 2px solid currentColor;">Keywords</div>
                    <div class="tab" onclick="switchTab(this, 'resources')" style="padding: 8px 12px; cursor: pointer;">Resources</div>
                    <div class="tab" onclick="switchTab(this, 'sources')" style="padding: 8px 12px; cursor: pointer;">Sources</div>
                </div>
                
                <div class="tab-content">"""
        
        # Keywords tab content
        tooltip += """
                    <div id="keywords" class="tab-pane active" style="padding: 10px; display: block;">"""
        if keywords:
            tooltip += """
                        <div style="display: flex; flex-wrap: wrap; gap: 5px;">"""
            tooltip += "".join([f'<span style="background: #e9ecef; padding: 3px 8px; border-radius: 15px; font-size: 12px;">{kw}</span>' for kw in keywords])
            tooltip += """
                        </div>"""
        else:
            tooltip += """
                        <p style="color: #6c757d; font-style: italic;">No keywords available</p>"""
        tooltip += """
                    </div>"""
        
        # Resources tab content (visualizations, examples, references)
        tooltip += """
                    <div id="resources" class="tab-pane" style="padding: 10px; display: none;">"""
        if resources:
            tooltip += """
                        <ul style="margin: 0; padding-left: 20px;">"""
            
            for resource in resources:
                if isinstance(resource, dict):
                    resource_type = resource.get("type", "reference")
                    resource_title = resource.get("title", "")
                    resource_description = resource.get("description", "")
                    resource_url = resource.get("url", "")
                    resource_image = resource.get("image", "")
                    
                    # Determine icon based on resource type
                    icon = "📄"
                    if "image" in resource_type.lower() or "visualization" in resource_type.lower():
                        icon = "🖼️"
                    elif "video" in resource_type.lower():
                        icon = "🎬"
                    elif "example" in resource_type.lower():
                        icon = "💡"
                    elif "code" in resource_type.lower():
                        icon = "💻"
                    
                    tooltip += f"""
                            <li style="margin-bottom: 8px;">
                                <div style="display: flex; align-items: flex-start;">
                                    <div style="margin-right: 8px; font-size: 18px;">{icon}</div>
                                    <div>
                                        {f'<strong>{resource_title}</strong><br>' if resource_title else ''}
                                        {f'{resource_description}<br>' if resource_description else ''}
                                        {f'<a href="{resource_url}" target="_blank" style="color: #0275d8; font-size: 12px;">View resource</a>' if resource_url else ''}
                                        {f'<div style="margin-top: 5px;"><img src="{resource_image}" alt="Resource visual" style="max-width: 100%; max-height: 120px; object-fit: contain;"></div>' if resource_image else ''}
                                    </div>
                                </div>
                            </li>"""
                else:
                    # If it's a string, just display it as resource text
                    tooltip += f"""
                            <li style="margin-bottom: 5px;">
                                <div style="display: flex; align-items: flex-start;">
                                    <div style="margin-right: 8px; font-size: 18px;">📄</div>
                                    <div>{resource}</div>
                                </div>
                            </li>"""
            
            tooltip += """
                        </ul>"""
        else:
            tooltip += """
                        <p style="color: #6c757d; font-style: italic;">No resources available</p>"""
        tooltip += """
                    </div>"""
        
        # Sources tab content
        tooltip += """
                    <div id="sources" class="tab-pane" style="padding: 10px; display: none;">"""
        if sources:
            tooltip += f"""
                        <div><strong>Origin:</strong> {", ".join(sources)}</div>"""
            if source_type:
                tooltip += f"""
                        <div style="margin-top: 5px;"><strong>Type:</strong> {source_type}</div>"""
        else:
            tooltip += """
                        <p style="color: #6c757d; font-style: italic;">No source information available</p>"""
        tooltip += """
                    </div>
                </div>
            </div>"""
            
        # Add JavaScript for tab switching
        tooltip += """
            <script>
            function switchTab(tab, tabId) {
                // Get all tabs and content panes
                var tabContainer = tab.parentNode.parentNode;
                var tabs = tabContainer.getElementsByClassName('tab');
                var panes = tabContainer.parentNode.getElementsByClassName('tab-pane');
                
                // Remove active class from all tabs and hide all panes
                for (var i = 0; i < tabs.length; i++) {
                    tabs[i].classList.remove('active');
                    tabs[i].style.borderBottom = 'none';
                }
                for (var i = 0; i < panes.length; i++) {
                    panes[i].style.display = 'none';
                }
                
                // Add active class to clicked tab and show corresponding pane
                tab.classList.add('active');
                tab.style.borderBottom = '2px solid currentColor';
                document.getElementById(tabId).style.display = 'block';
            }
            </script>
        """
        
        # Close the main div
        tooltip += """
        </div>
        """
        
        return tooltip
    
    def _create_tree_metaphor_legend(self, knowledge_graph: Dict[str, Any]) -> str:
        """
        Create an HTML legend explaining the tree metaphor visualization.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph
            
        Returns:
            str: HTML legend content
        """
        # Get hierarchy level counts
        hierarchy_counts = {
            "root": 0,
            "trunk": 0,
            "branch": 0,
            "leaf": 0,
            "resource": 0
        }
        
        # Count entities by hierarchy level
        for entity in knowledge_graph.get("entities", []):
            level = entity.get("hierarchy_level", "")
            if level in hierarchy_counts:
                hierarchy_counts[level] += 1
        
        # Format counts for display
        root_count = hierarchy_counts.get("root", 0)
        trunk_count = hierarchy_counts.get("trunk", 0)
        branch_count = hierarchy_counts.get("branch", 0)
        leaf_count = hierarchy_counts.get("leaf", 0)
        resource_count = hierarchy_counts.get("resource", 0)
        
        # Create enhanced legend HTML with visual tree metaphor - fixing f-string formatting
        legend_html = f"""
        <div class="tree-legend" style="position: absolute; top: 10px; right: 10px; width: 300px; background: rgba(255,255,255,0.9); border: 1px solid #d1d1d1; border-radius: 5px; padding: 15px; font-family: 'Segoe UI', Arial, sans-serif; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 1000; max-height: 80vh; overflow-y: auto;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #003366;">Tree of Knowledge</h3>
                <button onclick="toggleLegend()" style="background: none; border: none; cursor: pointer; font-size: 16px;">−</button>
            </div>
            
            <div id="legend-content">
                <div class="tree-illustration" style="text-align: center; margin-bottom: 15px;">
                    <svg width="200" height="220" viewBox="0 0 200 220">
                        <!-- Root -->
                        <rect x="85" y="200" width="30" height="15" fill="#003366" rx="2" ry="2" />
                        
                        <!-- Trunk -->
                        <rect x="95" y="160" width="10" height="40" fill="#336699" />
                        
                        <!-- Branches -->
                        <path d="M95 160 L65 130" stroke="#66A3D2" stroke-width="6" fill="none" />
                        <path d="M105 160 L135 130" stroke="#66A3D2" stroke-width="6" fill="none" />
                        
                        <!-- Leaves/Fruits -->
                        <circle cx="55" cy="120" r="10" fill="#99CC99" />
                        <circle cx="75" cy="110" r="10" fill="#99CC99" />
                        <circle cx="125" cy="110" r="10" fill="#99CC99" />
                        <circle cx="145" cy="120" r="10" fill="#99CC99" />
                        
                        <!-- Resources -->
                        <polygon points="40,140 50,130 60,140 50,150" fill="#D6A5C9" />
                        <polygon points="160,140 170,130 180,140 170,150" fill="#D6A5C9" />
                    </svg>
                </div>
                
                <div class="level" style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 20px; height: 20px; background: #003366; border-radius: 2px; margin-right: 10px;"></div>
                    <div>
                        <div style="font-weight: bold;">Roots: Foundation ({root_count})</div>
                        <div style="font-size: 12px; color: #666;">Course domains, fields, subjects</div>
                    </div>
                </div>
                
                <div class="level" style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 20px; height: 20px; background: #336699; border-radius: 50%; margin-right: 10px;"></div>
                    <div>
                        <div style="font-weight: bold;">Trunk: Concepts ({trunk_count})</div>
                        <div style="font-size: 12px; color: #666;">Theories, principles, frameworks</div>
                    </div>
                </div>
                
                <div class="level" style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 20px; height: 20px; background: #66A3D2; border: 1px solid #5590bd; margin-right: 10px;"></div>
                    <div>
                        <div style="font-weight: bold;">Branches: Methods ({branch_count})</div>
                        <div style="font-size: 12px; color: #666;">Techniques, approaches, processes</div>
                    </div>
                </div>
                
                <div class="level" style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 20px; height: 20px; background: #99CC99; border-radius: 50%; margin-right: 10px;"></div>
                    <div>
                        <div style="font-weight: bold;">Fruits/Leaves: Examples ({leaf_count})</div>
                        <div style="font-size: 12px; color: #666;">Applications, examples, case studies</div>
                    </div>
                </div>
                
                <div class="level" style="display: flex; align-items: center; margin-bottom: 12px;">
                    <div style="width: 20px; height: 20px; background: #D6A5C9; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); margin-right: 10px;"></div>
                    <div>
                        <div style="font-weight: bold;">Resources: Supporting ({resource_count})</div>
                        <div style="font-size: 12px; color: #666;">Visuals, definitions, references</div>
                    </div>
                </div>
                
                <h4 style="margin: 15px 0 10px 0; padding-top: 10px; border-top: 1px solid #eee;">Relationships:</h4>
                
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 40px; height: 3px; background: #0077b6; margin-right: 10px;"></div>
                    <div style="font-size: 13px;">Contains/Is Part Of</div>
                </div>
                
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 40px; height: 3px; background: #00b4d8; margin-right: 10px;"></div>
                    <div style="font-size: 13px;">Implements</div>
                </div>
                
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 40px; height: 3px; background: #90e0ef; margin-right: 10px;"></div>
                    <div style="font-size: 13px;">Applies</div>
                </div>
                
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 40px; height: 3px; background: #666666; border-top: 1px dashed #666666; margin-right: 10px;"></div>
                    <div style="font-size: 13px;">Related To</div>
                </div>
                
                <div style="font-size: 12px; margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee; color: #666;">
                    <div>• Click on nodes to see detailed information</div>
                    <div>• Hover over connections to see relationship details</div>
                    <div>• Use mouse wheel to zoom in/out</div>
                </div>
            </div>
            
            <script>
            function toggleLegend() {{
                var content = document.getElementById('legend-content');
                var button = content.previousElementSibling.querySelector('button');
                
                if (content.style.display === 'none') {{
                    content.style.display = 'block';
                    button.textContent = '−';
                }} else {{
                    content.style.display = 'none';
                    button.textContent = '+';
                }}
            }}
            </script>
        </div>
        """
        
        return legend_html
    
    def _append_legend_to_html(self, html_file: str, legend_html: str) -> None:
        """
        Append the legend HTML to the visualization HTML file.
        
        Args:
            html_file (str): Path to the HTML file
            legend_html (str): Legend HTML content
        """
        try:
            # Read the file with proper encoding detection
            with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Insert the legend before the closing body tag
            if '</body>' in content:
                new_content = content.replace('</body>', f'{legend_html}</body>')
                
                # Write the modified content back to the file
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"Added legend to {html_file}")
            else:
                logger.warning(f"Could not find </body> tag in {html_file}")
        except Exception as e:
            logger.error(f"Error adding legend to HTML file: {str(e)}")
    
    def _create_networkx_graph(self, knowledge_graph: Dict[str, Any]) -> nx.DiGraph:
        """
        Create a NetworkX directed graph from the knowledge graph.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph
            
        Returns:
            nx.DiGraph: The NetworkX directed graph
        """
        G = nx.DiGraph()
        
        # Add nodes (entities)
        for entity in knowledge_graph.get("entities", []):
            entity_id = entity.get("id")
            if entity_id:
                # Use entity name as label, fallback to id if not available
                label = entity.get("name", entity_id)
                G.add_node(entity_id, label=label)
        
        # Add edges (relationships)
        for relationship in knowledge_graph.get("relationships", []):
            source = relationship.get("source")
            target = relationship.get("target")
            rel_type = relationship.get("type", "related_to")
            
            if source and target:
                # Check if both nodes exist
                if G.has_node(source) and G.has_node(target):
                    G.add_edge(source, target, title=rel_type)
        
        # Check if we have edges in the graph
        if len(G.edges()) == 0 and len(G.nodes()) > 1:
            logger.warning("No edges found in the knowledge graph! Adding missing relationships...")
            self._add_fallback_relationships(G, knowledge_graph)
        
        return G
    
    def _brighten_color(self, hex_color: str, factor: float = 0.3) -> str:
        """
        Brighten a hex color by a factor.
        
        Args:
            hex_color (str): Hex color code
            factor (float): Brightening factor (0 to 1)
            
        Returns:
            str: Brightened hex color
        """
        # Remove the hash at the beginning if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Brighten the color
        new_rgb = []
        for color in rgb:
            # Apply brightening formula
            new_color = int(color + (255 - color) * factor)
            # Ensure value is in range 0-255
            new_color = max(0, min(255, new_color))
            new_rgb.append(new_color)
        
        # Convert back to hex
        return '#%02x%02x%02x' % tuple(new_rgb)
    
    def _darken_color(self, hex_color: str, factor: float = 0.3) -> str:
        """
        Darken a hex color by a factor.
        
        Args:
            hex_color (str): Hex color code
            factor (float): Darkening factor (0 to 1)
            
        Returns:
            str: Darkened hex color
        """
        # Remove the hash at the beginning if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Darken the color
        new_rgb = []
        for color in rgb:
            # Apply darkening formula
            new_color = int(color * (1 - factor))
            # Ensure value is in range 0-255
            new_color = max(0, min(255, new_color))
            new_rgb.append(new_color)
        
        # Convert back to hex
        return '#%02x%02x%02x' % tuple(new_rgb)
    
    def create_static_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        output_dir: str,
        filename: str = "knowledge_graph_static.png",
        figsize: Tuple[int, int] = (16, 12)
    ) -> str:
        """
        Create a static visualization of the knowledge graph.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph to visualize
            output_dir (str): Directory to save the visualization
            filename (str, optional): Name of the output PNG file
            figsize (Tuple[int, int], optional): Figure size (width, height)
            
        Returns:
            str: Path to the generated PNG file
        """
        logger.info("Creating static visualization of knowledge graph")
        
        try:
            # Create the graph
            G = self._create_networkx_graph(knowledge_graph)
            
            # Check if we have edges in the graph
            if len(G.edges()) == 0:
                logger.warning("No edges found in the knowledge graph! Adding missing relationships...")
                # Add fallback relationships
                self._add_fallback_relationships(G, knowledge_graph)
            
            # Create a hierarchical layout
            pos = nx.spring_layout(G, k=1.5, iterations=100)
            
            # Extract hierarchy levels for visual differentiation
            hierarchy_levels = {
                "root": [],
                "trunk": [],
                "branch": [],
                "leaf": [],
                "resource": []
            }
            
            node_sizes = {}
            node_colors = {}
            node_labels = {}
            
            for entity in knowledge_graph.get("entities", []):
                entity_id = entity.get("id", "")
                hierarchy_level = entity.get("hierarchy_level", "branch")
                importance = entity.get("properties", {}).get("importance", 5)
                
                if hierarchy_level in hierarchy_levels:
                    hierarchy_levels[hierarchy_level].append(entity_id)
                
                # Set node sizes based on importance and hierarchy level
                size_multiplier = {
                    "root": 3000,
                    "trunk": 2000,
                    "branch": 1500,
                    "leaf": 1000,
                    "resource": 800
                }
                base_size = size_multiplier.get(hierarchy_level, 1500)
                node_sizes[entity_id] = base_size + (importance * 100)
                
                # Set node colors based on hierarchy level
                node_colors[entity_id] = self.hierarchy_colors.get(hierarchy_level, "#d2e5ff")
                
                # Set node labels
                node_labels[entity_id] = entity.get("name", entity_id)
            
            # Create figure
            fig, ax = plt.subplots(figsize=figsize, dpi=100)
            
            # Define edge colors and styles
            edge_colors = []
            edge_widths = []
            edge_styles = []
            
            for u, v, data in G.edges(data=True):
                rel = self._find_relationship(knowledge_graph, u, v)
                if rel:
                    rel_type = rel.get("type", "related_to")
                    if rel_type == "contains" or rel_type == "is_part_of":
                        edge_colors.append("#0077b6")
                        edge_widths.append(2.5)
                        edge_styles.append("solid")
                    elif rel_type == "implements":
                        edge_colors.append("#00b4d8")
                        edge_widths.append(2)
                        edge_styles.append("solid")
                    elif rel_type == "applies":
                        edge_colors.append("#90e0ef")
                        edge_widths.append(2)
                        edge_styles.append("solid")
                    elif rel_type == "progression":
                        edge_colors.append("#d90429")
                        edge_widths.append(2)
                        edge_styles.append("dashed")
                    else:
                        edge_colors.append("#666666")
                        edge_widths.append(1.5)
                        edge_styles.append("dotted")
                else:
                    edge_colors.append("#999999")
                    edge_widths.append(1)
                    edge_styles.append("dotted")
            
            # Draw nodes by hierarchy level to ensure proper stacking
            for level, nodes in hierarchy_levels.items():
                nx.draw_networkx_nodes(
                    G, pos, 
                    nodelist=nodes,
                    node_size=[node_sizes.get(node, 1500) for node in nodes],
                    node_color=[node_colors.get(node, "#d2e5ff") for node in nodes],
                    alpha=0.85,
                    linewidths=2,
                    edgecolors='white',
                    ax=ax
                )
            
            # Draw edges
            for i, (u, v, data) in enumerate(G.edges(data=True)):
                nx.draw_networkx_edges(
                    G, pos,
                    edgelist=[(u, v)],
                    width=edge_widths[i],
                    edge_color=edge_colors[i],
                    style=edge_styles[i],
                    alpha=0.7,
                    arrows=True,
                    arrowsize=15,
                    ax=ax
                )
            
            # Draw node labels
            nx.draw_networkx_labels(
                G, pos,
                labels=node_labels,
                font_size=10,
                font_family='sans-serif',
                font_weight='bold',
                ax=ax
            )
            
            # Create legend
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.hierarchy_colors["root"], markersize=15, label='Root (Domain)'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.hierarchy_colors["trunk"], markersize=15, label='Trunk (Concepts)'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.hierarchy_colors["branch"], markersize=15, label='Branch (Methods)'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.hierarchy_colors["leaf"], markersize=15, label='Leaf (Examples)'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.hierarchy_colors["resource"], markersize=15, label='Resource'),
                plt.Line2D([0], [0], color='#0077b6', lw=2, label='Contains'),
                plt.Line2D([0], [0], color='#00b4d8', lw=2, label='Implements'),
                plt.Line2D([0], [0], color='#90e0ef', lw=2, label='Applies'),
                plt.Line2D([0], [0], color='#666666', lw=2, linestyle='dotted', label='Related')
            ]
            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1))
            
            # Set title and remove axes
            plt.title(f"Knowledge Graph: Tree of Knowledge", fontsize=16, pad=20)
            plt.axis('off')
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Save figure
            output_path = os.path.join(output_dir, filename)
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close(fig)
            
            logger.info(f"Static visualization saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating static visualization: {str(e)}")
            raise 

    def create_multi_level_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        output_dir: Optional[str] = None,
        filename: Optional[str] = None,
        height: Optional[str] = None,
        width: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create multi-level interactive visualizations of the knowledge graph.
        
        This generates multiple HTML files for different levels of the knowledge graph:
        - Level 1: Overview (domains and modules)
        - Level 2: Module views (module and its topics)
        - Level 3: Topic views (topic and its details)
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph to visualize
            output_dir (Optional[str]): Directory to save the visualization files (defaults to output/visualizations/multi_level)
            filename (Optional[str]): Base filename for the HTML files (defaults to "knowledge_graph")
            height (Optional[str]): Height of the visualization (defaults to "800px")
            width (Optional[str]): Width of the visualization (defaults to "100%")
            
        Returns:
            Dict[str, str]: Dictionary mapping view names to output file paths
        """
        # Process defaults
        output_dir = output_dir or os.path.join(self.output_dir, "multi_level")
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Creating multi_level visualization of knowledge graph with {len(knowledge_graph.get('entities', []))} entities and {len(knowledge_graph.get('relationships', []))} relationships")
        
        try:
            logger.info(f"Creating multi-level visualization of knowledge graph")
            # Create all the hierarchical views
            output_files = self._create_hierarchical_views(
                knowledge_graph, 
                output_dir,
                height=height or self.default_height,
                width=width or self.default_width
            )
            
            return output_files
            
        except Exception as e:
            logger.error(f"Error creating multi-level visualization: {str(e)}")
            raise
    
    def _create_hierarchical_views(
        self,
        knowledge_graph: Dict[str, Any],
        output_dir: str,
        height: Optional[str] = None,
        width: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create hierarchical views of the knowledge graph, including an overview,
        module, and topic views.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph
            output_dir (str): Directory to save the visualization files
            height (Optional[str]): Height of the visualization
            width (Optional[str]): Width of the visualization
            
        Returns:
            Dict[str, str]: Dictionary mapping view names to output file paths
        """
        output_files = {}
        
        # First, create separate views for each level
        views = self._create_hierarchical_views_data(knowledge_graph)
        
        # Create the overview visualization (Level 1)
        overview_file = os.path.join(output_dir, "knowledge_graph_overview.html")
        self._create_overview_visualization(
            knowledge_graph,
            views["overview"],
            overview_file,
            height or self.default_height,
            width or self.default_width
        )
        output_files["overview"] = overview_file
        
        # Create module visualizations (Level 2)
        for module_id in views["modules"]:
            module_file = os.path.join(output_dir, f"knowledge_graph_module_{module_id}.html")
            self._create_module_visualization(
                knowledge_graph,
                views["modules"][module_id],
                module_file,
                height or self.default_height,
                width or self.default_width,
                module_id
            )
            output_files[f"module_{module_id}"] = module_file
        
        # Create topic visualizations (Level 3)
        for topic_id in views["topics"]:
            topic_file = os.path.join(output_dir, f"knowledge_graph_topic_{topic_id}.html")
            self._create_topic_visualization(
                knowledge_graph,
                views["topics"][topic_id],
                topic_file,
                height or self.default_height,
                width or self.default_width,
                topic_id
            )
            output_files[f"topic_{topic_id}"] = topic_file
        
        return output_files
    
    def _get_connected_entities(
        self, 
        relationships: List[Dict[str, Any]], 
        entity_id: str, 
        target_level: Union[str, List[str]], 
        knowledge_graph: Dict[str, Any]
    ) -> Set[str]:
        """
        Get entities connected to a given entity with optional filtering by hierarchy level.
        
        Args:
            relationships (List[Dict[str, Any]]): List of relationships
            entity_id (str): ID of the source entity
            target_level (Union[str, List[str]]): Target hierarchy level(s) to filter by
            knowledge_graph (Dict[str, Any]): The knowledge graph
            
        Returns:
            Set[str]: Set of entity IDs connected to the given entity
        """
        if isinstance(target_level, str):
            target_levels = [target_level]
        else:
            target_levels = target_level
            
        connected_entities = set()
        
        for rel in relationships:
            source = rel.get("source")
            target = rel.get("target")
            
            # Check outgoing connections
            if source == entity_id:
                target_entity = self._find_entity_by_id(knowledge_graph, target)
                if target_entity and target_entity.get("hierarchy_level") in target_levels:
                    connected_entities.add(target)
            
            # Check incoming connections
            elif target == entity_id:
                source_entity = self._find_entity_by_id(knowledge_graph, source)
                if source_entity and source_entity.get("hierarchy_level") in target_levels:
                    connected_entities.add(source)
        
        return connected_entities
    
    def _filter_relationships(
        self, 
        relationships: List[Dict[str, Any]], 
        entity_ids: Set[str], 
        limit_per_node: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Filter relationships to include only those between entities in the given set,
        and limit the number of relationships per node using importance-based filtering.
        
        Args:
            relationships (List[Dict[str, Any]]): List of relationships
            entity_ids (Set[str]): Set of entity IDs to include
            limit_per_node (int, optional): Maximum number of relationships per node
            
        Returns:
            List[Dict[str, Any]]: Filtered list of relationships
        """
        # First, collect all relationships between entities in the set
        filtered_rels = []
        relationship_counts = {}  # entity_id -> count
        
        # Initialize relationship counts
        for entity_id in entity_ids:
            relationship_counts[entity_id] = 0
        
        # Group relationships by source entity
        relationships_by_source = {}
        for rel in relationships:
            source = rel.get("source")
            target = rel.get("target")
            
            if source in entity_ids and target in entity_ids:
                if source not in relationships_by_source:
                    relationships_by_source[source] = []
                
                # Calculate relationship importance score
                importance = self._calculate_relationship_importance(rel)
                rel["_importance_score"] = importance
                
                relationships_by_source[source].append(rel)
        
        # For each source entity, select the most important relationships up to the limit
        for source, rels in relationships_by_source.items():
            # Sort by importance (descending)
            sorted_rels = sorted(rels, key=lambda r: r.get("_importance_score", 0), reverse=True)
            
            # Take top N relationships
            for rel in sorted_rels[:limit_per_node]:
                # Remove temporary importance score
                if "_importance_score" in rel:
                    del rel["_importance_score"]
                
                filtered_rels.append(rel)
        
        return filtered_rels
    
    def _calculate_relationship_importance(self, relationship: Dict[str, Any]) -> float:
        """
        Calculate an importance score for a relationship based on its properties.
        
        Args:
            relationship (Dict[str, Any]): The relationship
            
        Returns:
            float: Importance score (higher is more important)
        """
        # Start with base importance
        importance = 5.0
        
        # Adjust based on relationship properties
        properties = relationship.get("properties", {})
        
        # If relationship has an explicit strength, use it as a base
        if "strength" in properties:
            importance = float(properties["strength"]) * 10
        
        # Hierarchical relationships are more important
        if properties.get("hierarchical", False):
            importance += 2.0
        
        # Relationship type importance
        rel_type = relationship.get("type", "related_to")
        type_importance = {
            "contains": 3.0,
            "is_part_of": 3.0,
            "has_part": 2.5,
            "implements": 2.0,
            "same_as": 1.5,
            "progression": 1.0,
            "related_to": 0.5
        }
        importance += type_importance.get(rel_type, 0.0)
        
        return importance
    
    def _find_parent_module(self, knowledge_graph: Dict[str, Any], topic_id: str) -> Optional[str]:
        """
        Find the parent module (trunk entity) of a topic (branch entity).
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph
            topic_id (str): ID of the topic entity
            
        Returns:
            Optional[str]: ID of the parent module entity, or None if not found
        """
        for rel in knowledge_graph.get("relationships", []):
            if rel.get("target") == topic_id and rel.get("type") in ["contains", "has_part"]:
                source_id = rel.get("source")
                source_entity = self._find_entity_by_id(knowledge_graph, source_id)
                if source_entity and source_entity.get("hierarchy_level") == "trunk":
                    return source_id
        return None 

    def _create_overview_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        view: Dict[str, Any],
        output_file: str,
        height: str,
        width: str
    ) -> None:
        """
        Create an overview visualization (Level 1) showing root and trunk entities.
        
        Args:
            knowledge_graph (Dict[str, Any]): The complete knowledge graph
            view (Dict[str, Any]): The filtered view for this level
            output_file (str): Path to the output HTML file
            height (str): Height of the visualization
            width (str): Width of the visualization
        """
        # Create a subgraph containing only the entities and relationships for this view
        subgraph = {
            "entities": view["entities"],
            "relationships": view["relationships"]
        }
        
        # Create a Pyvis network
        net = Network(
            height=height,
            width=width,
            bgcolor="#FFFFFF",
            font_color="#333333",
            directed=True,
            notebook=False
        )
        
        # Create NetworkX graph from the subgraph
        G = self._create_networkx_graph(subgraph)
        
        # Add network from NetworkX
        net.from_nx(G)
        
        # Style the nodes and edges
        self._style_nodes_and_edges(net, subgraph)
        
        # Set options for hierarchical layout
        self._set_hierarchical_options(net)
        
        # Add navigation controls
        nav_html = self._create_navigation_controls(
            "Overview",
            "This is the top-level view showing course domains and main modules.",
            None,  # No parent for the overview
            level="1",  # Changed to string to ensure consistency
            knowledge_graph=knowledge_graph
        )
        
        # Add legend
        legend_html = self._create_tree_metaphor_legend(knowledge_graph)
        
        # Add node click handler for navigation
        navigation_script = self._create_node_navigation_script(
            "overview",
            "module",
            filename_prefix="knowledge_graph"
        )
        
        # Save to HTML file
        try:
            net.save_graph(output_file)
            
            # Append navigation controls and legend to the HTML file
            self._append_html_to_file(output_file, nav_html, "nav-controls")
            self._append_html_to_file(output_file, legend_html, "legend")
            self._append_html_to_file(output_file, navigation_script, "navigation-script")
            
            logger.info(f"Saved overview visualization to {output_file}")
        except Exception as e:
            logger.error(f"Error saving overview visualization: {str(e)}")
            raise
    
    def _create_module_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        view: Dict[str, Any],
        output_file: str,
        height: str,
        width: str,
        module_id: str
    ) -> None:
        """
        Create a module visualization (Level 2) showing module and its topics.
        
        Args:
            knowledge_graph (Dict[str, Any]): The complete knowledge graph
            view (Dict[str, Any]): The filtered view for this level
            output_file (str): Path to the output HTML file
            height (str): Height of the visualization
            width (str): Width of the visualization
            module_id (str): ID of the module being visualized
        """
        # Create a subgraph containing only the entities and relationships for this view
        subgraph = {
            "entities": view["entities"],
            "relationships": view["relationships"]
        }
        
        # Create a Pyvis network
        net = Network(
            height=height,
            width=width,
            bgcolor="#FFFFFF",
            font_color="#333333",
            directed=True,
            notebook=False
        )
        
        # Create NetworkX graph from the subgraph
        G = self._create_networkx_graph(subgraph)
        
        # Add network from NetworkX
        net.from_nx(G)
        
        # Style the nodes and edges
        self._style_nodes_and_edges(net, subgraph)
        
        # Set options for hierarchical layout
        self._set_hierarchical_options(net)
        
        # Find module entity to get its name
        module_entity = self._find_entity_by_id(knowledge_graph, module_id)
        module_name = module_entity.get("name", "Module") if module_entity else "Module"
        
        # Add navigation controls
        nav_html = self._create_navigation_controls(
            module_name,
            f"This view shows the module '{module_name}' and its topics.",
            parent="Overview",  # Parent is the overview
            level="2",  # We're at level 2 (module level)
            knowledge_graph=knowledge_graph
        )
        
        # Add legend
        legend_html = self._create_tree_metaphor_legend(knowledge_graph)
        
        # Add node click handler for navigation
        navigation_script = self._create_node_navigation_script(
            "module",
            "topic",
            filename_prefix="knowledge_graph",
            module_id=module_id
        )
        
        # Save to HTML file
        try:
            net.save_graph(output_file)
            
            # Append navigation controls and legend to the HTML file
            self._append_html_to_file(output_file, nav_html, "nav-controls")
            self._append_html_to_file(output_file, legend_html, "legend")
            self._append_html_to_file(output_file, navigation_script, "navigation-script")
            
            logger.info(f"Saved module visualization to {output_file}")
        except Exception as e:
            logger.error(f"Error saving module visualization: {str(e)}")
            raise
    
    def _create_topic_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        view: Dict[str, Any],
        output_file: str,
        height: str,
        width: str,
        topic_id: str
    ) -> None:
        """
        Create a topic visualization (Level 3) showing topic and its related entities.
        
        Args:
            knowledge_graph (Dict[str, Any]): The complete knowledge graph
            view (Dict[str, Any]): The filtered view for this level
            output_file (str): Path to the output HTML file
            height (str): Height of the visualization
            width (str): Width of the visualization
            topic_id (str): ID of the topic being visualized
        """
        # Create a subgraph containing only the entities and relationships for this view
        subgraph = {
            "entities": view["entities"],
            "relationships": view["relationships"]
        }
        
        # Create a Pyvis network
        net = Network(
            height=height,
            width=width,
            bgcolor="#FFFFFF",
            font_color="#333333",
            directed=True,
            notebook=False
        )
        
        # Create NetworkX graph from the subgraph
        G = self._create_networkx_graph(subgraph)
        
        # Add network from NetworkX
        net.from_nx(G)
        
        # Style the nodes and edges
        self._style_nodes_and_edges(net, subgraph)
        
        # Set options for hierarchical layout
        self._set_hierarchical_options(net)
        
        # Find topic entity to get its name and parent module
        topic_entity = self._find_entity_by_id(knowledge_graph, topic_id)
        topic_name = topic_entity.get("name", "Topic") if topic_entity else "Topic"
        
        # Find parent module
        parent_module_id = self._find_parent_module(knowledge_graph, topic_id)
        parent_module_entity = self._find_entity_by_id(knowledge_graph, parent_module_id) if parent_module_id else None
        parent_module_name = parent_module_entity.get("name", "Module") if parent_module_entity else "Module"
        
        # Add navigation controls
        nav_html = self._create_navigation_controls(
            topic_name,
            f"This view shows the topic '{topic_name}' and its related entities.",
            parent=parent_module_name,  # Parent is the module
            level="3",  # We're at level 3 (topic level)
            level_name="Topics",
            knowledge_graph=knowledge_graph
        )
        
        # Add legend
        legend_html = self._create_tree_metaphor_legend(knowledge_graph)
        
        # Add node click handler for navigation
        navigation_script = self._create_node_navigation_script(
            "topic",
            None,  # No deeper level to navigate to
            filename_prefix="knowledge_graph",
            module_id=parent_module_id,
            topic_id=topic_id
        )
        
        # Save to HTML file
        try:
            net.save_graph(output_file)
            
            # Append navigation controls and legend to the HTML file
            self._append_html_to_file(output_file, nav_html, "nav-controls")
            self._append_html_to_file(output_file, legend_html, "legend")
            self._append_html_to_file(output_file, navigation_script, "navigation-script")
            
            logger.info(f"Saved topic visualization to {output_file}")
        except Exception as e:
            logger.error(f"Error saving topic visualization: {str(e)}")
            raise
            
    def _create_node_navigation_script(
        self,
        current_level: str,
        target_level: Optional[str],
        filename_prefix: str = "knowledge_graph",
        module_id: Optional[str] = None,
        topic_id: Optional[str] = None
    ) -> str:
        """
        Create JavaScript for node click navigation between visualization levels.
        
        Args:
            current_level (str): Current visualization level ('overview', 'module', or 'topic')
            target_level (Optional[str]): Target level to navigate to, or None if at leaf level
            filename_prefix (str): Prefix for HTML filenames
            module_id (Optional[str]): ID of the current module (for module view)
            topic_id (Optional[str]): ID of the current topic (for topic view)
            
        Returns:
            str: HTML/JavaScript for node navigation
        """
        # Create JavaScript for node click navigation
        if current_level == "overview" and target_level == "module":
            # From overview to module level
            script = """
            <script>
            // Add click event handler for nodes to navigate to module view
            document.addEventListener('DOMContentLoaded', function() {
                // Make sure network is defined
                setTimeout(function() {
                    if (typeof network !== 'undefined') {
                        console.log("Setting up navigation from overview to module view");
                        
                        network.on("click", function(params) {
                            if (params.nodes.length > 0) {
                                const nodeId = params.nodes[0];
                                const nodeData = network.body.data.nodes.get(nodeId);
                                
                                if (nodeData && nodeData.group === "trunk") {
                                    console.log("Clicked on module node:", nodeId);
                                    // Navigate to module view
                                    const moduleFilename = `%s_module_${nodeId}.html`;
                                    window.location.href = moduleFilename;
                                }
                            }
                        });
                        
                        // Add hover effect for clickable nodes
                        network.on("hoverNode", function(params) {
                            const nodeId = params.node;
                            const nodeData = network.body.data.nodes.get(nodeId);
                            
                            if (nodeData && nodeData.group === "trunk") {
                                document.body.style.cursor = 'pointer';
                            }
                        });
                        
                        network.on("blurNode", function(params) {
                            document.body.style.cursor = 'default';
                        });
                    } else {
                        console.error("Network object not found");
                    }
                }, 1000); // Give time for network to be initialized
            });
            </script>
            """ % filename_prefix
            
        elif current_level == "module" and target_level == "topic":
            # From module to topic level
            script = """
            <script>
            // Add click event handler for nodes to navigate to topic view
            document.addEventListener('DOMContentLoaded', function() {
                // Make sure network is defined
                setTimeout(function() {
                    if (typeof network !== 'undefined') {
                        console.log("Setting up navigation from module to topic view");
                        
                        network.on("click", function(params) {
                            if (params.nodes.length > 0) {
                                const nodeId = params.nodes[0];
                                const nodeData = network.body.data.nodes.get(nodeId);
                                
                                if (nodeData && nodeData.group === "branch") {
                                    console.log("Clicked on topic node:", nodeId);
                                    // Navigate to topic view
                                    const topicFilename = `%s_topic_${nodeId}.html`;
                                    window.location.href = topicFilename;
                                }
                            }
                        });
                        
                        // Add hover effect for clickable nodes
                        network.on("hoverNode", function(params) {
                            const nodeId = params.node;
                            const nodeData = network.body.data.nodes.get(nodeId);
                            
                            if (nodeData && nodeData.group === "branch") {
                                document.body.style.cursor = 'pointer';
                            }
                        });
                        
                        network.on("blurNode", function(params) {
                            document.body.style.cursor = 'default';
                        });
                    } else {
                        console.error("Network object not found");
                    }
                }, 1000); // Give time for network to be initialized
            });
            </script>
            """ % filename_prefix
            
        elif current_level == "topic" and target_level is None:
            # At topic level, no deeper navigation, but add interactivity
            script = """
            <script>
            // Add detailed information panel for clicked nodes
            document.addEventListener('DOMContentLoaded', function() {
                // Make sure network is defined
                setTimeout(function() {
                    if (typeof network !== 'undefined') {
                        console.log("Setting up node interaction at topic level");
                        
                        network.on("click", function(params) {
                            if (params.nodes.length > 0) {
                                const nodeId = params.nodes[0];
                                const nodeData = network.body.data.nodes.get(nodeId);
                                const nodeTitle = nodeData.title || '';
                                
                                console.log("Clicked on node:", nodeId);
                                
                                // Create or update info panel
                                let infoPanel = document.getElementById('node-info-panel');
                                if (!infoPanel) {
                                    infoPanel = document.createElement('div');
                                    infoPanel.id = 'node-info-panel';
                                    infoPanel.style.position = 'absolute';
                                    infoPanel.style.right = '10px';
                                    infoPanel.style.top = '10px';
                                    infoPanel.style.width = '300px';
                                    infoPanel.style.padding = '15px';
                                    infoPanel.style.backgroundColor = 'rgba(255,255,255,0.95)';
                                    infoPanel.style.border = '1px solid #d1d1d1';
                                    infoPanel.style.borderRadius = '5px';
                                    infoPanel.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
                                    infoPanel.style.zIndex = '1000';
                                    infoPanel.style.maxHeight = '80vh';
                                    infoPanel.style.overflowY = 'auto';
                                    document.body.appendChild(infoPanel);
                                }
                                
                                // Extract content from HTML tooltip if needed
                                let tooltipContent = nodeTitle;
                                if (nodeTitle.startsWith("<")) {
                                    const parser = new DOMParser();
                                    const tooltipDoc = parser.parseFromString(nodeTitle, 'text/html');
                                    tooltipContent = tooltipDoc.body.innerHTML;
                                }
                                
                                // Update info panel
                                infoPanel.innerHTML = `
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                        <h3 style="margin: 0; color: #003366;">${nodeData.label || 'Entity Details'}</h3>
                                        <button onclick="document.getElementById('node-info-panel').style.display='none'" 
                                            style="background: none; border: none; cursor: pointer; font-size: 16px;">×</button>
                                    </div>
                                    <div>${tooltipContent}</div>
                                `;
                                infoPanel.style.display = 'block';
                            }
                        });
                    } else {
                        console.error("Network object not found");
                    }
                }, 1000); // Give time for network to be initialized
            });
            </script>
            """
        else:
            # Default case or unrecognized level combination
            script = """
            <script>
            // Add basic node click behavior
            document.addEventListener('DOMContentLoaded', function() {
                // Make sure network is defined
                setTimeout(function() {
                    if (typeof network !== 'undefined') {
                        console.log("Setting up basic node interaction");
                        
                        network.on("click", function(params) {
                            if (params.nodes.length > 0) {
                                // Node click detected
                                console.log('Node clicked:', params.nodes[0]);
                            }
                        });
                    } else {
                        console.error("Network object not found");
                    }
                }, 1000); // Give time for network to be initialized
            });
            </script>
            """
        
        # Add a navigation bar with links back to parent views
        nav_links = []
        
        # Always include a link to the overview
        nav_links.append(f'<a href="{filename_prefix}_overview.html" class="nav-btn">Overview</a>')
        
        # Add module link if we're at topic level
        if current_level == "topic" and module_id:
            nav_links.append(f'<a href="{filename_prefix}_module_{module_id}.html" class="nav-btn">Back to Module</a>')
            
        # Create the navigation bar
        if nav_links:
            nav_bar = f"""
            <div id="nav-bar" style="position: fixed; top: 10px; left: 10px; z-index: 1000; 
                display: flex; gap: 10px; background: rgba(255,255,255,0.8); 
                padding: 8px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                {' '.join(nav_links)}
            </div>
            <style>
                .nav-btn {{
                    background-color: #336699;
                    color: white;
                    padding: 5px 12px;
                    border-radius: 4px;
                    text-decoration: none;
                    font-size: 14px;
                    font-weight: bold;
                    transition: background-color 0.2s;
                }}
                .nav-btn:hover {{
                    background-color: #264d73;
                }}
            </style>
            """
            script += nav_bar
        
        # Add a notification to users about clickable nodes
        if target_level is not None:
            help_text = {
                "overview": "Click on module nodes (blue circles) to explore them in detail.",
                "module": "Click on topic nodes (blue boxes) to see their detailed view.",
                "topic": "Click on nodes to see detailed information about them."
            }
            
            help_html = f"""
            <div id="help-tooltip" style="position: fixed; bottom: 20px; right: 20px; 
                background: rgba(0,0,0,0.7); color: white; padding: 10px 15px; 
                border-radius: 5px; font-size: 14px; max-width: 300px; z-index: 1000;">
                <p style="margin: 0;">{help_text.get(current_level, "")}</p>
                <button onclick="document.getElementById('help-tooltip').style.display='none'" 
                    style="background: none; border: none; color: white; 
                    position: absolute; top: 5px; right: 5px; cursor: pointer; font-size: 14px;">×</button>
            </div>
            """
            
            script += help_html
        
        return script
    
    def _style_nodes_and_edges(self, net: Network, knowledge_graph: Dict[str, Any]) -> None:
        """
        Apply styling to nodes and edges in the network.
        
        Args:
            net (Network): The Pyvis network
            knowledge_graph (Dict[str, Any]): The knowledge graph or subgraph
        """
        # Get color schemes
        hierarchy_colors = self._get_hierarchy_colors(knowledge_graph)
        
        # Define shapes for hierarchy levels
        level_shapes = {
            "root": "diamond",     # Root nodes (domains, fields)
            "trunk": "dot",        # Trunk nodes (theories, concepts)
            "branch": "box",       # Branch nodes (methods, techniques)
            "leaf": "star",        # Leaf/Fruit nodes (applications, examples)
            "resource": "triangle" # Supporting resources
        }
        
        # Set node properties
        for node in net.nodes:
            # Find the corresponding entity in the knowledge graph
            entity = None
            for e in knowledge_graph.get("entities", []):
                if e["id"] == node["id"]:
                    entity = e
                    break
                    
            if entity:
                # Set node properties based on hierarchy level
                hierarchy_level = entity.get("hierarchy_level", "branch")
                
                # Set node shape
                node["shape"] = level_shapes.get(hierarchy_level, "dot")
                
                # Set node color based on hierarchy level
                node["color"] = {
                    "border": self._darken_color(hierarchy_colors.get(hierarchy_level, "#d2e5ff"), 0.4),
                    "background": hierarchy_colors.get(hierarchy_level, "#d2e5ff"),
                    "highlight": {
                        "border": self._darken_color(hierarchy_colors.get(hierarchy_level, "#d2e5ff"), 0.5),
                        "background": self._brighten_color(hierarchy_colors.get(hierarchy_level, "#d2e5ff"), 0.2)
                    },
                    "hover": {
                        "border": self._darken_color(hierarchy_colors.get(hierarchy_level, "#d2e5ff"), 0.5),
                        "background": self._brighten_color(hierarchy_colors.get(hierarchy_level, "#d2e5ff"), 0.1)
                    }
                }
                
                # Set node size based on importance
                importance = entity.get("properties", {}).get("importance", 5)
                node["size"] = 24 + (importance * 3)
                
                # Set node font size based on hierarchy level
                if hierarchy_level == "root":
                    node["font"] = {"size": 22, "face": "Tahoma", "bold": True}
                elif hierarchy_level == "trunk":
                    node["font"] = {"size": 20, "face": "Tahoma", "bold": True}
                elif hierarchy_level == "branch":
                    node["font"] = {"size": 18, "face": "Tahoma"}
                else:
                    node["font"] = {"size": 16, "face": "Tahoma"}
                
                # Create a more informative tooltip with HTML formatting
                node["title"] = self._create_enhanced_node_tooltip(entity)
                
                # Set grouping for better visualization
                node["group"] = hierarchy_level
                
                # Set custom physics for different hierarchy levels
                if hierarchy_level == "root":
                    node["fixed"] = {"y": True}  # Fix root nodes at the top
        
        # Set edge properties with improved visibility
        for edge in net.edges:
            # Find the corresponding relationship in the knowledge graph
            rel = None
            for r in knowledge_graph.get("relationships", []):
                if r["source"] == edge["from"] and r["target"] == edge["to"]:
                    rel = r
                    break
                    
            if rel:
                # Get relationship type and apply appropriate style
                rel_type = rel.get("type", "related_to")
                
                # Define relationship type styles
                rel_colors = {
                    "contains": "#0077b6",      # Dark blue
                    "is_part_of": "#0077b6",    # Dark blue
                    "has_part": "#0077b6",      # Dark blue
                    "implements": "#00b4d8",    # Medium blue
                    "applies": "#90e0ef",       # Light blue
                    "same_as": "#023e8a",       # Deep blue
                    "similar_to": "#48cae4",    # Teal blue
                    "progression": "#adb5bd",   # Gray
                    "leads_to": "#adb5bd",      # Gray
                    "related_to": "#666666"     # Dark gray
                }
                
                # Set edge color and style
                edge["color"] = rel_colors.get(rel_type, "#666666")
                
                # Set edge width based on relationship strength
                strength = rel.get("properties", {}).get("strength", 0.5)
                edge["width"] = 1 + (strength * 2)
                
                # Style bidirectional/hierarchical relationships differently
                is_bidirectional = rel.get("properties", {}).get("bidirectional", False)
                is_hierarchical = rel.get("properties", {}).get("hierarchical", False)
                
                if is_bidirectional:
                    edge["arrows"] = {"to": {"enabled": True, "scaleFactor": 0.8}, "from": {"enabled": True, "scaleFactor": 0.8}}
                else:
                    edge["arrows"] = {"to": {"enabled": True, "scaleFactor": 1.0}}
                
                if not is_hierarchical and rel_type in ["related_to", "similar_to", "same_as"]:
                    edge["dashes"] = [5, 2]
                
                # Set edge label and tooltip
                edge["label"] = rel_type.replace("_", " ")
                
                # Create tooltip for the edge
                description = rel.get("properties", {}).get("description", "")
                if description:
                    edge["title"] = f"<div><strong>{rel_type.replace('_', ' ').title()}</strong>: {description}</div>"
    
    def _set_hierarchical_options(self, net: Network) -> None:
        """
        Set hierarchical layout options for the network.
        
        Args:
            net (Network): pyvis Network object
        """
        # Enhanced hierarchical layout settings for better visualization
        options = {
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "UD",  # Top to bottom layout
                    "sortMethod": "directed",
                    "nodeSpacing": 180,
                    "levelSeparation": 200,
                    "treeSpacing": 250,
                    "blockShifting": True,
                    "edgeMinimization": True
                }
            },
            "physics": {
                "enabled": True,
                "hierarchicalRepulsion": {
                    "centralGravity": 0.0,
                    "springLength": 200,
                    "springConstant": 0.02,
                    "nodeDistance": 200,
                    "damping": 0.09
                },
                "minVelocity": 0.75,
                "solver": "hierarchicalRepulsion"
            },
            "interaction": {
                "navigationButtons": True,
                "keyboard": True,
                "hover": True,
                "tooltipDelay": 200,
                "hideEdgesOnDrag": False,
                "multiselect": True
            },
            "edges": {
                "smooth": {
                    "type": "cubicBezier",
                    "forceDirection": "vertical",
                    "roundness": 0.65
                },
                "arrows": {
                    "to": {
                        "enabled": True,
                        "scaleFactor": 0.8
                    }
                },
                "font": {
                    "size": 12,
                    "strokeWidth": 0,
                    "align": "middle"
                },
                "hoverWidth": 2
            },
            "nodes": {
                "font": {
                    "strokeWidth": 0
                },
                "scaling": {
                    "min": 20,
                    "max": 40
                },
                "shadow": {
                    "enabled": True,
                    "size": 5
                }
            }
        }
        
        # Add the network options to the pyvis Network object
        net.set_options(json.dumps(options))
        
        # Instead of using add_js_code which doesn't exist, we'll add the initialization script
        # to the _append_html_to_file method which will inject it into the HTML
    
    def _create_navigation_controls(
        self,
        title: str,
        description: str,
        parent: Optional[str] = None,
        level: Union[str, int] = 1,
        level_name: Optional[str] = None,
        knowledge_graph: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create navigation controls HTML for the visualization.
        
        Args:
            title (str): Title for the visualization
            description (str): Description of the visualization
            parent (Optional[str]): Name of the parent visualization, or None if at top level
            level (Union[str, int]): Current hierarchy level (1=overview, 2=module, 3=topic)
            level_name (Optional[str]): Custom name for the current level
            knowledge_graph (Optional[Dict[str, Any]]): The knowledge graph
            
        Returns:
            str: HTML for navigation controls
        """
        # Ensure level is a string for comparison
        level_str = str(level) if not isinstance(level, str) else level
        
        # Set level names based on the current level
        level_names = {
            "1": "Overview",
            "2": "Modules",
            "3": level_name or "Topics"
        }
        
        # Generate navigation dots for the hierarchy levels
        dots_html = ""
        for lvl in ["1", "2", "3"]:
            active_class = "active" if lvl == level_str else ""
            dots_html += f'<div class="nav-dot {active_class}" data-level="{lvl}">{level_names.get(lvl, "Level " + lvl)}</div>'
        
        # Create buttons for parent levels if not at the overview level
        buttons_html = ""
        if level_str != '1':  # Not at the overview level
            buttons_html = f"""
            <div class="breadcrumbs">
                <a href="knowledge_graph_overview.html" class="breadcrumb-link">Overview</a>
                {f'<span class="breadcrumb-separator">›</span> {parent}' if parent else ''}
            </div>
            """
        
        # Create the navigation controls HTML
        html = f"""
        <div class="navigation-controls">
            <div class="nav-header">
                <h1>{title}</h1>
                <p>{description}</p>
            </div>
            
            <div class="nav-levels">
                {dots_html}
            </div>
            
            {buttons_html}
        </div>
        
        <style>
            .navigation-controls {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 10px 20px;
                z-index: 1000;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            
            .nav-header {{
                margin-bottom: 15px;
            }}
            
            .nav-header h1 {{
                margin: 0 0 5px 0;
                font-size: 1.5rem;
                color: #333;
            }}
            
            .nav-header p {{
                margin: 0;
                color: #666;
                font-size: 0.9rem;
            }}
            
            .nav-levels {{
                display: flex;
                gap: 15px;
                margin-bottom: 10px;
            }}
            
            .nav-dot {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: auto;
                min-width: 80px;
                height: 30px;
                padding: 0 10px;
                border-radius: 15px;
                background-color: #dee2e6;
                color: #495057;
                font-size: 0.8rem;
                font-weight: bold;
                position: relative;
            }}
            
            .nav-dot::before {{
                content: '';
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: currentColor;
                margin-right: 5px;
            }}
            
            .nav-dot.active {{
                background-color: #336699;
                color: white;
            }}
            
            .breadcrumbs {{
                font-size: 0.85rem;
                color: #6c757d;
            }}
            
            .breadcrumb-link {{
                color: #336699;
                text-decoration: none;
            }}
            
            .breadcrumb-link:hover {{
                text-decoration: underline;
            }}
            
            .breadcrumb-separator {{
                margin: 0 5px;
            }}
        </style>
        """
        
        return html
    
    def _append_html_to_file(self, html_file: str, html_content: str, element_id: str) -> None:
        """
        Append HTML content to an existing HTML file.
        
        Args:
            html_file (str): Path to the HTML file
            html_content (str): HTML content to append
            element_id (str): ID for the appended HTML element
        """
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(html_file), exist_ok=True)
            
            logging.info(f"Appending HTML content to {html_file}")
            
            # Read existing content if file exists
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = "<!DOCTYPE html>\n<html>\n<head>\n<title>Knowledge Graph</title>\n</head>\n<body>\n</body>\n</html>"
            
            # Add CSS to ensure the network container is visible
            network_css = """
<style>
#mynetwork {
    width: 100% !important;
    height: 85vh !important;
    position: relative !important;
    z-index: 999 !important; /* Higher z-index to ensure visibility */
    background-color: #FFFFFF !important;
    border: 1px solid lightgray !important;
    display: block !important;
    margin-top: 80px !important;
}
</style>
"""
            
            # Add script to make sure the network is visible
            network_script = """
<script>
// Make sure the network container is visible and correctly positioned
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('mynetwork');
    if (container) {
        // Set proper dimensions and styles
        container.style.width = '100%';
        container.style.height = '85vh';
        container.style.position = 'relative';
        container.style.zIndex = '999'; // Higher z-index to ensure visibility
        container.style.background = '#FFFFFF';
        container.style.marginTop = '80px';
        container.style.border = '1px solid lightgray';
        container.style.display = 'block'; // Ensure it's displayed
        
        // Force redraw after layout
        setTimeout(function() {
            if (typeof drawGraph === 'function') {
                console.log("Forcing redraw");
                drawGraph();
            }
            
            // Apply fit to view after a delay
            setTimeout(function() {
                if (window.network) {
                    console.log("Fitting network to view");
                    window.network.fit();
                }
            }, 500);
        }, 800);
    }
});
</script>
"""
            
            # Check if we need to inject the CSS and script
            if "</head>" in content:
                if "Make sure the network container is visible" not in content:
                    content = content.replace("</head>", f"{network_script}</head>")
                if "#mynetwork" not in content or "z-index: 999" not in content:
                    content = content.replace("</head>", f"{network_css}</head>")
            
            # Append the HTML content before the closing body tag
            content = content.replace("</body>", f"{html_content}</body>")
            
            # Write the content back to the file
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"Successfully appended HTML content to {html_file}")
        except Exception as e:
            logging.error(f"Error appending HTML content to {html_file}: {str(e)}")
    
    def _get_hierarchy_colors(self, knowledge_graph: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate color mappings for hierarchy levels.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph
            
        Returns:
            Dict[str, str]: Mapping of hierarchy levels to colors
        """
        return {
            "root": "#003366",     # Dark blue for roots (foundation)
            "trunk": "#336699",    # Medium blue for trunk (theories)
            "branch": "#66A3D2",   # Light blue for branches (methods)
            "leaf": "#99CC99",     # Green for leaves/fruits (applications)
            "resource": "#D6A5C9"  # Purple for resources
        }

    def _create_hierarchical_views_data(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create hierarchical views data of the knowledge graph for multi-level visualization.
        
        Args:
            knowledge_graph (Dict[str, Any]): The knowledge graph
            
        Returns:
            Dict[str, Any]: Dictionary with different views of the knowledge graph
        """
        # Initialize views
        views = {
            "overview": {"entities": [], "relationships": []},
            "modules": {},  # module_id -> {entities, relationships}
            "topics": {}    # topic_id -> {entities, relationships}
        }
        
        # Get all entities by hierarchy level
        entities_by_level = {
            "root": [],
            "trunk": [],
            "branch": [],
            "leaf": [],
            "resource": []
        }
        
        # Group entities by hierarchy level
        for entity in knowledge_graph.get("entities", []):
            level = entity.get("hierarchy_level", "branch")
            if level in entities_by_level:
                entities_by_level[level].append(entity)
        
        # Create overview (Level 1): root + trunk entities
        views["overview"]["entities"] = entities_by_level["root"] + entities_by_level["trunk"]
        
        # Filter relationships for overview
        overview_entity_ids = {entity["id"] for entity in views["overview"]["entities"]}
        views["overview"]["relationships"] = self._filter_relationships(
            knowledge_graph.get("relationships", []),
            overview_entity_ids,
            limit_per_node=self.fibonacci_sequence[3]  # Use Fibonacci sequence for limiting relationships
        )
        
        # Create module views (Level 2): a trunk entity + its directly connected branch entities
        for trunk_entity in entities_by_level["trunk"]:
            module_id = trunk_entity["id"]
            module_view = {"entities": [trunk_entity], "relationships": []}
            
            # Find all branch entities directly connected to this trunk entity
            connected_branches = self._get_connected_entities(
                knowledge_graph.get("relationships", []),
                module_id,
                target_level="branch",
                knowledge_graph=knowledge_graph
            )
            
            # Add the connected branch entities to the module view
            for branch_id in connected_branches:
                branch_entity = self._find_entity_by_id(knowledge_graph, branch_id)
                if branch_entity:
                    module_view["entities"].append(branch_entity)
            
            # Filter relationships for this module view
            module_entity_ids = {entity["id"] for entity in module_view["entities"]}
            module_view["relationships"] = self._filter_relationships(
                knowledge_graph.get("relationships", []),
                module_entity_ids,
                limit_per_node=self.fibonacci_sequence[4]  # Use Fibonacci sequence for limiting relationships
            )
            
            views["modules"][module_id] = module_view
        
        # Create topic views (Level 3): a branch entity + its directly connected leaf/resource entities
        for branch_entity in entities_by_level["branch"]:
            topic_id = branch_entity["id"]
            topic_view = {"entities": [branch_entity], "relationships": []}
            
            # Find all leaf/resource entities directly connected to this branch entity
            connected_leaves = self._get_connected_entities(
                knowledge_graph.get("relationships", []),
                topic_id,
                target_level=["leaf", "resource"],
                knowledge_graph=knowledge_graph
            )
            
            # Add the connected leaf/resource entities to the topic view
            for leaf_id in connected_leaves:
                leaf_entity = self._find_entity_by_id(knowledge_graph, leaf_id)
                if leaf_entity:
                    topic_view["entities"].append(leaf_entity)
            
            # Filter relationships for this topic view
            topic_entity_ids = {entity["id"] for entity in topic_view["entities"]}
            topic_view["relationships"] = self._filter_relationships(
                knowledge_graph.get("relationships", []),
                topic_entity_ids,
                limit_per_node=self.fibonacci_sequence[5]  # Use Fibonacci sequence for limiting relationships
            )
            
            views["topics"][topic_id] = topic_view
        
        return views