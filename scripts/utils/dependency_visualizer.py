#!/usr/bin/env python3
"""
Streamlit Dependency Visualization App for uqlab-streamlit project.

This app provides interactive visualization and querying of Python dependencies.

Usage:
    streamlit run dependency_visualizer.py
"""

import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from typing import Dict, List, Set, Optional
import networkx as nx
from collections import defaultdict


# Page configuration
st.set_page_config(
    page_title="Dependency Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


class DependencyVisualizer:
    """Handles loading and visualization of dependency data."""
    
    def __init__(self, data_file: str = "dependencies.json"):
        """Initialize visualizer with data file."""
        self.data_file = data_file
        self.data = None
        self.graph = None
        self.load_data()
    
    def load_data(self) -> bool:
        """Load dependency data from JSON file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except FileNotFoundError:
            return False
        except json.JSONDecodeError:
            return False
    
    def get_files_dataframe(self) -> pd.DataFrame:
        """Convert files data to pandas DataFrame."""
        if not self.data:
            return pd.DataFrame()
        
        rows = []
        for file_path, file_info in self.data['files'].items():
            local_imports = [
                imp['module'] for imp in file_info['imports'] 
                if imp['type'] == 'local'
            ]
            external_imports = [
                imp['module'] for imp in file_info['imports'] 
                if imp['type'] == 'external'
            ]
            
            rows.append({
                'File': file_path,
                'Module': file_info['module_name'],
                'Category': file_info['category'],
                'Local Imports': len(local_imports),
                'External Imports': len(external_imports),
                'Imported By': len(file_info['imported_by']),
                'Local Import List': ', '.join(local_imports[:5]) + ('...' if len(local_imports) > 5 else ''),
                'External Import List': ', '.join(external_imports[:5]) + ('...' if len(external_imports) > 5 else ''),
            })
        
        return pd.DataFrame(rows)
    
    def get_imports_dataframe(self) -> pd.DataFrame:
        """Get detailed imports as DataFrame."""
        if not self.data:
            return pd.DataFrame()
        
        rows = []
        for file_path, file_info in self.data['files'].items():
            for imp in file_info['imports']:
                rows.append({
                    'Source File': file_path,
                    'Source Module': file_info['module_name'],
                    'Source Category': file_info['category'],
                    'Imported Module': imp['module'],
                    'Import Type': imp['type'],
                    'Line': imp['line'],
                    'Is Relative': imp['is_relative'],
                    'Import Statement': imp['import_type']
                })
        
        return pd.DataFrame(rows)
    
    def build_networkx_graph(self, filter_category: Optional[str] = None) -> nx.DiGraph:
        """Build NetworkX graph from dependency data."""
        G = nx.DiGraph()
        
        if not self.data:
            return G
        
        # Add nodes
        for file_path, file_info in self.data['files'].items():
            if filter_category and file_info['category'] != filter_category:
                continue
            
            G.add_node(
                file_path,
                module=file_info['module_name'],
                category=file_info['category'],
                local_imports=len([imp for imp in file_info['imports'] if imp['type'] == 'local']),
                imported_by=len(file_info['imported_by'])
            )
        
        # Add edges
        for file_path, file_info in self.data['files'].items():
            if filter_category and file_info['category'] != filter_category:
                continue
            
            for imp in file_info['imports']:
                if imp['type'] == 'local':
                    # Find target files
                    for target_path, target_info in self.data['files'].items():
                        if target_info['module_name'] == imp['module']:
                            if filter_category and target_info['category'] != filter_category:
                                continue
                            G.add_edge(file_path, target_path, module=imp['module'])
        
        return G
    
    def create_plotly_graph(self, filter_category: Optional[str] = None,
                           highlight_cross_boundary: bool = False) -> go.Figure:
        """Create interactive Plotly graph visualization."""
        if not self.data or 'graph' not in self.data:
            return go.Figure()
        
        graph_data = self.data['graph']
        
        # Filter nodes and edges
        if filter_category:
            filtered_nodes = [
                node for node in graph_data['nodes']
                if node['category'] == filter_category
            ]
            node_ids = {node['id'] for node in filtered_nodes}
            filtered_edges = [
                edge for edge in graph_data['edges']
                if edge['source'] in node_ids and edge['target'] in node_ids
            ]
        else:
            filtered_nodes = graph_data['nodes']
            filtered_edges = graph_data['edges']
        
        # Build NetworkX graph for layout
        G = nx.DiGraph()
        for node in filtered_nodes:
            G.add_node(node['id'])
        for edge in filtered_edges:
            G.add_edge(edge['source'], edge['target'])
        
        # Calculate layout
        if len(G.nodes()) > 0:
            try:
                pos = nx.spring_layout(G, k=2, iterations=50)
            except:
                pos = {node: (0, 0) for node in G.nodes()}
        else:
            pos = {}
        
        # Create edge traces
        edge_traces = []
        
        # Regular edges
        regular_edges = [e for e in filtered_edges if not (highlight_cross_boundary and e.get('is_cross_boundary', False))]
        if regular_edges:
            edge_x = []
            edge_y = []
            for edge in regular_edges:
                x0, y0 = pos.get(edge['source'], (0, 0))
                x1, y1 = pos.get(edge['target'], (0, 0))
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_traces.append(go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines',
                name='Dependencies'
            ))
        
        # Cross-boundary edges (highlighted)
        if highlight_cross_boundary:
            cross_edges = [e for e in filtered_edges if e.get('is_cross_boundary', False)]
            if cross_edges:
                edge_x = []
                edge_y = []
                for edge in cross_edges:
                    x0, y0 = pos.get(edge['source'], (0, 0))
                    x1, y1 = pos.get(edge['target'], (0, 0))
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                edge_traces.append(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=2, color='red', dash='dash'),
                    hoverinfo='none',
                    mode='lines',
                    name='Cross-boundary'
                ))
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []
        
        category_colors = {
            'frontend': '#FF6B6B',
            'backend': '#4ECDC4',
            'shared': '#95E1D3',
            'scripts': '#F38181',
            'tests': '#AA96DA',
            'notebooks': '#FCBAD3'
        }
        
        for node in filtered_nodes:
            x, y = pos.get(node['id'], (0, 0))
            node_x.append(x)
            node_y.append(y)
            
            # Create hover text
            hover_text = f"<b>{node['label']}</b><br>"
            hover_text += f"Module: {node['module']}<br>"
            hover_text += f"Category: {node['category']}<br>"
            hover_text += f"Local imports: {node['local_imports']}<br>"
            hover_text += f"External imports: {node['external_imports']}<br>"
            hover_text += f"Imported by: {node['imported_by_count']} files"
            node_text.append(hover_text)
            
            # Color by category
            node_color.append(category_colors.get(node['category'], '#999'))
            
            # Size by importance (imported_by_count)
            size = 10 + min(node['imported_by_count'] * 2, 30)
            node_size.append(size)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                color=node_color,
                size=node_size,
                line=dict(width=2, color='white')
            ),
            name='Files'
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title='Dependency Graph',
            showlegend=True,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=700,
            plot_bgcolor='#f8f9fa'
        )
        
        return fig
    
    def query_where_imported(self, module_name: str) -> List[Dict]:
        """Find all files that import a given module."""
        if not self.data:
            return []
        
        results = []
        for file_path, file_info in self.data['files'].items():
            for imp in file_info['imports']:
                if module_name in imp['module'] or imp['module'] in module_name:
                    results.append({
                        'file': file_path,
                        'module': file_info['module_name'],
                        'category': file_info['category'],
                        'import': imp['module'],
                        'line': imp['line'],
                        'type': imp['type']
                    })
        
        return results
    
    def query_what_imports(self, file_path: str) -> List[Dict]:
        """Find all imports from a given file."""
        if not self.data or file_path not in self.data['files']:
            return []
        
        file_info = self.data['files'][file_path]
        return [
            {
                'module': imp['module'],
                'type': imp['type'],
                'line': imp['line'],
                'import_type': imp['import_type'],
                'is_relative': imp['is_relative']
            }
            for imp in file_info['imports']
        ]
    
    def get_import_chain(self, start_file: str, max_depth: int = 3) -> List[List[str]]:
        """Get import chains starting from a file."""
        if not self.data or start_file not in self.data['files']:
            return []
        
        chains = []
        visited = set()
        
        def dfs(file_path: str, chain: List[str], depth: int):
            if depth > max_depth or file_path in visited:
                return
            
            visited.add(file_path)
            chain.append(file_path)
            
            if file_path in self.data['files']:
                file_info = self.data['files'][file_path]
                local_imports = [
                    imp['module'] for imp in file_info['imports']
                    if imp['type'] == 'local'
                ]
                
                if not local_imports:
                    chains.append(chain.copy())
                else:
                    for imp_module in local_imports:
                        # Find file for this module
                        for target_path, target_info in self.data['files'].items():
                            if target_info['module_name'] == imp_module:
                                dfs(target_path, chain.copy(), depth + 1)
            
            visited.remove(file_path)
        
        dfs(start_file, [], 0)
        return chains


def main():
    """Main Streamlit app."""
    st.title("🔍 Python Dependency Analyzer")
    st.markdown("Interactive visualization and analysis of Python dependencies in uqlab-streamlit")
    
    # Initialize visualizer
    viz = DependencyVisualizer()
    
    if not viz.data:
        st.error("⚠️ No dependency data found!")
        st.info("Run the analyzer first: `python analyze_dependencies.py`")
        return
    
    # Sidebar
    st.sidebar.header("📊 Overview")
    metadata = viz.data.get('metadata', {})
    stats = viz.data.get('statistics', {})
    
    st.sidebar.metric("Total Files", metadata.get('total_files', 0))
    st.sidebar.metric("Local Modules", metadata.get('total_local_modules', 0))
    st.sidebar.metric("Circular Dependencies", metadata.get('circular_dependencies_count', 0))
    
    if stats.get('by_category'):
        st.sidebar.subheader("Files by Category")
        for category, count in sorted(stats['by_category'].items()):
            st.sidebar.text(f"{category}: {count}")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Files Table", 
        "🔗 Imports Table",
        "📊 Graph Visualization",
        "🔍 Query Tool",
        "📈 Statistics"
    ])
    
    # Tab 1: Files Table
    with tab1:
        st.header("Files Overview")
        
        df = viz.get_files_dataframe()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            categories = ['All'] + sorted(df['Category'].unique().tolist())
            selected_category = st.selectbox("Filter by Category", categories)
        
        with col2:
            min_imports = st.number_input("Min Local Imports", min_value=0, value=0)
        
        with col3:
            search_term = st.text_input("Search files", "")
        
        # Apply filters
        filtered_df = df.copy()
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['Category'] == selected_category]
        if min_imports > 0:
            filtered_df = filtered_df[filtered_df['Local Imports'] >= min_imports]
        if search_term:
            filtered_df = filtered_df[
                filtered_df['File'].str.contains(search_term, case=False) |
                filtered_df['Module'].str.contains(search_term, case=False)
            ]
        
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=500
        )
        
        st.download_button(
            "📥 Download CSV",
            filtered_df.to_csv(index=False),
            "dependencies_files.csv",
            "text/csv"
        )
    
    # Tab 2: Imports Table
    with tab2:
        st.header("Detailed Imports")
        
        imports_df = viz.get_imports_dataframe()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            import_types = ['All'] + sorted(imports_df['Import Type'].unique().tolist())
            selected_import_type = st.selectbox("Filter by Import Type", import_types)
        
        with col2:
            source_categories = ['All'] + sorted(imports_df['Source Category'].unique().tolist())
            selected_source_cat = st.selectbox("Filter by Source Category", source_categories)
        
        with col3:
            search_import = st.text_input("Search imports", "")
        
        # Apply filters
        filtered_imports = imports_df.copy()
        if selected_import_type != 'All':
            filtered_imports = filtered_imports[filtered_imports['Import Type'] == selected_import_type]
        if selected_source_cat != 'All':
            filtered_imports = filtered_imports[filtered_imports['Source Category'] == selected_source_cat]
        if search_import:
            filtered_imports = filtered_imports[
                filtered_imports['Imported Module'].str.contains(search_import, case=False) |
                filtered_imports['Source File'].str.contains(search_import, case=False)
            ]
        
        st.dataframe(
            filtered_imports,
            use_container_width=True,
            height=500
        )
        
        st.download_button(
            "📥 Download CSV",
            filtered_imports.to_csv(index=False),
            "dependencies_imports.csv",
            "text/csv"
        )
    
    # Tab 3: Graph Visualization
    with tab3:
        st.header("Dependency Graph")
        
        col1, col2 = st.columns(2)
        with col1:
            graph_categories = ['All'] + sorted(stats.get('by_category', {}).keys())
            graph_filter = st.selectbox("Filter graph by category", graph_categories, key='graph_cat')
        
        with col2:
            highlight_cross = st.checkbox("Highlight cross-boundary imports", value=True)
        
        filter_cat = None if graph_filter == 'All' else graph_filter
        
        fig = viz.create_plotly_graph(
            filter_category=filter_cat,
            highlight_cross_boundary=highlight_cross
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 **Tip**: Node size indicates how many files import it. Hover over nodes for details.")
    
    # Tab 4: Query Tool
    with tab4:
        st.header("Dependency Query Tool")
        
        query_type = st.radio(
            "Query Type",
            ["Where is X imported?", "What does X import?", "Show import chain"]
        )
        
        if query_type == "Where is X imported?":
            st.subheader("Find all files that import a module")
            
            module_search = st.text_input(
                "Enter module name (e.g., 'batch_experiments', 'ui_components')",
                key='where_imported'
            )
            
            if module_search:
                results = viz.query_where_imported(module_search)
                
                if results:
                    st.success(f"Found {len(results)} imports of '{module_search}'")
                    
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True)
                else:
                    st.warning(f"No imports found for '{module_search}'")
        
        elif query_type == "What does X import?":
            st.subheader("Show all imports from a file")
            
            files_list = sorted(viz.data['files'].keys())
            selected_file = st.selectbox("Select file", files_list, key='what_imports')
            
            if selected_file:
                results = viz.query_what_imports(selected_file)
                
                if results:
                    st.success(f"File '{selected_file}' has {len(results)} imports")
                    
                    # Separate by type
                    local = [r for r in results if r['type'] == 'local']
                    external = [r for r in results if r['type'] == 'external']
                    stdlib = [r for r in results if r['type'] == 'stdlib']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Local", len(local))
                    with col2:
                        st.metric("External", len(external))
                    with col3:
                        st.metric("Stdlib", len(stdlib))
                    
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True)
                else:
                    st.info(f"File '{selected_file}' has no imports")
        
        else:  # Import chain
            st.subheader("Show import chains")
            
            files_list = sorted(viz.data['files'].keys())
            chain_file = st.selectbox("Select starting file", files_list, key='chain')
            max_depth = st.slider("Max chain depth", 1, 5, 3)
            
            if chain_file:
                chains = viz.get_import_chain(chain_file, max_depth)
                
                if chains:
                    st.success(f"Found {len(chains)} import chains")
                    
                    for idx, chain in enumerate(chains[:10], 1):
                        st.text(f"{idx}. {' → '.join(chain)}")
                    
                    if len(chains) > 10:
                        st.info(f"... and {len(chains) - 10} more chains")
                else:
                    st.info("No import chains found")
    
    # Tab 5: Statistics
    with tab5:
        st.header("Dependency Statistics")
        
        if stats:
            # Import type distribution
            st.subheader("Import Type Distribution")
            if stats.get('by_import_type'):
                import_type_df = pd.DataFrame([
                    {'Type': k, 'Count': v}
                    for k, v in stats['by_import_type'].items()
                ])
                fig = px.pie(import_type_df, values='Count', names='Type', 
                           title='Imports by Type')
                st.plotly_chart(fig, use_container_width=True)
            
            # Category distribution
            st.subheader("Files by Category")
            if stats.get('by_category'):
                category_df = pd.DataFrame([
                    {'Category': k, 'Count': v}
                    for k, v in stats['by_category'].items()
                ])
                fig = px.bar(category_df, x='Category', y='Count',
                           title='Files by Category')
                st.plotly_chart(fig, use_container_width=True)
            
            # Most imported files
            st.subheader("Most Imported Files")
            if stats.get('most_imported'):
                most_imported_df = pd.DataFrame(
                    stats['most_imported'],
                    columns=['File', 'Import Count']
                )
                st.dataframe(most_imported_df, use_container_width=True)
            
            # Files with most dependencies
            st.subheader("Files with Most Dependencies")
            if stats.get('most_dependencies'):
                most_deps_df = pd.DataFrame(
                    stats['most_dependencies'],
                    columns=['File', 'Dependency Count']
                )
                st.dataframe(most_deps_df, use_container_width=True)
            
            # Cross-boundary imports
            st.subheader("Cross-Boundary Analysis")
            cross_boundary = stats.get('cross_boundary_imports', 0)
            st.metric("Frontend ↔ Backend Imports", cross_boundary)
            
            if cross_boundary > 0:
                st.warning("⚠️ Cross-boundary imports detected. Consider reviewing architecture.")
        
        # Circular dependencies
        if viz.data.get('circular_dependencies'):
            st.subheader("Circular Dependencies")
            st.error(f"⚠️ Found {len(viz.data['circular_dependencies'])} circular dependency chains")
            
            for idx, cycle in enumerate(viz.data['circular_dependencies'][:5], 1):
                st.text(f"{idx}. {' → '.join(cycle)}")
            
            if len(viz.data['circular_dependencies']) > 5:
                st.info(f"... and {len(viz.data['circular_dependencies']) - 5} more")


if __name__ == '__main__':
    main()

# Made with Bob
