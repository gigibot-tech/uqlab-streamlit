"""
Core Visualization Utilities

Consolidated plotting functions shared across all UI components.
Eliminates duplicate plotting code and unifies color schemes.

Key Features:
- Unified color palette
- Shared plot styling
- Common chart types (distributions, correlations, time series)
- Error handling decorators
- Responsive layouts
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

logger = logging.getLogger(__name__)


# ============================================================================
# Color Schemes - Single Source of Truth
# ============================================================================

class ColorScheme:
    """Unified color scheme for all visualizations."""
    
    # Uncertainty types
    ALEATORIC = "#FF6B6B"  # Red
    EPISTEMIC = "#4ECDC4"  # Teal
    TOTAL = "#95E1D3"      # Light teal
    
    # Performance metrics
    ACCURACY = "#45B7D1"   # Blue
    LOSS = "#F38181"       # Pink
    
    # Groups/Categories
    CLEAN = "#A8E6CF"      # Light green
    NOISY = "#FFD3B6"      # Light orange
    ALEATORIC_LIKE = "#FF6B6B"  # Red
    EPISTEMIC_LIKE = "#4ECDC4"  # Teal
    
    # Status
    SUCCESS = "#51CF66"    # Green
    WARNING = "#FFD43B"    # Yellow
    ERROR = "#FF6B6B"      # Red
    INFO = "#74C0FC"       # Light blue
    
    # Neutral
    GRAY_LIGHT = "#E9ECEF"
    GRAY_MEDIUM = "#ADB5BD"
    GRAY_DARK = "#495057"
    
    @classmethod
    def get_group_colors(cls) -> Dict[str, str]:
        """Get color mapping for data groups."""
        return {
            "clean": cls.CLEAN,
            "aleatoric_like": cls.ALEATORIC_LIKE,
            "epistemic_like": cls.EPISTEMIC_LIKE,
            "noisy": cls.NOISY,
        }
    
    @classmethod
    def get_uncertainty_colors(cls) -> Dict[str, str]:
        """Get color mapping for uncertainty types."""
        return {
            "aleatoric": cls.ALEATORIC,
            "epistemic": cls.EPISTEMIC,
            "total": cls.TOTAL,
        }


# ============================================================================
# Plot Styling
# ============================================================================

DEFAULT_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif", size=12),
    margin=dict(l=50, r=50, t=50, b=50),
    hovermode="closest",
)

DEFAULT_AXIS = dict(
    showgrid=True,
    gridcolor=ColorScheme.GRAY_LIGHT,
    zeroline=True,
    zerolinecolor=ColorScheme.GRAY_MEDIUM,
)


def apply_default_style(fig: go.Figure) -> go.Figure:
    """Apply default styling to a plotly figure."""
    fig.update_layout(**DEFAULT_LAYOUT)
    fig.update_xaxes(**DEFAULT_AXIS)
    fig.update_yaxes(**DEFAULT_AXIS)
    return fig


# ============================================================================
# Error Handling Decorator
# ============================================================================

def handle_plot_errors(func: Callable) -> Callable:
    """Decorator to handle plotting errors gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            st.error(f"Failed to create plot: {str(e)}")
            return None
    return wrapper


# ============================================================================
# Distribution Plots
# ============================================================================

@handle_plot_errors
def plot_distribution(
    data: pd.DataFrame,
    column: str,
    group_by: Optional[str] = None,
    title: Optional[str] = None,
    bins: int = 30,
    show_kde: bool = True,
) -> go.Figure:
    """
    Create distribution plot (histogram with optional KDE).
    
    Args:
        data: DataFrame with data
        column: Column to plot
        group_by: Optional column to group by
        title: Plot title
        bins: Number of histogram bins
        show_kde: Whether to show KDE overlay
    
    Returns:
        Plotly figure
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    title = title or f"Distribution of {column}"
    
    if group_by and group_by in data.columns:
        # Grouped histogram
        fig = px.histogram(
            data,
            x=column,
            color=group_by,
            nbins=bins,
            title=title,
            marginal="box" if show_kde else None,
            color_discrete_map=ColorScheme.get_group_colors(),
        )
    else:
        # Single histogram
        fig = px.histogram(
            data,
            x=column,
            nbins=bins,
            title=title,
            marginal="box" if show_kde else None,
        )
        fig.update_traces(marker_color=ColorScheme.INFO)
    
    return apply_default_style(fig)


@handle_plot_errors
def plot_box_comparison(
    data: pd.DataFrame,
    value_column: str,
    group_column: str,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Create box plot comparing groups.
    
    Args:
        data: DataFrame with data
        value_column: Column with values
        group_column: Column with groups
        title: Plot title
    
    Returns:
        Plotly figure
    """
    title = title or f"{value_column} by {group_column}"
    
    fig = px.box(
        data,
        x=group_column,
        y=value_column,
        title=title,
        color=group_column,
        color_discrete_map=ColorScheme.get_group_colors(),
    )
    
    return apply_default_style(fig)


