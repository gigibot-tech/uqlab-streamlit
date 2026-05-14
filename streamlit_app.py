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
        st.success("✅ Logged in as: **test@example.com**")
        st.caption("(Auto-created test user)")
        
        st.markdown("---")
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
        
        with st.form("experiment_form"):
            exp_name = st.text_input("Experiment Name", value=f"exp_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}")
            
            st.markdown("#### Data Configuration")
            col1, col2 = st.columns(2)
            with col1:
                under_supported = st.text_input("Under-supported Classes", value="3,5", help="Comma-separated class IDs")
                under_train_per_class = st.number_input("Under-supported Samples/Class", min_value=10, max_value=500, value=50)
            with col2:
                regular_train_per_class = st.number_input("Regular Samples/Class", min_value=50, max_value=1000, value=300)
                eval_per_group = st.number_input("Eval Samples/Group", min_value=100, max_value=2000, value=600)
            
            st.markdown("#### Model Configuration")
            col1, col2, col3 = st.columns(3)
            with col1:
                dinov2_model = st.selectbox("DINOv2 Model", ["small", "base", "large"], index=0)
            with col2:
                hidden_dim = st.number_input("Hidden Dimension", min_value=64, max_value=1024, value=256, step=64)
            with col3:
                dropout = st.number_input("Dropout", min_value=0.0, max_value=0.9, value=0.2, step=0.1)
            
            st.markdown("#### Training Configuration")
            col1, col2, col3 = st.columns(3)
            with col1:
                epochs = st.number_input("Epochs", min_value=1, max_value=100, value=12)
            with col2:
                learning_rate = st.number_input("Learning Rate", min_value=0.0001, max_value=0.1, value=0.001, format="%.4f")
            with col3:
                weight_decay = st.number_input("Weight Decay", min_value=0.0, max_value=0.01, value=0.0001, format="%.5f")
            
            train_batch_size = st.number_input("Training Batch Size", min_value=16, max_value=512, value=256, step=16)
            
            st.markdown("#### Evaluation Configuration")
            col1, col2 = st.columns(2)
            with col1:
                mc_passes = st.number_input("MC Dropout Passes", min_value=5, max_value=100, value=20)
            with col2:
                attribution_method = st.selectbox("Attribution Method", ["dualxda", "gradcam", "integrated_gradients"])
            
            submitted = st.form_submit_button("🚀 Create Experiment", type="primary")
            
            if submitted:
                with st.spinner("Creating experiment..."):
                    try:
                        # Prepare experiment data
                        experiment_data = {
                            "name": exp_name,
                            "config": {
                                "noise_type": noise_type,
                                "under_supported_classes": under_supported,
                                "under_train_per_class": under_train_per_class,
                                "regular_train_per_class": regular_train_per_class,
                                "eval_per_group": eval_per_group,
                                "dinov2_model": dinov2_model,
                                "hidden_dim": hidden_dim,
                                "dropout": dropout,
                                "epochs": epochs,
                                "learning_rate": learning_rate,
                                "weight_decay": weight_decay,
                                "train_batch_size": train_batch_size,
                                "mc_passes": mc_passes,
                                "attribution_method": attribution_method,
                            }
                        }
                        
                        # Create experiment (using no-auth endpoint)
                        response = requests.post(
                            f"{API_BASE_URL}/api/v1/experiments/no-auth",
                            json=experiment_data,
                            headers=get_headers(),
                            timeout=30
                        )
                        response.raise_for_status()
                        result = response.json()
                        
                        st.success(f"✅ Experiment created: {result['name']}")
                        st.info(f"Experiment ID: {result['id']}")
                        st.info(f"Status: {result['status']}")
                        st.json(result)
                        
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to create experiment: {str(e)}")
                        if hasattr(e, 'response') and e.response is not None:
                            st.error(f"Response: {e.response.text}")
    
    with tab2:
        st.subheader("Experiment Results")
        
        if st.button("🔄 Refresh Experiments"):
            st.rerun()
        
        try:
            # Fetch experiments using no-auth endpoint
            response = requests.get(
                f"{API_BASE_URL}/api/v1/experiments/no-auth",
                headers=get_headers(),
                timeout=10
            )
            response.raise_for_status()
            experiments = response.json()
            
            if not experiments:
                st.info("No experiments found. Create one in the 'Run Experiment' tab!")
            else:
                # Display experiments table
                exp_data = []
                for exp in experiments:
                    exp_data.append({
                        "Name": exp["name"],
                        "Status": exp["status"],
                        "Progress": f"{exp.get('progress', 0):.1%}",
                        "Created": pd.to_datetime(exp["created_at"]).strftime("%Y-%m-%d %H:%M"),
                        "Aleatoric AUROC": f"{exp['aleatoric_auroc']:.3f}" if exp.get('aleatoric_auroc') else "N/A",
                        "Epistemic AUROC": f"{exp['epistemic_auroc']:.3f}" if exp.get('epistemic_auroc') else "N/A",
                    })
                
                df_exp = pd.DataFrame(exp_data)
                st.dataframe(df_exp, use_container_width=True, hide_index=True)
                
                st.caption(f"Total experiments: {len(experiments)}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch experiments: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                st.error(f"Response: {e.response.text}")
    
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
