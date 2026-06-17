"""
Streamlit Dashboard for Uncertainty Quantification
Connects to the FastAPI backend to display dataset statistics and experiment results
"""

import sys
from pathlib import Path

# Ensure ``uqlab`` (under src/) and legacy top-level shims resolve before imports.
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC = _PROJECT_ROOT / "src"
for _path in (_SRC, _PROJECT_ROOT):
    _entry = str(_path)
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import streamlit as st
import requests
import pandas as pd
import os
from typing import Optional

# Import UI components
from ui_components import (
    build_base_experiment_config,
    render_batch_results,
    render_batch_sweep_config,
    render_batch_base_config,
    render_dataset_selection,
    render_configuration_progress,
    render_epistemic_config,
    render_aleatoric_config,
    render_dataset_comparison,
    render_model_config,
    render_training_config,
    render_evaluation_config,
    render_evaluation_strategy,
    render_roc_explanation,
    render_experiment_results,
    render_2d_sweep_config,
    render_2d_results_analysis,
    render_model_selector,
    render_model_inference_panel,
    render_data_overlap_analysis,
    render_experiment_type_validation,
    render_validation_summary,
    validate_sweep_configuration,
    render_unified_builder,
    render_hypothesis_validation_tab,
)

# Import UQ Benchmarks UI components (Phase 5)
from uqlab.ui_components.visualization.analysis.uq_benchmarks import render_uq_benchmarks_tab

# Import watsonx.ai cloud mode components
from uqlab.evaluation.classification.watsonx_streamlit import render_cloud_mode_toggle

# Custom CSS for glowing arrow animation
st.markdown("""
<style>
@keyframes glow-pulse {
    0%, 100% {
        opacity: 0.6;
        text-shadow: 0 0 5px #4CAF50, 0 0 10px #4CAF50;
    }
    50% {
        opacity: 1;
        text-shadow: 0 0 10px #4CAF50, 0 0 20px #4CAF50, 0 0 30px #4CAF50;
    }
}

.glowing-arrow {
    font-size: 2em;
    color: #4CAF50;
    animation: glow-pulse 2s ease-in-out infinite;
    text-align: center;
    margin: 10px 0;
}

.connection-box {
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%);
    border-left: 4px solid #4CAF50;
    padding: 12px;
    border-radius: 4px;
    margin: 10px 0;
}

.connection-text {
    color: #4CAF50;
    font-weight: 600;
    font-size: 0.9em;
}
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")  # Optional: for authenticated endpoints

# Page config
st.set_page_config(
    page_title="Uncertainty Quantification Dashboard",
    page_icon="📊",
    layout="wide"
)

def get_headers() -> dict:
    """Get request headers with optional authentication"""
    headers = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers

def fetch_dataset_stats(dataset_name: str = "cifar10n", noise_type: str = "worse_label") -> Optional[dict]:
    """Fetch dataset statistics from the backend API"""
    try:
        url = f"{API_BASE_URL}/api/v1/datasets/{dataset_name}/stats"
        params = {"noise_type": noise_type}
        response = requests.get(url, params=params, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch dataset stats: {str(e)}")
        return None

def main():
    st.title("🔬 Uncertainty Quantification Experiment Configuration")
    
    # ========== DATASET SELECTION & OVERVIEW (TOP OF PAGE) ==========
    st.markdown("### 📊 Dataset Selection & Overview")
    dataset_name, noise_type, stats = render_dataset_selection(
        "cifar10n",
        "worse_label",
        fetch_dataset_stats
    )
    
    st.markdown("---")
    
    # ========== CLOUD MODE TOGGLE ==========
    cloud_enabled, cloud_config = render_cloud_mode_toggle()
    
    # Store cloud configuration in session state
    st.session_state['cloud_enabled'] = cloud_enabled
    st.session_state['cloud_config'] = cloud_config
    
    # Display note about cloud mode usage
    if cloud_enabled:
        if cloud_config:
            st.success("✅ **Cloud mode enabled**: watsonx.ai will be used for model inference during evaluation")
        else:
            st.warning("⚠️ **Cloud mode enabled but not configured**: Please provide watsonx.ai credentials above")
    else:
        st.info("💻 **Local mode**: Inference will run on your local machine")
    
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.success("✅ Logged in as: **test@example.com**")
        st.caption("(Auto-created test user)")
        
        st.markdown("---")
        
        # ========== CONFIGURATION PROGRESS SIDEBAR ==========
        st.markdown("### ⚙️ Configuration Progress")
        
        # Initialize session state for tracking completion
        if 'config_progress' not in st.session_state:
            st.session_state.config_progress = {
                'dataset': False,
                'epistemic': False,
                'aleatoric': False,
                'model': False,
                'evaluation': False
            }
        
        # Dataset is completed if selected (always true in this case)
        st.session_state.config_progress['dataset'] = True
        
        # Display progress items
        render_configuration_progress(st.session_state.config_progress, API_BASE_URL)
    
    # Experiment section
    st.header("🧪 Experiments")
    st.caption(
        "**Hypothesis Validation** — preset sweeps, inspect runs, plots. "
        "**Custom experiments** — API grids (optional). **Tools** — model inference & benchmarks."
    )

    hypothesis_tab, custom_tab, tools_tab = st.tabs([
        "Hypothesis Validation",
        "Custom experiments (API)",
        "Tools",
    ])


    with hypothesis_tab:
        render_hypothesis_validation_tab()


    with custom_tab:
        st.caption("Custom epistemic/aleatoric sweeps via the API (optional).")
        class_names = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
        render_unified_builder(
            dataset_name=dataset_name,
            noise_type=noise_type,
            stats=stats,
            class_names=class_names,
            fetch_dataset_stats=fetch_dataset_stats,
            api_base_url=API_BASE_URL,
            get_headers=get_headers,
        )

    with tools_tab:
        tool_model, tool_bench = st.tabs(["Model Selector", "UQ Benchmarks"])
        with tool_model:
            st.subheader("Model Selector & Inference")
            st.markdown(
                "Load trained models from completed experiments and run inference."
            )
            render_model_selector(API_BASE_URL, get_headers)
            st.markdown("---")
            render_model_inference_panel(API_BASE_URL, get_headers)
        with tool_bench:
            render_uq_benchmarks_tab(API_BASE_URL, get_headers)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <small>Uncertainty Quantification Dashboard | Connected to FastAPI Backend</small>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

# Made with Bob
