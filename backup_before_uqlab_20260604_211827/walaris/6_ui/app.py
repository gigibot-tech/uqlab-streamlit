"""
Main Streamlit Application

Consolidated UI entry point with tabbed interface.
Provides access to all experiment management and visualization features.
"""

import logging
from pathlib import Path
from typing import Optional

import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Page Configuration
# ============================================================================

def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Walaris MLOps Platform",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 1rem 2rem;
            font-size: 1.1rem;
        }
        </style>
    """, unsafe_allow_html=True)


# ============================================================================
# Session State Management
# ============================================================================

def initialize_session_state():
    """Initialize session state variables."""
    if "api_base_url" not in st.session_state:
        st.session_state.api_base_url = "http://localhost:8000"
    
    if "selected_experiment" not in st.session_state:
        st.session_state.selected_experiment = None
    
    if "selected_batch" not in st.session_state:
        st.session_state.selected_batch = None
    
    if "refresh_trigger" not in st.session_state:
        st.session_state.refresh_trigger = 0


# ============================================================================
# Sidebar
# ============================================================================

def render_sidebar():
    """Render sidebar with global settings."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API Configuration
        st.markdown("### API Configuration")
        api_url = st.text_input(
            "API Base URL",
            value=st.session_state.api_base_url,
            help="Backend API endpoint"
        )
        if api_url != st.session_state.api_base_url:
            st.session_state.api_base_url = api_url
            st.rerun()
        
        # Connection Status
        st.markdown("### Connection Status")
        try:
            import requests
            response = requests.get(f"{api_url}/health", timeout=2)
            if response.status_code == 200:
                st.success("✅ Connected")
            else:
                st.error("❌ Connection failed")
        except Exception as e:
            st.error(f"❌ Cannot reach API: {str(e)[:50]}")
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### Quick Actions")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state.refresh_trigger += 1
            st.rerun()
        
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")
        
        st.markdown("---")
        
        # Info
        st.markdown("### About")
        st.caption("""
        **Walaris MLOps Platform**
        
        Uncertainty quantification and 
        experiment management for ML.
        
        Version: 1.0.0
        """)


# ============================================================================
# Main Content Tabs
# ============================================================================

def render_experiments_tab():
    """Render single experiments tab."""
    st.markdown("## 🧪 Single Experiments")
    st.markdown("Create and manage individual experiments")
    
    # Import here to avoid circular dependencies
    try:
        from . import experiment_builder
        experiment_builder.render()
    except ImportError as e:
        st.error(f"Failed to load experiment builder: {e}")
        st.info("This module is under development.")


def render_batch_tab():
    """Render batch experiments tab."""
    st.markdown("## 📦 Batch Experiments")
    st.markdown("Create and manage batches of experiments")
    
    try:
        from . import batch_builder
        batch_builder.render()
    except ImportError as e:
        st.error(f"Failed to load batch builder: {e}")
        st.info("This module is under development.")


def render_results_tab():
    """Render results viewer tab."""
    st.markdown("## 📊 Results & Analysis")
    st.markdown("View and compare experiment results")
    
    try:
        from . import results_viewer
        results_viewer.render()
    except ImportError as e:
        st.error(f"Failed to load results viewer: {e}")
        st.info("This module is under development.")


def render_signals_tab():
    """Render signal analysis tab."""
    st.markdown("## 📈 Signal Analysis")
    st.markdown("Analyze uncertainty signals and patterns")
    
    try:
        from . import signal_viewer
        signal_viewer.render()
    except ImportError as e:
        st.error(f"Failed to load signal viewer: {e}")
        st.info("This module is under development.")


def render_correlation_tab():
    """Render correlation analysis tab."""
    st.markdown("## 🔗 Correlation Analysis")
    st.markdown("Explore relationships between signals and metrics")
    
    try:
        from . import correlation_viz
        correlation_viz.render()
    except ImportError as e:
        st.error(f"Failed to load correlation viz: {e}")
        st.info("This module is under development.")


def render_monitoring_tab():
    """Render system monitoring tab."""
    st.markdown("## 📡 System Monitoring")
    st.markdown("Monitor running experiments and system health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Active Experiments",
            value="0",
            delta="0",
        )
    
    with col2:
        st.metric(
            label="Queued Experiments",
            value="0",
            delta="0",
        )
    
    with col3:
        st.metric(
            label="Completed Today",
            value="0",
            delta="+0",
        )
    
    st.info("Real-time monitoring features coming soon!")


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point."""
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main header
    st.markdown('<h1 class="main-header">🔬 Walaris MLOps Platform</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Uncertainty Quantification & Experiment Management</p>',
        unsafe_allow_html=True
    )
    
    # Main tabs
    tabs = st.tabs([
        "🧪 Experiments",
        "📦 Batches",
        "📊 Results",
        "📈 Signals",
        "🔗 Correlations",
        "📡 Monitoring",
    ])
    
    with tabs[0]:
        render_experiments_tab()
    
    with tabs[1]:
        render_batch_tab()
    
    with tabs[2]:
        render_results_tab()
    
    with tabs[3]:
        render_signals_tab()
    
    with tabs[4]:
        render_correlation_tab()
    
    with tabs[5]:
        render_monitoring_tab()
    
    # Footer
    st.markdown("---")
    st.caption("Made with ❤️ by the Walaris Team | Powered by Streamlit & FastAPI")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()


# Made with Bob