# ============================================================================
# Correlation Plots
# ============================================================================

@handle_plot_errors
def plot_correlation_matrix(
    data: pd.DataFrame,
    columns: Optional[List[str]] = None,
    title: str = "Correlation Matrix",
    method: str = "pearson",
) -> go.Figure:
    """
    Create correlation heatmap.
    
    Args:
        data: DataFrame with data
        columns: Columns to include (None = all numeric)
        title: Plot title
        method: Correlation method ('pearson', 'spearman', 'kendall')
    
    Returns:
        Plotly figure
    """
    if columns:
        plot_data = data[columns]
    else:
        plot_data = data.select_dtypes(include=[np.number])
    
    corr = plot_data.corr(method=method)
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale="RdBu",
        zmid=0,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont={"size": 10},
        colorbar=dict(title="Correlation"),
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title="",
        height=max(400, len(corr) * 30),
    )
    
    return apply_default_style(fig)


@handle_plot_errors
def plot_scatter_with_correlation(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    group_by: Optional[str] = None,
    title: Optional[str] = None,
    show_trendline: bool = True,
) -> go.Figure:
    """
    Create scatter plot with correlation info.
    
    Args:
        data: DataFrame with data
        x_column: X-axis column
        y_column: Y-axis column
        group_by: Optional grouping column
        title: Plot title
        show_trendline: Whether to show trendline
    
    Returns:
        Plotly figure
    """
    title = title or f"{y_column} vs {x_column}"
    
    if group_by and group_by in data.columns:
        fig = px.scatter(
            data,
            x=x_column,
            y=y_column,
            color=group_by,
            title=title,
            trendline="ols" if show_trendline else None,
            color_discrete_map=ColorScheme.get_group_colors(),
        )
    else:
        fig = px.scatter(
            data,
            x=x_column,
            y=y_column,
            title=title,
            trendline="ols" if show_trendline else None,
        )
        fig.update_traces(marker_color=ColorScheme.INFO)
    
    # Add correlation coefficient
    corr = data[[x_column, y_column]].corr().iloc[0, 1]
    fig.add_annotation(
        text=f"r = {corr:.3f}",
        xref="paper", yref="paper",
        x=0.95, y=0.95,
        showarrow=False,
        bgcolor="white",
        bordercolor=ColorScheme.GRAY_MEDIUM,
        borderwidth=1,
    )
    
    return apply_default_style(fig)


# ============================================================================
# Time Series Plots
# ============================================================================

