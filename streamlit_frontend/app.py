"""
Main Streamlit Application Entry Point
"""

import streamlit as st

from config import AppConfig
from pages import dataset_stats, experiments
from services.api_client import APIClient

# Page configuration
st.set_page_config(
    page_title="Uncertainty Quantification Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application entry point."""
    # Initialize configuration
    config = AppConfig()
    
    # Initialize API client (Singleton pattern)
    api_client = APIClient.get_instance(
        base_url=config.api_url,
        token=config.api_token
    )
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 UQ Dashboard")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["Dataset Statistics", "Experiments"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown(f"**API:** `{config.api_url}`")
        
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Route to appropriate page
    if page == "Dataset Statistics":
        dataset_stats.render(api_client)
    elif page == "Experiments":
        experiments.render(api_client)


if __name__ == "__main__":
    main()

# Made with Bob
