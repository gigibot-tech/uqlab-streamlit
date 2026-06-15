"""
Batch Experiment Builder

Consolidated form for creating and managing batch experiments.
Allows configuration of multiple experiments with parameter sweeps.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import streamlit as st
import requests
import pandas as pd

logger = logging.getLogger(__name__)


# ============================================================================
# API Client
# ============================================================================

def create_batch(name: str, description: str, experiments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Create batch via API."""
    try:
        api_url = st.session_state.get("api_base_url", "http://localhost:8000")
        response = requests.post(
            f"{api_url}/api/v1/batch/no-auth",
            json={
                "name": name,
                "description": description,
                "experiments": experiments,
                "run_parallel": False,
                "max_parallel": 4,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to create batch: {e}")
        st.error(f"Failed to create batch: {str(e)}")
        return None


def list_batches() -> list:
    """List all batches."""
    try:
        api_url = st.session_state.get("api_base_url", "http://localhost:8000")
        response = requests.get(
            f"{api_url}/api/v1/batch/no-auth",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to list batches: {e}")
        return []


# ============================================================================
# Parameter Sweep Configuration
# ============================================================================

def render_sweep_config() -> Optional[Dict[str, List[Any]]]:
    """Render parameter sweep configuration."""
    st.markdown("### 🔄 Parameter Sweep")
    
    sweep_type = st.radio(
        "Sweep Type",
        options=["Grid Search", "Random Search", "Manual List"],
        horizontal=True,
    )
    
    if sweep_type == "Grid Search":
        col1, col2 = st.columns(2)
        
        with col1:
            param_name = st.selectbox(
                "Parameter to Sweep",
                options=["learning_rate", "batch_size", "dropout_rate", "noise_rate"],
            )
        
        with col2:
            if param_name in ["learning_rate", "dropout_rate", "noise_rate"]:
                min_val = st.number_input("Min Value", value=0.001, format="%.6f")
                max_val = st.number_input("Max Value", value=0.1, format="%.6f")
                steps = st.number_input("Steps", min_value=2, max_value=20, value=5)
                
                import numpy as np
                values = np.linspace(min_val, max_val, steps).tolist()
            else:
                values = st.multiselect(
                    "Values",
                    options=[16, 32, 64, 128, 256, 512],
                    default=[64, 128],
                )
        
        return {param_name: values}
    
    elif sweep_type == "Manual List":
        st.info("Define experiments manually below")
        return None
    
    else:
        st.info("Random search not yet implemented")
        return None


# ============================================================================
# Experiment List Builder
# ============================================================================

def render_experiment_list_builder(sweep_config: Optional[Dict[str, List[Any]]]) -> List[Dict[str, Any]]:
    """Build list of experiments from sweep config."""
    
    if sweep_config:
        # Generate experiments from sweep
        param_name = list(sweep_config.keys())[0]
        values = sweep_config[param_name]
        
        experiments = []
        for value in values:
            exp_config = {
                "dataset": "cifar10",
                "noise_type": "symmetric",
                "noise_rate": 0.2,
                "architecture": "resnet18",
                "epochs": 50,
                "batch_size": 128,
                "learning_rate": 0.001,
                "optimizer": "adam",
                "mc_samples": 10,
                "dropout_rate": 0.1,
            }
            exp_config[param_name] = value
            
            experiments.append({
                "name": f"exp_{param_name}_{value}",
                "config": exp_config,
            })
        
        st.success(f"✅ Generated {len(experiments)} experiments")
        
        # Show preview
        with st.expander("Preview Experiments"):
            df = pd.DataFrame([
                {
                    "Name": exp["name"],
                    param_name: exp["config"][param_name],
                }
                for exp in experiments
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        return experiments
    
    else:
        # Manual experiment definition
        st.markdown("### ➕ Add Experiments Manually")
        
        if "batch_experiments" not in st.session_state:
            st.session_state.batch_experiments = []
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            exp_name = st.text_input("Experiment Name", key="manual_exp_name")
        
        with col2:
            if st.button("Add Experiment", use_container_width=True):
                if exp_name:
                    st.session_state.batch_experiments.append({
                        "name": exp_name,
                        "config": {
                            "dataset": "cifar10",
                            "epochs": 50,
                            "batch_size": 128,
                        }
                    })
                    st.rerun()
        
        # Show current list
        if st.session_state.batch_experiments:
            st.markdown(f"**Current Experiments:** {len(st.session_state.batch_experiments)}")
            
            for idx, exp in enumerate(st.session_state.batch_experiments):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(exp["name"])
                with col2:
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state.batch_experiments.pop(idx)
                        st.rerun()
        
        return st.session_state.batch_experiments


# ============================================================================
# Batch List Display
# ============================================================================

def render_batch_list():
    """Render list of existing batches."""
    st.markdown("### 📦 Recent Batches")
    
    batches = list_batches()
    
    if not batches:
        st.info("No batches yet. Create your first one above!")
        return
    
    # Display as table
    df = pd.DataFrame([
        {
            "Name": batch.get("name", "N/A"),
            "Status": batch.get("status", "N/A"),
            "Total": batch.get("total_experiments", 0),
            "Completed": batch.get("completed_experiments", 0),
            "Progress": f"{batch.get('progress', 0):.1%}",
            "Created": batch.get("created_at", "N/A")[:19] if batch.get("created_at") else "N/A",
        }
        for batch in batches[:10]
    ])
    
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================================
# Main Render Function
# ============================================================================

def render():
    """Main render function for batch builder."""
    
    st.markdown("Create batches of experiments with parameter sweeps or manual configuration.")
    
    # Batch metadata
    st.markdown("### 📝 Batch Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        batch_name = st.text_input(
            "Batch Name",
            value=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )
    
    with col2:
        batch_description = st.text_input(
            "Description",
            value="",
            placeholder="Optional description",
        )
    
    st.markdown("---")
    
    # Sweep configuration
    sweep_config = render_sweep_config()
    
    st.markdown("---")
    
    # Build experiment list
    experiments = render_experiment_list_builder(sweep_config)
    
    st.markdown("---")
    
    # Create batch
    st.markdown("### 🚀 Create Batch")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"Ready to create batch with {len(experiments)} experiments")
    
    with col2:
        create_button = st.button(
            "Create Batch",
            type="primary",
            use_container_width=True,
            disabled=len(experiments) == 0,
        )
    
    if create_button:
        if not batch_name:
            st.error("Please provide a batch name")
        elif len(experiments) == 0:
            st.error("Add at least one experiment")
        else:
            with st.spinner("Creating batch..."):
                result = create_batch(batch_name, batch_description or "", experiments)
                
                if result:
                    st.success(f"✅ Batch created: {result.get('id')}")
                    st.session_state.batch_experiments = []
                    st.rerun()
    
    st.markdown("---")
    
    # Show recent batches
    render_batch_list()


# Made with Bob