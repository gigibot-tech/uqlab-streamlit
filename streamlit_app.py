"""
Streamlit Dashboard for Uncertainty Quantification
Connects to the FastAPI backend to display dataset statistics and experiment results
"""

import streamlit as st
import requests
import pandas as pd
import os
from typing import Optional

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
    st.title("📊 Uncertainty Quantification Dashboard")
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        dataset_name = st.selectbox(
            "Dataset",
            ["cifar10n"],
            help="Select the dataset to analyze"
        )
        noise_type = st.selectbox(
            "Noise Type",
            ["worse_label", "aggre_label", "random_label1", "random_label2", "random_label3"],
            help="Type of label noise in the dataset"
        )
        
        st.markdown("---")
        st.markdown(f"**API Endpoint:** `{API_BASE_URL}`")
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Fetch data
    with st.spinner("Loading dataset statistics..."):
        stats = fetch_dataset_stats(dataset_name, noise_type)
    
    if not stats:
        st.warning("No data available. Make sure the backend API is running.")
        st.code(f"Backend URL: {API_BASE_URL}")
        st.info("💡 Start the backend with: `docker-compose up backend`")
        return
    
    # Display summary metrics
    st.header("📈 Dataset Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Samples",
            value=f"{stats.get('total_samples', 0):,}"
        )
    
    with col2:
        st.metric(
            label="Clean Samples",
            value=f"{stats.get('clean_samples', 0):,}",
            delta=None,
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            label="Noisy Samples",
            value=f"{stats.get('noisy_samples', 0):,}",
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        noise_rate = stats.get('noise_rate', 0) * 100
        st.metric(
            label="Overall Noise Rate",
            value=f"{noise_rate:.1f}%"
        )
    
    st.markdown("---")
    
    # Noise distribution by class
    st.header("🎯 Noise Distribution by Class")
    
    noise_per_class = stats.get('noise_per_class', {})
    class_names = stats.get('class_names', [])
    
    if noise_per_class:
        # Prepare data for table
        table_data = []
        for class_id, data in noise_per_class.items():
            # class_names is a list, use index to get name
            class_idx = int(class_id)
            class_name = class_names[class_idx] if class_idx < len(class_names) else f"Class {class_id}"
            total = data.get('total', 0)
            noisy = data.get('noisy', 0)
            clean = total - noisy
            rate = data.get('rate', 0) * 100
            
            table_data.append({
                "Class": class_name,
                "Total Samples": total,
                "Clean": clean,
                "Noisy": noisy,
                "Noise Rate": f"{rate:.1f}%"
            })
        
        df = pd.DataFrame(table_data)
        
        # Display as table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Visualization
        st.subheader("📊 Noise Rate by Class")
        chart_data = df[["Class", "Noise Rate"]].copy()
        chart_data["Noise Rate"] = chart_data["Noise Rate"].str.rstrip('%').astype(float)
        st.bar_chart(chart_data.set_index("Class"))
    else:
        st.info("No class-level noise distribution data available.")
    
    st.markdown("---")
    
    # Experiment section
    st.header("🧪 Experiments")
    
    tab1, tab2 = st.tabs(["Run Experiment", "View Results"])
    
    with tab1:
        st.subheader("Configure and Run Experiment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            exp_name = st.text_input("Experiment Name", value="test_experiment")
            model_type = st.selectbox("Model Type", ["resnet18", "resnet34", "resnet50"])
            epochs = st.number_input("Epochs", min_value=1, max_value=100, value=10)
        
        with col2:
            batch_size = st.number_input("Batch Size", min_value=1, max_value=512, value=32)
            learning_rate = st.number_input("Learning Rate", min_value=0.0001, max_value=1.0, value=0.001, format="%.4f")
            uncertainty_method = st.selectbox("Uncertainty Method", ["ensemble", "mc_dropout", "deep_ensemble"])
        
        if st.button("🚀 Start Experiment", type="primary"):
            st.info("Experiment functionality coming soon! This will trigger training via the backend API.")
            st.code(f"""
POST {API_BASE_URL}/api/v1/experiments/
{{
    "name": "{exp_name}",
    "dataset_name": "{dataset_name}",
    "model_type": "{model_type}",
    "config": {{
        "epochs": {epochs},
        "batch_size": {batch_size},
        "learning_rate": {learning_rate},
        "uncertainty_method": "{uncertainty_method}"
    }}
}}
            """)
    
    with tab2:
        st.subheader("Experiment Results")
        st.info("Results viewer coming soon! This will display completed experiments and their metrics.")
    
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
