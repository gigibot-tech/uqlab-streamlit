"""Interactive Streamlit Dashboard for UQ Classification Experiments.

This app provides an interactive interface for exploring training results,
visualizing decision boundaries, and comparing model checkpoints across epochs.

Features:
- Experiment selection and metadata display
- Training metrics visualization (loss, accuracy)
- Decision boundary explorer with epoch navigation
- Checkpoint comparison in grid layout
- Interactive controls and data export

Usage:
    streamlit run uq_classification/streamlit_app.py
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="UQ Classification Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .experiment-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .checkpoint-info {
        font-size: 0.9rem;
        color: #555;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Data Loading Functions
# ============================================================================

@st.cache_data
def load_experiments(experiments_dir: str = "experiments") -> Dict[str, List[str]]:
    """Load all available experiments and their runs.
    
    Args:
        experiments_dir: Directory containing experiment data
        
    Returns:
        Dictionary mapping experiment names to list of run IDs
    """
    exp_path = Path(experiments_dir)
    if not exp_path.exists():
        return {}
    
    experiments = {}
    for exp_dir in exp_path.iterdir():
        if exp_dir.is_dir():
            runs = [f.stem for f in exp_dir.glob("*.json")]
            if runs:
                experiments[exp_dir.name] = sorted(runs, reverse=True)
    
    return experiments


@st.cache_data
def load_experiment_data(experiment_name: str, run_id: str, 
                         experiments_dir: str = "experiments") -> Optional[Dict]:
    """Load experiment data from JSON file.
    
    Args:
        experiment_name: Name of the experiment
        run_id: Run identifier
        experiments_dir: Directory containing experiment data
        
    Returns:
        Dictionary with experiment data or None if not found
    """
    filepath = Path(experiments_dir) / experiment_name / f"{run_id}.json"
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load experiment data: {e}")
        return None


@st.cache_data
def get_checkpoint_images(experiment_name: str, run_id: str,
                          viz_dir: str = "visualizations") -> List[Tuple[int, Path]]:
    """Get all checkpoint visualization images for an experiment.
    
    Args:
        experiment_name: Name of the experiment
        run_id: Run identifier
        viz_dir: Directory containing visualizations
        
    Returns:
        List of (epoch, image_path) tuples sorted by epoch
    """
    viz_path = Path(viz_dir) / experiment_name / run_id
    
    if not viz_path.exists():
        return []
    
    images = []
    for img_file in viz_path.glob("epoch_*.png"):
        try:
            # Extract epoch number from filename (e.g., "epoch_10.png")
            epoch = int(img_file.stem.split('_')[1])
            images.append((epoch, img_file))
        except (ValueError, IndexError):
            continue
    
    return sorted(images, key=lambda x: x[0])


def extract_metrics_dataframe(metrics: Dict) -> pd.DataFrame:
    """Convert metrics dictionary to pandas DataFrame.
    
    Args:
        metrics: Dictionary of metrics with step/value pairs
        
    Returns:
        DataFrame with columns for each metric
    """
    if not metrics:
        return pd.DataFrame()
    
    # Build dataframe from metrics
    data = {}
    max_steps = 0
    
    for metric_name, values in metrics.items():
        if isinstance(values, list):
            steps = [v.get('step', i) for i, v in enumerate(values)]
            vals = [v.get('value', v) if isinstance(v, dict) else v for v in values]
            data[metric_name] = vals
            max_steps = max(max_steps, len(vals))
    
    # Ensure all metrics have same length
    for key in data:
        if len(data[key]) < max_steps:
            data[key].extend([None] * (max_steps - len(data[key])))
    
    df = pd.DataFrame(data)
    df.index.name = 'epoch'
    return df


# ============================================================================
# UI Components
# ============================================================================

def render_header():
    """Render the main header."""
    st.markdown('<div class="main-header">📊 UQ Classification Dashboard</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Explore training results and decision boundaries</div>', 
                unsafe_allow_html=True)


def render_experiment_selector(experiments: Dict[str, List[str]]) -> Tuple[Optional[str], Optional[str]]:
    """Render experiment and run selector in sidebar.
    
    Args:
        experiments: Dictionary of experiments and runs
        
    Returns:
        Tuple of (experiment_name, run_id) or (None, None)
    """
    st.sidebar.header("🔍 Experiment Selection")
    
    if not experiments:
        st.sidebar.warning("No experiments found. Run training first!")
        return None, None
    
    # Experiment selector
    experiment_names = list(experiments.keys())
    selected_exp = st.sidebar.selectbox(
        "Select Experiment",
        experiment_names,
        help="Choose an experiment to explore"
    )
    
    if not selected_exp:
        return None, None
    
    # Run selector
    runs = experiments[selected_exp]
    selected_run = st.sidebar.selectbox(
        "Select Run",
        runs,
        help="Choose a specific training run"
    )
    
    return selected_exp, selected_run


def render_experiment_metadata(data: Dict):
    """Render experiment metadata and configuration.
    
    Args:
        data: Experiment data dictionary
    """
    st.subheader("📋 Experiment Metadata")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Run ID", data.get('run_id', 'N/A'))
    
    with col2:
        st.metric("Experiment", data.get('experiment_name', 'N/A'))
    
    with col3:
        run_name = data.get('run_name', 'N/A')
        st.metric("Run Name", run_name if run_name else 'N/A')
    
    # Parameters in expandable section
    params = data.get('params', {})
    if params:
        with st.expander("⚙️ Hyperparameters", expanded=False):
            # Create a nice table for parameters
            param_df = pd.DataFrame([
                {"Parameter": k, "Value": v} 
                for k, v in params.items()
            ])
            st.dataframe(param_df, use_container_width=True, hide_index=True)


def render_metrics_summary(metrics: Dict):
    """Render summary metrics cards.
    
    Args:
        metrics: Dictionary of metrics
    """
    st.subheader("📈 Final Metrics")
    
    # Extract final values
    final_metrics = {}
    for metric_name, values in metrics.items():
        if isinstance(values, list) and values:
            last_val = values[-1]
            if isinstance(last_val, dict):
                final_metrics[metric_name] = last_val.get('value', 0)
            else:
                final_metrics[metric_name] = last_val
    
    # Display in columns
    cols = st.columns(min(len(final_metrics), 4))
    for idx, (name, value) in enumerate(final_metrics.items()):
        with cols[idx % len(cols)]:
            # Format value
            if isinstance(value, float):
                formatted_value = f"{value:.4f}"
            else:
                formatted_value = str(value)
            
            st.metric(
                label=name.replace('_', ' ').title(),
                value=formatted_value
            )


def render_training_curves(df: pd.DataFrame):
    """Render training curves (loss and accuracy).
    
    Args:
        df: DataFrame with metrics
    """
    st.subheader("📉 Training Curves")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Loss", "Accuracy", "All Metrics"])
    
    with tab1:
        loss_cols = [col for col in df.columns if 'loss' in col.lower()]
        if loss_cols:
            st.line_chart(df[loss_cols], use_container_width=True)
        else:
            st.info("No loss metrics found")
    
    with tab2:
        acc_cols = [col for col in df.columns if 'acc' in col.lower()]
        if acc_cols:
            st.line_chart(df[acc_cols], use_container_width=True)
        else:
            st.info("No accuracy metrics found")
    
    with tab3:
        if not df.empty:
            st.line_chart(df, use_container_width=True)
        else:
            st.info("No metrics available")


def render_decision_boundary_explorer(images: List[Tuple[int, Path]]):
    """Render decision boundary explorer with epoch slider.
    
    Args:
        images: List of (epoch, image_path) tuples
    """
    st.subheader("🎯 Decision Boundary Explorer")
    
    if not images:
        st.warning("No decision boundary visualizations found. "
                  "Run training with visualization enabled.")
        return
    
    # Epoch slider
    epochs = [epoch for epoch, _ in images]
    selected_epoch = st.slider(
        "Select Epoch",
        min_value=min(epochs),
        max_value=max(epochs),
        value=max(epochs),
        step=1 if len(epochs) > 1 else 1,
        help="Navigate through training epochs"
    )
    
    # Find image for selected epoch
    image_path = None
    for epoch, path in images:
        if epoch == selected_epoch:
            image_path = path
            break
    
    if image_path and image_path.exists():
        # Display image
        try:
            image = Image.open(image_path)
            st.image(image, use_column_width=True, 
                    caption=f"Decision Boundary at Epoch {selected_epoch}")
            
            # Image info
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📁 **File:** `{image_path.name}`")
            with col2:
                st.info(f"📊 **Epoch:** {selected_epoch}/{max(epochs)}")
            
        except Exception as e:
            st.error(f"Failed to load image: {e}")
    else:
        st.warning(f"Image not found for epoch {selected_epoch}")


def render_checkpoint_comparison(images: List[Tuple[int, Path]]):
    """Render checkpoint comparison grid.
    
    Args:
        images: List of (epoch, image_path) tuples
    """
    st.subheader("🔄 Checkpoint Comparison")
    
    if not images:
        st.warning("No checkpoints available for comparison")
        return
    
    # Checkpoint selector
    epochs = [epoch for epoch, _ in images]
    
    # Multi-select for epochs
    selected_epochs = st.multiselect(
        "Select Epochs to Compare",
        epochs,
        default=epochs[-3:] if len(epochs) >= 3 else epochs,
        help="Choose multiple epochs to compare side-by-side"
    )
    
    if not selected_epochs:
        st.info("Select at least one epoch to display")
        return
    
    # Grid layout
    cols_per_row = st.slider("Images per row", 1, 4, 2)
    
    # Display images in grid
    selected_images = [(e, p) for e, p in images if e in selected_epochs]
    
    for i in range(0, len(selected_images), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, (epoch, path) in enumerate(selected_images[i:i+cols_per_row]):
            with cols[j]:
                try:
                    image = Image.open(path)
                    st.image(image, use_column_width=True, 
                            caption=f"Epoch {epoch}")
                except Exception as e:
                    st.error(f"Failed to load epoch {epoch}: {e}")


def render_data_export(data: Dict, df: pd.DataFrame):
    """Render data export options.
    
    Args:
        data: Experiment data dictionary
        df: Metrics dataframe
    """
    st.subheader("💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export metrics as CSV
        if not df.empty:
            csv = df.to_csv(index=True)
            st.download_button(
                label="📥 Download Metrics (CSV)",
                data=csv,
                file_name=f"metrics_{data.get('run_id', 'unknown')}.csv",
                mime="text/csv",
                help="Download training metrics as CSV file"
            )
    
    with col2:
        # Export full data as JSON
        json_str = json.dumps(data, indent=2)
        st.download_button(
            label="📥 Download Full Data (JSON)",
            data=json_str,
            file_name=f"experiment_{data.get('run_id', 'unknown')}.json",
            mime="application/json",
            help="Download complete experiment data"
        )


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point."""
    
    # Render header
    render_header()
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Configuration")
    
    # Directory settings
    with st.sidebar.expander("📁 Directory Settings", expanded=False):
        experiments_dir = st.text_input(
            "Experiments Directory",
            value="experiments",
            help="Directory containing experiment JSON files"
        )
        viz_dir = st.text_input(
            "Visualizations Directory",
            value="visualizations",
            help="Directory containing decision boundary images"
        )
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data", help="Reload experiments from disk"):
        st.cache_data.clear()
        st.rerun()
    
    # Load experiments
    experiments = load_experiments(experiments_dir)
    
    # Experiment selector
    selected_exp, selected_run = render_experiment_selector(experiments)
    
    if not selected_exp or not selected_run:
        st.info("👈 Select an experiment from the sidebar to begin")
        
        # Show available experiments
        if experiments:
            st.subheader("Available Experiments")
            exp_summary = []
            for exp_name, runs in experiments.items():
                exp_summary.append({
                    "Experiment": exp_name,
                    "Runs": len(runs),
                    "Latest Run": runs[0] if runs else "N/A"
                })
            st.dataframe(pd.DataFrame(exp_summary), use_container_width=True, hide_index=True)
        
        return
    
    # Load experiment data
    data = load_experiment_data(selected_exp, selected_run, experiments_dir)
    
    if not data:
        st.error(f"Failed to load experiment data for {selected_exp}/{selected_run}")
        return
    
    # Main content area
    st.divider()
    
    # Metadata section
    render_experiment_metadata(data)
    
    st.divider()
    
    # Metrics section
    metrics = data.get('metrics', {})
    df = pd.DataFrame()  # Initialize df
    
    if metrics:
        render_metrics_summary(metrics)
        
        st.divider()
        
        # Training curves
        df = extract_metrics_dataframe(metrics)
        if not df.empty:
            render_training_curves(df)
    else:
        st.warning("No metrics found in experiment data")
    
    st.divider()
    
    # Decision boundary visualizations
    images = get_checkpoint_images(selected_exp, selected_run, viz_dir)
    
    if images:
        # Explorer
        render_decision_boundary_explorer(images)
        
        st.divider()
        
        # Comparison
        render_checkpoint_comparison(images)
    else:
        st.info("No decision boundary visualizations available for this experiment")
    
    st.divider()
    
    # Export section
    render_data_export(data, df if metrics else pd.DataFrame())
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>UQ Classification Dashboard | Made with ❤️ using Streamlit</p>
        <p style='font-size: 0.8rem;'>
            💡 Tip: Use the sidebar to navigate between experiments and configure settings
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

# Made with Bob