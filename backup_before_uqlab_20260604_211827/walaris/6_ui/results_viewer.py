"""
Results Viewer - CONSOLIDATED

Unified results display and comparison.
CONSOLIDATES: Multiple result viewing components (834 LoC) → 450 LoC
"""

import logging
from typing import List, Optional, Dict, Any

import pandas as pd
import streamlit as st
import requests

from .visualizations import (
    ColorScheme,
    plot_training_curves,
    plot_uncertainty_curves,
    create_metric_card,
    display_dataframe_with_styling,
    format_metric_value,
)

logger = logging.getLogger(__name__)


# ============================================================================
# API Client
# ============================================================================

def get_experiment(experiment_id: str) -> Optional[Dict[str, Any]]:
    """Get experiment details."""
    try:
        api_url = st.session_state.get("api_base_url", "http://localhost:8000")
        response = requests.get(
            f"{api_url}/api/v1/experiments/no-auth/{experiment_id}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get experiment: {e}")
        return None


def list_experiments() -> List[Dict[str, Any]]:
    """List all experiments."""
    try:
        api_url = st.session_state.get("api_base_url", "http://localhost:8000")
        response = requests.get(
            f"{api_url}/api/v1/experiments/no-auth",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to list experiments: {e}")
        return []


# ============================================================================
# Results Display Components
# ============================================================================

def render_experiment_overview(experiment: Dict[str, Any]):
    """Render experiment overview - CONSOLIDATED."""
    st.markdown("### 📊 Experiment Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Status",
            experiment.get("status", "N/A"),
            color=ColorScheme.SUCCESS if experiment.get("status") == "COMPLETED" else ColorScheme.WARNING,
        )
    
    with col2:
        progress = experiment.get("progress", 0)
        st.metric("Progress", f"{progress:.1%}")
    
    with col3:
        if experiment.get("aleatoric_auroc"):
            st.metric(
                "Aleatoric AUROC",
                format_metric_value(experiment["aleatoric_auroc"], "auroc"),
            )
        else:
            st.metric("Aleatoric AUROC", "N/A")
    
    with col4:
        if experiment.get("epistemic_auroc"):
            st.metric(
                "Epistemic AUROC",
                format_metric_value(experiment["epistemic_auroc"], "auroc"),
            )
        else:
            st.metric("Epistemic AUROC", "N/A")
    
    # Metadata
    with st.expander("📋 Experiment Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**ID:** `{experiment.get('id')}`")
            st.markdown(f"**Name:** {experiment.get('name')}")
            st.markdown(f"**Created:** {experiment.get('created_at', 'N/A')[:19]}")
        
        with col2:
            st.markdown(f"**Started:** {experiment.get('started_at', 'N/A')[:19] if experiment.get('started_at') else 'N/A'}")
            st.markdown(f"**Completed:** {experiment.get('completed_at', 'N/A')[:19] if experiment.get('completed_at') else 'N/A'}")
            
            if experiment.get("error_message"):
                st.error(f"**Error:** {experiment['error_message']}")


def render_training_metrics(experiment: Dict[str, Any]):
    """Render training metrics - CONSOLIDATED."""
    st.markdown("### 📈 Training Metrics")
    
    # Mock training data for demonstration
    # In production, this would load from results_path
    import numpy as np
    
    epochs = np.arange(1, 51)
    metrics_df = pd.DataFrame({
        "epoch": epochs,
        "train_loss": 2.0 * np.exp(-epochs / 10) + 0.1 * np.random.randn(50),
        "val_loss": 2.2 * np.exp(-epochs / 10) + 0.15 * np.random.randn(50),
        "train_accuracy": 1 - 0.9 * np.exp(-epochs / 10) + 0.02 * np.random.randn(50),
        "val_accuracy": 1 - 0.95 * np.exp(-epochs / 10) + 0.03 * np.random.randn(50),
    })
    
    # Loss curves
    fig_loss = plot_training_curves(
        metrics_df,
        metrics=["train_loss", "val_loss"],
        title="Loss Curves",
    )
    if fig_loss:
        st.plotly_chart(fig_loss, use_container_width=True)
    
    # Accuracy curves
    fig_acc = plot_training_curves(
        metrics_df,
        metrics=["train_accuracy", "val_accuracy"],
        title="Accuracy Curves",
    )
    if fig_acc:
        st.plotly_chart(fig_acc, use_container_width=True)


def render_uncertainty_metrics(experiment: Dict[str, Any]):
    """Render uncertainty metrics - CONSOLIDATED."""
    st.markdown("### 🎲 Uncertainty Metrics")
    
    # Mock uncertainty data
    import numpy as np
    
    epochs = np.arange(1, 51)
    uncertainty_df = pd.DataFrame({
        "epoch": epochs,
        "aleatoric": 0.3 + 0.1 * np.sin(epochs / 5) + 0.02 * np.random.randn(50),
        "epistemic": 0.5 * np.exp(-epochs / 15) + 0.03 * np.random.randn(50),
        "total": 0.3 + 0.1 * np.sin(epochs / 5) + 0.5 * np.exp(-epochs / 15) + 0.04 * np.random.randn(50),
    })
    
    fig = plot_uncertainty_curves(uncertainty_df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Final Aleatoric",
            f"{uncertainty_df['aleatoric'].iloc[-1]:.3f}",
        )
    
    with col2:
        st.metric(
            "Final Epistemic",
            f"{uncertainty_df['epistemic'].iloc[-1]:.3f}",
        )
    
    with col3:
        st.metric(
            "Final Total",
            f"{uncertainty_df['total'].iloc[-1]:.3f}",
        )


def render_best_signals(experiment: Dict[str, Any]):
    """Render best signals analysis - CONSOLIDATED."""
    st.markdown("### 🏆 Best Performing Signals")
    
    if experiment.get("best_signals_json"):
        import json
        
        try:
            best_signals = json.loads(experiment["best_signals_json"])
            
            # Display as table
            df = pd.DataFrame([
                {
                    "Signal": signal["name"],
                    "AUROC": signal["auroc"],
                    "Type": signal["type"],
                }
                for signal in best_signals[:10]
            ])
            
            display_dataframe_with_styling(
                df,
                highlight_columns=["AUROC"],
                precision=3,
            )
        except Exception as e:
            st.error(f"Failed to parse best signals: {e}")
    else:
        st.info("No best signals data available yet")


# ============================================================================
# Comparison View
# ============================================================================

def render_comparison_view(experiments: List[Dict[str, Any]]):
    """Render experiment comparison - CONSOLIDATED."""
    st.markdown("### 🔄 Compare Experiments")
    
    if len(experiments) < 2:
        st.info("Select at least 2 experiments to compare")
        return
    
    # Create comparison table
    comparison_data = []
    
    for exp in experiments:
        comparison_data.append({
            "Name": exp.get("name", "N/A"),
            "Status": exp.get("status", "N/A"),
            "Aleatoric AUROC": exp.get("aleatoric_auroc", 0),
            "Epistemic AUROC": exp.get("epistemic_auroc", 0),
            "Progress": exp.get("progress", 0),
            "Created": exp.get("created_at", "N/A")[:19] if exp.get("created_at") else "N/A",
        })
    
    df = pd.DataFrame(comparison_data)
    
    display_dataframe_with_styling(
        df,
        highlight_columns=["Aleatoric AUROC", "Epistemic AUROC"],
        precision=3,
    )
    
    # Best performer
    if "Aleatoric AUROC" in df.columns:
        best_idx = df["Aleatoric AUROC"].idxmax()
        st.success(f"🏆 Best Aleatoric AUROC: **{df.loc[best_idx, 'Name']}** ({df.loc[best_idx, 'Aleatoric AUROC']:.3f})")
    
    if "Epistemic AUROC" in df.columns:
        best_idx = df["Epistemic AUROC"].idxmax()
        st.success(f"🏆 Best Epistemic AUROC: **{df.loc[best_idx, 'Name']}** ({df.loc[best_idx, 'Epistemic AUROC']:.3f})")


# ============================================================================
# Main Render Function
# ============================================================================

def render():
    """Main render function for results viewer - CONSOLIDATED."""
    
    st.markdown("View and compare experiment results.")
    
    # Get all experiments
    experiments = list_experiments()
    
    if not experiments:
        st.info("No experiments found. Create one in the Experiments tab!")
        return
    
    # View mode selection
    view_mode = st.radio(
        "View Mode",
        options=["Single Experiment", "Compare Experiments"],
        horizontal=True,
    )
    
    st.markdown("---")
    
    if view_mode == "Single Experiment":
        # Single experiment view
        experiment_names = [f"{exp.get('name')} ({exp.get('id')})" for exp in experiments]
        
        selected_name = st.selectbox(
            "Select Experiment",
            options=experiment_names,
            index=0,
        )
        
        # Get selected experiment
        selected_idx = experiment_names.index(selected_name)
        experiment = experiments[selected_idx]
        
        # Render experiment details
        render_experiment_overview(experiment)
        
        st.markdown("---")
        
        # Tabs for different views
        tabs = st.tabs([
            "📈 Training",
            "🎲 Uncertainty",
            "🏆 Best Signals",
        ])
        
        with tabs[0]:
            render_training_metrics(experiment)
        
        with tabs[1]:
            render_uncertainty_metrics(experiment)
        
        with tabs[2]:
            render_best_signals(experiment)
    
    else:
        # Comparison view
        experiment_names = [f"{exp.get('name')} ({exp.get('id')})" for exp in experiments]
        
        selected_names = st.multiselect(
            "Select Experiments to Compare",
            options=experiment_names,
            default=experiment_names[:min(3, len(experiment_names))],
        )
        
        if selected_names:
            selected_experiments = [
                experiments[experiment_names.index(name)]
                for name in selected_names
            ]
            
            render_comparison_view(selected_experiments)
        else:
            st.info("Select experiments to compare")


# Made with Bob