@handle_plot_errors
def plot_training_curves(
    metrics_df: pd.DataFrame,
    metrics: List[str],
    title: str = "Training Curves",
    x_column: str = "epoch",
) -> go.Figure:
    """
    Create training curves plot.
    
    Args:
        metrics_df: DataFrame with metrics
        metrics: List of metric columns to plot
        title: Plot title
        x_column: X-axis column (epoch, step, etc.)
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    colors = [ColorScheme.ACCURACY, ColorScheme.LOSS, ColorScheme.INFO]
    
    for i, metric in enumerate(metrics):
        if metric not in metrics_df.columns:
            continue
        
        fig.add_trace(go.Scatter(
            x=metrics_df[x_column],
            y=metrics_df[metric],
            mode="lines+markers",
            name=metric,
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6),
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_column.capitalize(),
        yaxis_title="Value",
        hovermode="x unified",
    )
    
    return apply_default_style(fig)


@handle_plot_errors
def plot_uncertainty_curves(
    metrics_df: pd.DataFrame,
    x_column: str = "epoch",
    title: str = "Uncertainty Evolution",
) -> go.Figure:
    """
    Create uncertainty evolution plot.
    
    Args:
        metrics_df: DataFrame with uncertainty metrics
        x_column: X-axis column
        title: Plot title
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    uncertainty_cols = {
        "aleatoric": ColorScheme.ALEATORIC,
        "epistemic": ColorScheme.EPISTEMIC,
        "total": ColorScheme.TOTAL,
    }
    
    for col, color in uncertainty_cols.items():
        if col in metrics_df.columns:
            fig.add_trace(go.Scatter(
                x=metrics_df[x_column],
                y=metrics_df[col],
                mode="lines+markers",
                name=col.capitalize(),
                line=dict(color=color, width=2),
                marker=dict(size=6),
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_column.capitalize(),
        yaxis_title="Uncertainty",
        hovermode="x unified",
    )
    
    return apply_default_style(fig)


# ============================================================================
# Multi-Panel Plots
# ============================================================================

@handle_plot_errors
def create_signal_comparison_grid(
    data: pd.DataFrame,
    signals: List[str],
    group_column: str = "group",
    rows: int = 2,
) -> go.Figure:
    """
    Create grid of signal distributions.
    
    Args:
        data: DataFrame with signals
        signals: List of signal columns
        group_column: Column for grouping
        rows: Number of rows in grid
    
    Returns:
        Plotly figure
    """
    cols = (len(signals) + rows - 1) // rows
    
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=signals,
        vertical_spacing=0.12,
        horizontal_spacing=0.10,
    )
    
    group_colors = ColorScheme.get_group_colors()
    
    for idx, signal in enumerate(signals):
        if signal not in data.columns:
            continue
        
        row = idx // cols + 1
        col = idx % cols + 1
        
        for group in data[group_column].unique():
            group_data = data[data[group_column] == group][signal]
            
            fig.add_trace(
                go.Histogram(
                    x=group_data,
                    name=group,
                    marker_color=group_colors.get(group, ColorScheme.INFO),
                    showlegend=(idx == 0),
                    opacity=0.7,
                ),
                row=row,
                col=col,
            )
    
    fig.update_layout(
        title="Signal Distributions by Group",
        height=300 * rows,
        barmode="overlay",
    )
    
    return apply_default_style(fig)


# ============================================================================
# Utility Functions
# ============================================================================

def format_metric_value(value: float, metric_name: str) -> str:
    """Format metric value for display."""
    if pd.isna(value):
        return "N/A"
    
    if "accuracy" in metric_name.lower() or "auroc" in metric_name.lower():
        return f"{value:.1%}"
    elif "loss" in metric_name.lower():
        return f"{value:.4f}"
    else:
        return f"{value:.3f}"


def create_metric_card(
    title: str,
    value: float,
    delta: Optional[float] = None,
    color: str = ColorScheme.INFO,
) -> None:
    """
    Create a metric card in Streamlit.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Optional change value
        color: Card color
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.metric(
            label=title,
            value=format_metric_value(value, title),
            delta=f"{delta:+.2%}" if delta is not None else None,
        )
    
    with col2:
        st.markdown(
            f'<div style="background-color: {color}; height: 60px; border-radius: 5px;"></div>',
            unsafe_allow_html=True,
        )


def display_dataframe_with_styling(
    df: pd.DataFrame,
    highlight_columns: Optional[List[str]] = None,
    precision: int = 3,
) -> None:
    """
    Display DataFrame with custom styling.
    
    Args:
        df: DataFrame to display
        highlight_columns: Columns to highlight
        precision: Decimal precision
    """
    styled_df = df.style.format(precision=precision)
    
    if highlight_columns:
        styled_df = styled_df.background_gradient(
            subset=highlight_columns,
            cmap="RdYlGn",
        )
    
    st.dataframe(styled_df, use_container_width=True)


# Made with Bob