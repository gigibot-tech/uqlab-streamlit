"""
Progressive Disclosure Streamlit App for Uncertainty Quantification
Inspired by MLflow UI pattern - each step appears only after previous is completed
"""

import sys
from pathlib import Path

# Ensure walaris package is importable
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC = _PROJECT_ROOT / "src"
for _path in (_SRC, _PROJECT_ROOT):
    _entry = str(_path)
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import streamlit as st
import requests
import pandas as pd
import os
from typing import Optional, Dict, Any

# Page config
st.set_page_config(
    page_title="UQ Experiment Builder",
    page_icon="🔬",
    layout="wide"
)

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")

# Custom CSS for progressive disclosure
st.markdown("""
<style>
.step-complete {
    background-color: rgba(76, 175, 80, 0.1);
    border-left: 4px solid #4CAF50;
    padding: 12px;
    border-radius: 4px;
    margin: 10px 0;
}

.step-active {
    background-color: rgba(33, 150, 243, 0.1);
    border-left: 4px solid #2196F3;
    padding: 20px;
    border-radius: 4px;
    margin: 10px 0;
}

.step-pending {
    opacity: 0.5;
    padding: 12px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


def selectbox_without_default(label, options, help_text=None):
    """Selectbox that requires explicit selection (no default)"""
    options_with_empty = [''] + list(options)
    format_func = lambda x: '⬇️ Select one option' if x == '' else x
    return st.selectbox(label, options_with_empty, format_func=format_func, help=help_text)


def get_headers() -> dict:
    """Get request headers with optional authentication"""
    headers = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers


def fetch_dataset_stats(dataset_name: str, noise_type: str) -> Optional[dict]:
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
    st.title("🔬 Uncertainty Quantification Experiment Builder")
    st.caption("Progressive configuration workflow - complete each step to proceed")
    
    # Initialize session state
    if 'workflow' not in st.session_state:
        st.session_state.workflow = {
            'step1_complete': False,
            'step2_complete': False,
            'step3_complete': False,
            'step4_complete': False,
            'dataset_config': {},
            'training_config': {},
            'uncertainty_config': {},
            'evaluation_config': {},
        }
    
    workflow = st.session_state.workflow
    
    # Sidebar - Progress Tracker
    with st.sidebar:
        st.markdown("### ⚙️ Configuration Progress")
        st.markdown("---")
        
        steps = [
            ("📊", "Dataset Selection", workflow['step1_complete']),
            ("🧠", "Training Setup", workflow['step2_complete']),
            ("🎲", "Uncertainty Config", workflow['step3_complete']),
            ("📊", "Evaluation Setup", workflow['step4_complete']),
        ]
        
        for icon, name, complete in steps:
            if complete:
                st.markdown(f"✅ {icon} **{name}**")
            else:
                st.markdown(f"⬜ {icon} {name}")
        
        st.markdown("---")
        
        # Reset button
        if st.button("🔄 Start Over", help="Reset all configuration"):
            st.session_state.workflow = {
                'step1_complete': False,
                'step2_complete': False,
                'step3_complete': False,
                'step4_complete': False,
                'dataset_config': {},
                'training_config': {},
                'uncertainty_config': {},
                'evaluation_config': {},
            }
            st.rerun()
    
    # ========== STEP 1: DATASET SELECTION ==========
    if workflow['step1_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            dataset_name = workflow['dataset_config']['dataset_name']
            noise_type = workflow['dataset_config'].get('noise_type', 'none')
            st.markdown(f"**✅ Step 1: Dataset** - {dataset_name.upper()} ({noise_type})")
        with col2:
            if st.button("Edit", key="edit_step1"):
                workflow['step1_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 📊 Step 1: Dataset Selection")
        
        # Dataset selection
        dataset_choice = selectbox_without_default(
            "Choose a dataset",
            ["cifar10"],
            help_text="CIFAR-10: 50,000 training images, 10 classes"
        )
        
        if not dataset_choice:
            st.info("👆 Please select a dataset to continue")
            st.stop()
        
        # Noise type selection
        noise_options = ["none", "worse_label", "random_label1", "random_label2"]
        noise_choice = st.selectbox(
            "Label noise type",
            noise_options,
            index=0,
            help="CIFAR-10N provides synthetic noisy labels for uncertainty research"
        )
        
        # Fetch and display stats
        with st.spinner("Loading dataset statistics..."):
            stats = fetch_dataset_stats(dataset_choice, noise_choice)
        
        if stats:
            st.markdown("#### Dataset Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Samples", f"{stats.get('total_samples', 50000):,}")
            with col2:
                st.metric("Classes", stats.get('num_classes', 10))
            with col3:
                noise_rate = stats.get('noise_rate', 0.0)
                st.metric("Noise Rate", f"{noise_rate:.1%}" if noise_choice != "none" else "0%")
            
            # Show dataset preview
            with st.expander("📋 View dataset details"):
                st.json(stats)
            
            # Continue button
            if st.button("✓ Continue to Training Setup", type="primary", use_container_width=True):
                workflow['step1_complete'] = True
                workflow['dataset_config'] = {
                    'dataset_name': dataset_choice,
                    'noise_type': noise_choice,
                    'stats': stats
                }
                st.rerun()
        else:
            st.error("Failed to load dataset. Please check backend connection.")
            st.stop()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()  # Don't show next steps until this is complete
    
    # ========== STEP 2: TRAINING SETUP ==========
    if workflow['step2_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            if workflow['training_config'].get('use_checkpoint'):
                checkpoint_id = workflow['training_config']['checkpoint_id']
                st.markdown(f"**✅ Step 2: Training** - Using checkpoint: {checkpoint_id}")
            else:
                model_arch = workflow['training_config']['model_architecture']
                epochs = workflow['training_config']['epochs']
                st.markdown(f"**✅ Step 2: Training** - {model_arch}, {epochs} epochs")
        with col2:
            if st.button("Edit", key="edit_step2"):
                workflow['step2_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 🧠 Step 2: Training Setup")
        
        # Training mode selection
        training_mode = st.radio(
            "Training mode",
            ["Train new model", "Use existing checkpoint"],
            help="Train a new model or load a pre-trained checkpoint"
        )
        
        if training_mode == "Train new model":
            st.markdown("#### Model Configuration")
            
            col1, col2 = st.columns(2)
            with col1:
                model_arch = st.selectbox(
                    "Model architecture",
                    ["dinov2-small", "dinov2-base", "resnet18", "resnet50"],
                    help="DINOv2 models are pre-trained vision transformers"
                )
                hidden_dim = st.number_input("Hidden dimension", min_value=64, max_value=1024, value=256, step=64)
                dropout = st.slider("Dropout rate", 0.0, 0.5, 0.2, 0.05)
            
            with col2:
                epochs = st.number_input("Training epochs", min_value=1, max_value=100, value=12)
                learning_rate = st.number_input("Learning rate", min_value=0.0001, max_value=0.1, value=0.001, format="%.4f")
                batch_size = st.selectbox("Batch size", [64, 128, 256, 512], index=2)
            
            if st.button("✓ Continue to Uncertainty Configuration", type="primary", use_container_width=True):
                workflow['step2_complete'] = True
                workflow['training_config'] = {
                    'use_checkpoint': False,
                    'model_architecture': model_arch,
                    'hidden_dim': hidden_dim,
                    'dropout': dropout,
                    'epochs': epochs,
                    'learning_rate': learning_rate,
                    'batch_size': batch_size
                }
                st.rerun()
        
        else:  # Use existing checkpoint
            st.markdown("#### Select Checkpoint")
            
            # Fetch available checkpoints
            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/v1/experiments/no-auth",
                    headers=get_headers(),
                    timeout=10
                )
                response.raise_for_status()
                experiments = response.json()
                
                # Filter completed experiments
                completed_exps = [
                    exp for exp in experiments 
                    if exp.get('status') == 'completed'
                ]
                
                if completed_exps:
                    checkpoint_options = [
                        f"{exp['name']} (ID: {exp['id']})" 
                        for exp in completed_exps
                    ]
                    checkpoint_choice = selectbox_without_default(
                        "Select checkpoint",
                        checkpoint_options,
                        help_text="Choose a completed experiment to use as checkpoint"
                    )
                    
                    if checkpoint_choice:
                        # Extract experiment ID
                        checkpoint_id = checkpoint_choice.split("ID: ")[1].rstrip(")")
                        
                        if st.button("✓ Continue to Uncertainty Configuration", type="primary", use_container_width=True):
                            workflow['step2_complete'] = True
                            workflow['training_config'] = {
                                'use_checkpoint': True,
                                'checkpoint_id': checkpoint_id
                            }
                            st.rerun()
                    else:
                        st.info("👆 Please select a checkpoint to continue")
                else:
                    st.warning("No completed experiments found. Please train a new model.")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to fetch experiments: {str(e)}")
                st.info("Falling back to training new model...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # ========== STEP 3: UNCERTAINTY CONFIGURATION ==========
    if workflow['step3_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            epis_enabled = workflow['uncertainty_config'].get('epistemic_enabled', False)
            alea_enabled = workflow['uncertainty_config'].get('aleatoric_enabled', False)
            st.markdown(f"**✅ Step 3: Uncertainty** - Epistemic: {epis_enabled}, Aleatoric: {alea_enabled}")
        with col2:
            if st.button("Edit", key="edit_step3"):
                workflow['step3_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 🎲 Step 3: Uncertainty Configuration")
        
        col1, col2 = st.columns(2)
        
        # Epistemic Uncertainty (Dataset Size)
        with col1:
            st.markdown("#### Epistemic Uncertainty")
            st.caption("Model uncertainty due to limited training data")
            
            epistemic_enabled = st.checkbox("Enable dataset size sweep", value=True)
            
            if epistemic_enabled:
                under_supported_mode = st.radio(
                    "Under-supported classes",
                    ["Random selection", "Manual selection"],
                    help="Classes with limited training data"
                )
                
                if under_supported_mode == "Random selection":
                    num_under = st.slider("Number of under-supported classes", 1, 5, 2)
                    under_supported = f"random:{num_under}"
                else:
                    class_names = ["airplane", "automobile", "bird", "cat", "deer", 
                                 "dog", "frog", "horse", "ship", "truck"]
                    selected_classes = st.multiselect(
                        "Select under-supported classes",
                        class_names,
                        default=class_names[:2]
                    )
                    under_supported = ",".join([str(class_names.index(c)) for c in selected_classes])
                
                under_train_per_class = st.number_input(
                    "Samples per under-supported class",
                    min_value=10, max_value=500, value=50, step=10
                )
                regular_train_per_class = st.number_input(
                    "Samples per regular class",
                    min_value=50, max_value=1000, value=300, step=50
                )
            else:
                under_supported = None
                under_train_per_class = None
                regular_train_per_class = None
        
        # Aleatoric Uncertainty (Label Noise)
        with col2:
            st.markdown("#### Aleatoric Uncertainty")
            st.caption("Data uncertainty due to label noise")
            
            noise_type = workflow['dataset_config'].get('noise_type', 'none')
            
            if noise_type != 'none':
                aleatoric_enabled = st.checkbox(
                    f"Use dataset noise ({noise_type})",
                    value=True,
                    help=f"Use CIFAR-10N {noise_type} noise labels"
                )
                custom_noise = None
            else:
                aleatoric_enabled = st.checkbox("Add custom label noise", value=False)
                if aleatoric_enabled:
                    custom_noise = st.slider(
                        "Custom noise rate (%)",
                        0, 50, 10, 5
                    ) / 100.0
                else:
                    custom_noise = None
        
        # Dataset preview
        if epistemic_enabled:
            st.markdown("#### Dataset Configuration Preview")
            if under_supported and under_train_per_class and regular_train_per_class:
                if under_supported.startswith("random:"):
                    num_under = int(under_supported.split(":")[1])
                else:
                    num_under = len(under_supported.split(","))
                
                num_regular = 10 - num_under
                under_samples = num_under * under_train_per_class
                regular_samples = num_regular * regular_train_per_class
                total_samples = under_samples + regular_samples
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Under-supported", f"{under_samples:,} samples")
                with col2:
                    st.metric("Regular classes", f"{regular_samples:,} samples")
                with col3:
                    st.metric("Total training", f"{total_samples:,} samples")
        
        # Continue button
        if st.button("✓ Continue to Evaluation Setup", type="primary", use_container_width=True):
            workflow['step3_complete'] = True
            workflow['uncertainty_config'] = {
                'epistemic_enabled': epistemic_enabled,
                'under_supported': under_supported if epistemic_enabled else None,
                'under_train_per_class': under_train_per_class if epistemic_enabled else None,
                'regular_train_per_class': regular_train_per_class if epistemic_enabled else None,
                'aleatoric_enabled': aleatoric_enabled,
                'custom_noise_rate': custom_noise if aleatoric_enabled else None
            }
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # ========== STEP 4: EVALUATION SETUP ==========
    if workflow['step4_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            eval_per_group = workflow['evaluation_config']['eval_per_group']
            mc_passes = workflow['evaluation_config']['mc_passes']
            st.markdown(f"**✅ Step 4: Evaluation** - {eval_per_group} samples/group, {mc_passes} MC passes")
        with col2:
            if st.button("Edit", key="edit_step4"):
                workflow['step4_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 📊 Step 4: Evaluation Setup")
        
        st.markdown("#### Evaluation Pool Configuration")
        
        # Calculate available samples
        dataset_stats = workflow['dataset_config'].get('stats', {})
        total_samples = dataset_stats.get('total_samples', 50000)
        
        # Estimate training samples used
        if workflow['uncertainty_config'].get('epistemic_enabled'):
            under_train = workflow['uncertainty_config'].get('under_train_per_class', 50)
            regular_train = workflow['uncertainty_config'].get('regular_train_per_class', 300)
            under_supported = workflow['uncertainty_config'].get('under_supported', 'random:2')
            
            if under_supported.startswith("random:"):
                num_under = int(under_supported.split(":")[1])
            else:
                num_under = len(under_supported.split(","))
            
            num_regular = 10 - num_under
            estimated_train = (num_under * under_train) + (num_regular * regular_train)
        else:
            estimated_train = 2500  # Default estimate
        
        available_for_eval = total_samples - estimated_train
        
        st.info(f"📊 Estimated available for evaluation: ~{available_for_eval:,} samples")
        
        # Evaluation configuration
        col1, col2 = st.columns(2)
        
        with col1:
            eval_per_group = st.number_input(
                "Samples per evaluation group",
                min_value=50,
                max_value=500,
                value=100,
                step=50,
                help="Number of samples to evaluate per group (under-supported, regular-clean, regular-noisy)"
            )
            
            # Calculate total evaluation samples
            num_groups = 3 if workflow['uncertainty_config'].get('epistemic_enabled') else 2
            total_eval = eval_per_group * num_groups
            st.caption(f"Total evaluation samples: {total_eval:,}")
        
        with col2:
            mc_passes = st.number_input(
                "MC Dropout passes",
                min_value=1,
                max_value=50,
                value=20,
                help="Number of forward passes with dropout for uncertainty estimation"
            )
        
        # Uncertainty signals selection
        st.markdown("#### Uncertainty Signals")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Epistemic Signals**")
            epistemic_signals = []
            if st.checkbox("inverse_mass", value=True):
                epistemic_signals.append("inverse_mass")
            if st.checkbox("dominance", value=True):
                epistemic_signals.append("dominance")
            if st.checkbox("inverse_logit_magnitude", value=True):
                epistemic_signals.append("inverse_logit_magnitude")
        
        with col2:
            st.markdown("**Aleatoric Signals**")
            aleatoric_signals = []
            if st.checkbox("inverse_coherence", value=True):
                aleatoric_signals.append("inverse_coherence")
        
        with col3:
            st.markdown("**Baseline Signals**")
            baseline_signals = []
            if st.checkbox("msp_uncertainty", value=True):
                baseline_signals.append("msp_uncertainty")
            if st.checkbox("predictive_entropy", value=True):
                baseline_signals.append("predictive_entropy")
            if st.checkbox("mutual_info", value=False):
                baseline_signals.append("mutual_info")
        
        all_signals = epistemic_signals + aleatoric_signals + baseline_signals
        
        if not all_signals:
            st.warning("⚠️ Please select at least one uncertainty signal")
            st.stop()
        
        # Continue to review
        if st.button("✓ Review & Launch Experiment", type="primary", use_container_width=True):
            workflow['step4_complete'] = True
            workflow['evaluation_config'] = {
                'eval_per_group': eval_per_group,
                'mc_passes': mc_passes,
                'selected_signals': all_signals
            }
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # ========== STEP 5: REVIEW & LAUNCH ==========
    st.markdown('<div class="step-active">', unsafe_allow_html=True)
    st.markdown("### 🚀 Step 5: Review & Launch")
    
    # Experiment name
    exp_name = st.text_input(
        "Experiment name",
        value=f"exp_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
        help="Unique name for this experiment"
    )
    
    # Configuration summary
    st.markdown("#### Configuration Summary")
    
    with st.expander("📊 Dataset Configuration", expanded=True):
        dataset_config = workflow['dataset_config']
        st.write(f"**Dataset:** {dataset_config['dataset_name'].upper()}")
        st.write(f"**Noise type:** {dataset_config.get('noise_type', 'none')}")
        st.write(f"**Total samples:** {dataset_config['stats'].get('total_samples', 0):,}")
    
    with st.expander("🧠 Training Configuration", expanded=True):
        training_config = workflow['training_config']
        if training_config.get('use_checkpoint'):
            st.write(f"**Mode:** Using checkpoint")
            st.write(f"**Checkpoint ID:** {training_config['checkpoint_id']}")
        else:
            st.write(f"**Mode:** Train new model")
            st.write(f"**Architecture:** {training_config['model_architecture']}")
            st.write(f"**Epochs:** {training_config['epochs']}")
            st.write(f"**Learning rate:** {training_config['learning_rate']}")
    
    with st.expander("🎲 Uncertainty Configuration", expanded=True):
        uncertainty_config = workflow['uncertainty_config']
        st.write(f"**Epistemic enabled:** {uncertainty_config['epistemic_enabled']}")
        if uncertainty_config['epistemic_enabled']:
            st.write(f"**Under-supported:** {uncertainty_config['under_supported']}")
            st.write(f"**Under-supported samples:** {uncertainty_config['under_train_per_class']}")
            st.write(f"**Regular samples:** {uncertainty_config['regular_train_per_class']}")
        st.write(f"**Aleatoric enabled:** {uncertainty_config['aleatoric_enabled']}")
    
    with st.expander("📊 Evaluation Configuration", expanded=True):
        evaluation_config = workflow['evaluation_config']
        st.write(f"**Samples per group:** {evaluation_config['eval_per_group']}")
        st.write(f"**MC dropout passes:** {evaluation_config['mc_passes']}")
        st.write(f"**Signals:** {', '.join(evaluation_config['selected_signals'])}")
    
    # Launch button
    col1, col2 = st.columns([3, 1])
    with col1:
        launch_button = st.button("🚀 Launch Experiment", type="primary", use_container_width=True)
    with col2:
        if st.button("← Start Over", use_container_width=True):
            st.session_state.workflow = {
                'step1_complete': False,
                'step2_complete': False,
                'step3_complete': False,
                'step4_complete': False,
                'dataset_config': {},
                'training_config': {},
                'uncertainty_config': {},
                'evaluation_config': {},
            }
            st.rerun()
    
    if launch_button:
        with st.spinner("Creating experiment..."):
            try:
                # Build experiment config
                from ui_components import build_base_experiment_config
                
                experiment_data = {
                    "name": exp_name,
                    "config": build_base_experiment_config(
                        noise_type=workflow['dataset_config'].get('noise_type', 'none'),
                        under_supported=workflow['uncertainty_config'].get('under_supported'),
                        under_train_per_class=workflow['uncertainty_config'].get('under_train_per_class', 50),
                        regular_train_per_class=workflow['uncertainty_config'].get('regular_train_per_class', 300),
                        dinov2_model=workflow['training_config'].get('model_architecture', 'dinov2-small'),
                        hidden_dim=workflow['training_config'].get('hidden_dim', 256),
                        dropout=workflow['training_config'].get('dropout', 0.2),
                        epochs=workflow['training_config'].get('epochs', 12),
                        learning_rate=workflow['training_config'].get('learning_rate', 0.001),
                        weight_decay=0.0001,
                        train_batch_size=workflow['training_config'].get('batch_size', 256),
                        eval_per_group=workflow['evaluation_config']['eval_per_group'],
                        mc_passes=workflow['evaluation_config']['mc_passes'],
                        use_untrained_resnet=False,
                        aleatoric_noise_percentage=((workflow['uncertainty_config'].get('custom_noise_rate') or 0.0) * 100) if workflow['uncertainty_config'].get('custom_noise_rate') is not None else 0.0,
                    )
                }
                
                # Create experiment
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
                
                with st.expander("📋 View full response"):
                    st.json(result)
                
                # Reset workflow
                if st.button("Create Another Experiment"):
                    st.session_state.workflow = {
                        'step1_complete': False,
                        'step2_complete': False,
                        'step3_complete': False,
                        'step4_complete': False,
                        'dataset_config': {},
                        'training_config': {},
                        'uncertainty_config': {},
                        'evaluation_config': {},
                    }
                    st.rerun()
                
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to create experiment: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    st.error(f"Response: {e.response.text}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <small>Uncertainty Quantification Experiment Builder | Progressive Disclosure UI</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

# Made with Bob
