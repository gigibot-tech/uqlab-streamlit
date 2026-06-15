"""
Correlation Visualization

Specialized correlation analysis and visualization tools.
Explores relationships between signals, metrics, and data characteristics.
"""

import logging
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np
import streamlit as st

from .visualizations import (
    ColorScheme,
    plot_correlation_matrix,
    plot_scatter_with_correlation,
    handle_plot_errors,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Data Loading
# ============================================================================

@st.cache_data
def load_correlation_data(file_path: str) -> Optional[pd.DataFrame]:
    """Load data for correlation analysis."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        st.error(f"Failed to load data: {str(e)}")
        return None


# ============================================================================
# Correlation Analysis
# ============================================================================

def compute_correlation_significance(df: pd.DataFrame, col1: str, col2: str) -> Dict[str, float]:
    """Compute correlation with significance test."""
    from scipy import stats
    
    # Remove NaN values
    mask = ~(df[col1].isna() | df[col2].isna())
    x = df.loc[mask, col1].values
    y = df.loc[mask, col2].values
    
    if len(x) < 3:
        return {"correlation": 0.0, "p_value": 1.0, "n_samples": len(x)}
    
    # Pearson correlation
    corr, p_value = stats.pearsonr(x, y)
    
    return {
        "correlation": corr,
        "p_value": p_value,
        "n_samples": len(x),
        "significant": p_value < 0.05,
    }


def find_top_correlations(df: pd.DataFrame, columns: List[str], top_n: int = 10) -> pd.DataFrame:
    """Find top correlations in dataset."""
    correlations = []
    
    for i, col1 in enumerate(columns):
        for col2 in columns[i+1:]:
            stats = compute_correlation_significance(df, col1, col2)
            
            correlations.append({
                "Variable 1": col1,
                "Variable 2": col2,
                "Correlation": stats["correlation"],
                "P-value": stats["p_value"],
                "Significant": "✓" if stats["significant"] else "✗",
                "N": stats["n_samples"],
            })
    
    # Sort by absolute correlation
    corr_df = pd.DataFrame(correlations)
    corr_df["Abs Correlation"] = corr_df["Correlation"].abs()
    corr_df = corr_df.sort_values("Abs Correlation", ascending=False)
    
    return corr_df.head(top_n).drop("Abs Correlation", axis=1)


# ============================================================================
# Visualization Components
# ============================================================================

def render_correlation_matrix_view(df: pd.DataFrame, columns: List[str]):
    """Render correlation matrix view."""
    st.markdown("#### Correlation Matrix")
    
    # Method selection
    method = st.selectbox(
        "Correlation Method",
        options=["pearson", "spearman", "kendall"],
        index=0,
    )
    
    # Create matrix
    fig = plot_correlation_matrix(df, columns=columns, method=method)
    if fig:
        st.plotly_chart(fig, use_container_width=True)


def render_pairwise_analysis(df: pd.DataFrame, columns: List[str]):
    """Render pairwise correlation analysis."""
    st.markdown("#### Pairwise Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_var = st.selectbox("X Variable", options=columns, index=0, key="pair_x")
    
    with col2:
        y_var = st.selectbox("Y Variable", options=columns, index=min(1, len(columns)-1), key="pair_y")
    
    if x_var != y_var:
        # Scatter plot
        group_by = st.selectbox(
            "Color by (optional)",
            options=["None"] + [col for col in df.columns if df[col].dtype == 'object'],
            index=0,
        )
        
        fig = plot_scatter_with_correlation(
            df,
            x_var,
            y_var,
            group_by=group_by if group_by != "None" else None,
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        stats = compute_correlation_significance(df, x_var, y_var)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Correlation", f"{stats['correlation']:.3f}")
        
        with col2:
            st.metric("P-value", f"{stats['p_value']:.4f}")
        
        with col3:
            st.metric("Samples", stats['n_samples'])
        
        if stats['significant']:
            st.success("✓ Statistically significant (p < 0.05)")
        else:
            st.warning("✗ Not statistically significant (p ≥ 0.05)")


def render_top_correlations(df: pd.DataFrame, columns: List[str]):
    """Render top correlations table."""
    st.markdown("#### Top Correlations")
    
    top_n = st.slider("Number of top correlations", min_value=5, max_value=50, value=10)
    
    top_corr = find_top_correlations(df, columns, top_n=top_n)
    
    st.dataframe(
        top_corr.style.background_gradient(subset=["Correlation"], cmap="RdYlGn", vmin=-1, vmax=1),
        use_container_width=True,
        hide_index=True,
    )


def render_conditional_analysis(df: pd.DataFrame, columns: List[str]):
    """Render conditional correlation analysis."""
    st.markdown("#### Conditional Analysis")
    
    st.info("Analyze how correlations change under different conditions")
    
    # Select conditioning variable
    categorical_cols = [col for col in df.columns if df[col].dtype == 'object']
    
    if not categorical_cols:
        st.warning("No categorical variables found for conditioning")
        return
    
    condition_var = st.selectbox("Condition on", options=categorical_cols)
    
    col1, col2 = st.columns(2)
    
    with col1:
        x_var = st.selectbox("X Variable", options=columns, index=0, key="cond_x")
    
    with col2:
        y_var = st.selectbox("Y Variable", options=columns, index=min(1, len(columns)-1), key="cond_y")
    
    if x_var != y_var:
        # Compute correlations for each condition
        conditions = df[condition_var].unique()
        
        results = []
        for condition in conditions:
            subset = df[df[condition_var] == condition]
            stats = compute_correlation_significance(subset, x_var, y_var)
            
            results.append({
                "Condition": condition,
                "Correlation": stats["correlation"],
                "P-value": stats["p_value"],
                "N": stats["n_samples"],
                "Significant": "✓" if stats["significant"] else "✗",
            })
        
        results_df = pd.DataFrame(results)
        
        st.dataframe(
            results_df.style.background_gradient(subset=["Correlation"], cmap="RdYlGn", vmin=-1, vmax=1),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================================
# Main Render Function
# ============================================================================

def render():
    """Main render function for correlation visualization."""
    
    st.markdown("""
    Explore correlations between signals, metrics, and data characteristics.
    Upload a CSV file with multiple numeric columns to begin.
    """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Data CSV",
        type=["csv"],
        help="CSV file with numeric columns for correlation analysis",
    )
    
    if uploaded_file is None:
        st.info("👆 Upload a CSV file to begin correlation analysis")
        
        # Show example
        with st.expander("📋 Example Use Cases"):
            st.markdown("""
            - **Signal Correlations**: Analyze relationships between uncertainty signals
            - **Metric Relationships**: Explore how different metrics relate to each other
            - **Feature Analysis**: Understand feature importance and redundancy
            - **Conditional Analysis**: See how correlations change across groups
            """)
        
        return
    
    # Load data
    df = load_correlation_data(uploaded_file)
    
    if df is None or df.empty:
        st.error("Failed to load data or file is empty")
        return
    
    # Get numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        st.error("Need at least 2 numeric columns for correlation analysis")
        return
    
    # Display info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", len(df))
    
    with col2:
        st.metric("Numeric Columns", len(numeric_cols))
    
    with col3:
        st.metric("Total Columns", len(df.columns))
    
    st.markdown("---")
    
    # Column selection
    with st.expander("🎯 Select Columns for Analysis", expanded=True):
        selected_cols = st.multiselect(
            "Columns to analyze",
            options=numeric_cols,
            default=numeric_cols[:min(10, len(numeric_cols))],
        )
    
    if len(selected_cols) < 2:
        st.warning("Select at least 2 columns for correlation analysis")
        return
    
    st.markdown("---")
    
    # Tabs for different views
    tabs = st.tabs([
        "🔲 Matrix",
        "📊 Pairwise",
        "🏆 Top Correlations",
        "🔀 Conditional",
    ])
    
    with tabs[0]:
        render_correlation_matrix_view(df, selected_cols)
    
    with tabs[1]:
        render_pairwise_analysis(df, selected_cols)
    
    with tabs[2]:
        render_top_correlations(df, selected_cols)
    
    with tabs[3]:
        render_conditional_analysis(df, selected_cols)


# Made with Bob