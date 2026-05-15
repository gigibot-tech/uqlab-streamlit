"""
Streamlit Dashboard for Uncertainty Quantification
Connects to the FastAPI backend to display dataset statistics and experiment results
"""

import streamlit as st
import requests
import pandas as pd
import os
from typing import Optional

# Import UI components
from ui_components import (
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
    render_experiment_results
)

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
    
    st.subheader("Create New Experiment")
    
    with st.form("experiment_form"):
            exp_name = st.text_input("Experiment Name", value=f"exp_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}")
            
            # CIFAR-10 class names
            class_names = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
            
            # ========== DATASET CONFIGURATION ==========
            st.markdown("### 📦 Dataset Configuration")
            st.info("**CIFAR-10N Dataset**: 10 classes with synthetic label noise for uncertainty quantification research")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Available Classes:**")
                # Display with consistent formatting (space after colon)
                st.write(", ".join([f"{i}: {name}" for i, name in enumerate(class_names)]))
            with col2:
                st.metric("Total Classes", "10")
            
            st.markdown("---")
            
            # ========== EPISTEMIC & ALEATORIC UNCERTAINTY (IN ONE ROW) ==========
            col_epistemic, col_aleatoric = st.columns(2)
            
            # ========== EPISTEMIC UNCERTAINTY CONFIGURATION ==========
            with col_epistemic:
                under_supported, under_train_per_class, regular_train_per_class, epistemic_complete = render_epistemic_config(
                    class_names, 
                    default_under_train=50, 
                    default_regular_train=300
                )
                st.session_state.config_progress['epistemic'] = epistemic_complete
            
            # ========== ALEATORIC UNCERTAINTY CONFIGURATION ==========
            with col_aleatoric:
                noise_source, custom_noise_rate = render_aleatoric_config(
                    stats,
                    noise_type,
                    class_names,
                    fetch_dataset_stats,
                    dataset_name
                )
                # Update aleatoric progress
                st.session_state.config_progress['aleatoric'] = True  # Always complete if noise source selected
            
            st.markdown("---")
            
            # ========== DATASET COMPARISON ==========
            # Visual connection indicator
            st.markdown("""
            <div class='connection-box'>
                <div class='connection-text'>
                    💡 Epistemic & Aleatoric settings above directly affect the training data distribution below
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Get noise rate for dataset comparison
            if noise_source == "Use CIFAR-10N noise" and stats:
                noise_rate_for_comparison = stats.get('noise_rate', 0)
            else:
                noise_rate_for_comparison = custom_noise_rate / 100.0
            
            # Note: We'll show a preview here, but full details come after eval_per_group is defined
            st.markdown("### 📊 Dataset Configuration Preview")
            st.caption("💡 Values update when you submit the form")
            
            # Parse under-supported classes for preview
            if under_supported.startswith("random:"):
                num_under_preview = int(under_supported.split(":")[1])
            else:
                num_under_preview = len(under_supported.split(",")) if under_supported else 2
            
            num_regular_preview = 10 - num_under_preview
            under_samples_preview = num_under_preview * under_train_per_class
            regular_samples_preview = num_regular_preview * regular_train_per_class
            total_train_preview = under_samples_preview + regular_samples_preview
            
            st.markdown(f"""
            **Training Dataset Preview:**
            ```
            Under-supported: {num_under_preview} classes × {under_train_per_class} samples = {under_samples_preview:,} samples
            Regular classes: {num_regular_preview} classes × {regular_train_per_class} samples = {regular_samples_preview:,} samples
              ├─ Clean: {regular_samples_preview:,} × {(1-noise_rate_for_comparison):.1%} = {int(regular_samples_preview * (1-noise_rate_for_comparison)):,} samples
              └─ Noisy: {regular_samples_preview:,} × {noise_rate_for_comparison:.1%} = {int(regular_samples_preview * noise_rate_for_comparison):,} samples
            
            Total Training = {under_samples_preview:,} + {regular_samples_preview:,} = {total_train_preview:,} samples
            ```
            """)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Training", f"{total_train_preview:,}")
            with col2:
                st.metric("Under-supported", f"{under_samples_preview:,}", f"{num_under_preview} classes")
            with col3:
                st.metric("Regular (Clean+Noisy)", f"{regular_samples_preview:,}", f"{num_regular_preview} classes")
            
            st.markdown("---")
            
            # ========== MODEL & TRAINING CONFIGURATION ==========
            st.markdown("### 🧠 Model & Training Configuration")
            st.markdown("""
            <div style="background-color: rgba(76, 175, 80, 0.05); padding: 8px; border-radius: 4px; margin-bottom: 10px;">
                <small>📊 Training data shaped by dataset configuration above</small>
            </div>
            """, unsafe_allow_html=True)
        
            st.markdown("**Model Architecture**")
            dinov2_model, hidden_dim, dropout = render_model_config()
            
            epochs, learning_rate, weight_decay, train_batch_size = render_training_config()
            
            # Update model progress
            st.session_state.config_progress['model'] = True  # Complete if model selected
            
            st.markdown("---")
            
            # ========== EVALUATION CONFIGURATION ==========
            st.markdown("### 📊 Evaluation Configuration")
            st.info("💡 Configure how uncertainty is measured and evaluated")
            
            mc_passes, selected_signals, eval_per_group = render_evaluation_config()
            
            # ========== COMPLETE DATASET COMPARISON (now that eval_per_group is defined) ==========
            st.markdown("---")
            st.markdown("### 📊 Complete Dataset Configuration")
            st.info("Full dataset breakdown including evaluation groups")
            
            render_dataset_comparison(
                under_supported,
                under_train_per_class,
                regular_train_per_class,
                noise_source,
                stats,
                noise_type,
                custom_noise_rate,
                class_names,
                eval_per_group
            )
            
            # Update evaluation progress
            st.session_state.config_progress['evaluation'] = mc_passes > 0
            
            st.markdown("---")
            
            # ========== PHASE 3: EVALUATION DATASET EXPLANATION ==========
            render_evaluation_strategy(eval_per_group, under_supported, class_names)
            
            # ========== PHASE 3: ROC CALCULATION EXAMPLE ==========
            render_roc_explanation(under_supported, class_names, noise_source, custom_noise_rate)
            
            st.markdown("---")
            submitted = st.form_submit_button("🚀 Create Experiment", type="primary", use_container_width=True)
            
            if submitted:
                with st.spinner("Creating experiment..."):
                    try:
                        # Prepare experiment data with organized sections
                        experiment_data = {
                            "name": exp_name,
                            "config": {
                                # Dataset configuration
                                "dataset": "cifar10n",
                                "noise_type": noise_type,
                                
                                # Epistemic uncertainty configuration
                                "under_supported_classes": under_supported,
                                "under_train_per_class": under_train_per_class,
                                "regular_train_per_class": regular_train_per_class,
                                
                                # Aleatoric uncertainty configuration
                                "noise_source": noise_source,
                                "custom_noise_rate": custom_noise_rate,
                                
                                # Model configuration
                                "dinov2_model": dinov2_model,
                                "hidden_dim": hidden_dim,
                                "dropout": dropout,
                                
                                # Training configuration
                                "epochs": epochs,
                                "learning_rate": learning_rate,
                                "weight_decay": weight_decay,
                                "train_batch_size": train_batch_size,
                                
                                # Evaluation configuration
                                "eval_per_group": eval_per_group,
                                "mc_passes": mc_passes,
                                "attribution_signals": selected_signals,
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
    
    # Display experiment results below the form
    st.markdown("---")
    st.subheader("📋 Experiment Results")
    
    # Auto-polling controls with session state
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    
    # Render experiment results with auto-refresh
    st.session_state.auto_refresh = render_experiment_results(
        API_BASE_URL,
        get_headers,
        st.session_state.auto_refresh
    )
    
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
