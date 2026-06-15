"""
Signal Viewer - CONSOLIDATED

Unified signal analysis and visualization.
CONSOLIDATES: per_sample_signals_viz.py (1,953 LoC) → 550 LoC
Major savings through shared plotting utilities and deduplication.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .visualizations import (
    ColorScheme,
    plot_distribution,
    plot_box_comparison,
    plot_correlation_matrix,
    plot_scatter_with_correlation,
    create_signal_comparison_grid,
    handle_plot_errors,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Constants - Shared Definitions
# ============================================================================

SIGNAL_COLUMNS = [
    "msp_uncertainty",
    "predictive_entropy",
    "mutual_info",
    "coherence",
    "inverse_coherence",
    "dominance",
    "inverse_mass",
    "inverse_logit_magnitude",
]

META_COLUMNS = [
    "group",
    "dataset_index",
    "clean_label",
    "noisy_label",
    "is_noisy",
]

GROUP_ORDER = ["clean", "aleatoric_like", "epistemic_like"]


# ============================================================================
# Data Loading
# ============================================================================

@st.cache_data
def load_signal_data(file_path: str) -> Optional[pd.DataFrame]:
    """Load signal data from CSV file."""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} samples from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        st.error(f"Failed to load data: {str(e)}")
        return None


def get_available_signals(df: pd.DataFrame) -> List[str]:
    """Get list of available signal columns."""
    return [col for col in SIGNAL_COLUMNS if col in df.columns]


# ============================================================================
# Signal Statistics
# ============================================================================

def compute_signal_statistics(df: pd.DataFrame, signals: List[str], group_by: Optional[str] = None) -> pd.DataFrame:
    """Compute statistics for signals."""
    if group_by and group_by in df.columns:
        stats = df.groupby(group_by)[signals].agg(['mean', 'std', 'min', 'max'])
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        return stats.reset_index()
    else:
        stats = df[signals].describe().T
        return stats


# ============================================================================
# Visualization Components
# ============================================================================

@handle_plot_errors
def plot_signal_distributions_grid(df: pd.DataFrame, signals: List[str], group_column: str = "group") -> go.Figure:
    """Create grid of signal distributions - CONSOLIDATED."""
    return create_signal_comparison_grid(df, signals, group_column, rows=2)


@handle_plot_errors
def plot_signal_boxplots(df: pd.DataFrame, signals: List[str], group_column: str = "group") -> go.Figure:
    """Create box plots for all signals - CONSOLIDATED."""
    n_signals = len(signals)
    cols = 3
    rows = (n_signals + cols - 1) // cols
    
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=signals,
        vertical_spacing=0.12,
        horizontal_spacing=0.10,
    )
    
    group_colors = ColorScheme.get_group_colors()
    
    for idx, signal in enumerate(signals):
        if signal not in df.columns:
            continue
        
        row = idx // cols + 1
        col = idx % cols + 1
        
        for group in df[group_column].unique():
            group_data = df[df[group_column] == group][signal]
            
            fig.add_trace(
                go.Box(
                    y=group_data,
                    name=group,
                    marker_color=group_colors.get(group, ColorScheme.INFO),
                    showlegend=(idx == 0),
                ),
                row=row,
                col=col,
            )
    
    fig.update_layout(
        title="Signal Box Plots by Group",
        height=300 * rows,
        showlegend=True,
    )
    
    return fig


@handle_plot_errors
def plot_ude_analysis(df: pd.DataFrame, aleatoric_signal: str, epistemic_signal: str) -> go.Figure:
    """Create UDE (Uncertainty Decomposition Error) analysis plot - CONSOLIDATED."""
    fig = go.Figure()
    
    if "group" in df.columns:
        for group in df["group"].unique():
            group_data = df[df["group"] == group]
            
            fig.add_trace(go.Scatter(
                x=group_data[aleatoric_signal],
                y=group_data[epistemic_signal],
                mode="markers",
                name=group,
                marker=dict(
                    size=8,
                    color=ColorScheme.get_group_colors().get(group, ColorScheme.INFO),
                    opacity=0.6,
                ),
            ))
    else:
        fig.add_trace(go.Scatter(
            x=df[aleatoric_signal],
            y=df[epistemic_signal],
            mode="markers",
            marker=dict(size=8, color=ColorScheme.INFO, opacity=0.6),
        ))
    
    # Add diagonal line
    max_val = max(df[aleatoric_signal].max(), df[epistemic_signal].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode="lines",
        name="Equal Uncertainty",
        line=dict(color=ColorScheme.GRAY_MEDIUM, dash="dash"),
        showlegend=True,
    ))
    
    fig.update_layout(
        title="Uncertainty Decomposition Analysis",
        xaxis_title=f"{aleatoric_signal} (Aleatoric)",
        yaxis_title=f"{epistemic_signal} (Epistemic)",
        hovermode="closest",
    )
    
    return fig


# ============================================================================
# UI Tabs - CONSOLIDATED
# ============================================================================

def render_table_tab(df: pd.DataFrame, signals: List[str]):
    """Render data table tab - CONSOLIDATED."""
    st.markdown("#### Raw Data Table")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        if "is_noisy" in df.columns:
            show_noisy_only = st.checkbox("Show only noisy samples", value=False)
            if show_noisy_only:
                df = df[df["is_noisy"].astype(bool)]
    
    with col2:
        if "group" in df.columns:
            selected_groups = st.multiselect(
                "Filter by group",
                options=df["group"].unique().tolist(),
                default=df["group"].unique().tolist(),
            )
            df = df[df["group"].isin(selected_groups)]
    
    # Display columns
    display_cols = [c for c in META_COLUMNS if c in df.columns] + signals
    
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        height=400,
    )
    
    st.caption(f"Showing {len(df)} samples")


def render_summary_tab(df: pd.DataFrame, signals: List[str]):
    """Render summary statistics tab - CONSOLIDATED."""
    st.markdown("#### Summary Statistics")
    
    if "group" in df.columns:
        stats = compute_signal_statistics(df, signals, group_by="group")
        st.dataframe(stats, use_container_width=True, hide_index=True)
    else:
        stats = compute_signal_statistics(df, signals)
        st.dataframe(stats, use_container_width=True)


def render_distributions_tab(df: pd.DataFrame, signals: List[str]):
    """Render distributions tab - CONSOLIDATED."""
    st.markdown("#### Signal Distributions")
    
    # Plot type selection
    plot_type = st.radio(
        "Plot Type",
        options=["Histograms", "Box Plots", "Violin Plots"],
        horizontal=True,
    )
    
    if plot_type == "Histograms":
        fig = plot_signal_distributions_grid(df, signals)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    elif plot_type == "Box Plots":
        fig = plot_signal_boxplots(df, signals)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Violin plots coming soon!")


def render_correlation_tab(df: pd.DataFrame, signals: List[str]):
    """Render correlation tab - CONSOLIDATED."""
    st.markdown("#### Signal Correlations")
    
    # Correlation matrix
    fig = plot_correlation_matrix(df, columns=signals, method="pearson")
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Pairwise scatter
    st.markdown("##### Pairwise Relationships")
    col1, col2 = st.columns(2)
    
    with col1:
        x_signal = st.selectbox("X-axis Signal", options=signals, index=0)
    
    with col2:
        y_signal = st.selectbox("Y-axis Signal", options=signals, index=min(1, len(signals)-1))
    
    if x_signal != y_signal:
        fig = plot_scatter_with_correlation(
            df,
            x_signal,
            y_signal,
            group_by="group" if "group" in df.columns else None,
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)


def render_ude_tab(df: pd.DataFrame, signals: List[str]):
    """Render UDE analysis tab - CONSOLIDATED."""
    st.markdown("#### Uncertainty Decomposition Error (UDE) Analysis")
    
    st.info("""
    UDE analysis examines how well signals separate aleatoric and epistemic uncertainty.
    Ideal signals should show clear separation between uncertainty types.
    """)
    
    # Signal selection
    col1, col2 = st.columns(2)
    
    with col1:
        aleatoric_signal = st.selectbox(
            "Aleatoric Signal",
            options=signals,
            index=0,
        )
    
    with col2:
        epistemic_signal = st.selectbox(
            "Epistemic Signal",
            options=signals,
            index=min(1, len(signals)-1),
        )
    
    if aleatoric_signal != epistemic_signal:
        fig = plot_ude_analysis(df, aleatoric_signal, epistemic_signal)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Compute UDE score
        if "group" in df.columns:
            st.markdown("##### UDE Scores by Group")
            
            for group in df["group"].unique():
                group_data = df[df["group"] == group]
                
                # Simple UDE approximation
                aleatoric_vals = group_data[aleatoric_signal].values
                epistemic_vals = group_data[epistemic_signal].values
                
                ude_score = np.abs(aleatoric_vals - epistemic_vals).mean()
                
                st.metric(
                    label=f"{group} UDE",
                    value=f"{ude_score:.4f}",
                )


# ============================================================================
# Main Render Function
# ============================================================================

def render():
    """Main render function for signal viewer - CONSOLIDATED."""
    
    st.markdown("""
    Analyze uncertainty signals from experiment results.
    Upload a per-sample signals CSV file to get started.
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Per-Sample Signals CSV",
        type=["csv"],
        help="CSV file with per-sample uncertainty signals",
    )
    
    if uploaded_file is None:
        st.info("👆 Upload a signals CSV file to begin analysis")
        
        # Show example
        with st.expander("📋 Expected CSV Format"):
            st.code("""
group,dataset_index,clean_label,noisy_label,is_noisy,msp_uncertainty,predictive_entropy,mutual_info
clean,0,3,3,False,0.123,0.456,0.789
aleatoric_like,1,5,7,True,0.234,0.567,0.890
epistemic_like,2,2,2,False,0.345,0.678,0.901
            """)
        
        return
    
    # Load data
    df = load_signal_data(uploaded_file)
    
    if df is None or df.empty:
        st.error("Failed to load data or file is empty")
        return
    
    # Get available signals
    signals = get_available_signals(df)
    
    if not signals:
        st.error(f"No signal columns found. Expected: {', '.join(SIGNAL_COLUMNS)}")
        return
    
    # Display info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Samples", len(df))
    
    with col2:
        st.metric("Signals", len(signals))
    
    with col3:
        if "group" in df.columns:
            st.metric("Groups", df["group"].nunique())
        else:
            st.metric("Groups", "N/A")
    
    st.markdown("---")
    
    # Tabs for different views - CONSOLIDATED
    tabs = st.tabs([
        "📋 Table",
        "📊 Summary",
        "📈 Distributions",
        "🔗 Correlations",
        "🎯 UDE Analysis",
    ])
    
    with tabs[0]:
        render_table_tab(df, signals)
    
    with tabs[1]:
        render_summary_tab(df, signals)
    
    with tabs[2]:
        render_distributions_tab(df, signals)
    
    with tabs[3]:
        render_correlation_tab(df, signals)
    
    with tabs[4]:
        render_ude_tab(df, signals)


# Made with Bob