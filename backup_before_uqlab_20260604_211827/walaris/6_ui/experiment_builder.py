"""
Single Experiment Builder

Consolidated form for creating and configuring individual experiments.
Provides preset selection and custom configuration options.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

import streamlit as st
import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Models
# ============================================================================

class ExperimentConfig(BaseModel):
    """Experiment configuration."""
    # Dataset
    dataset: str = Field(default="cifar10", description="Dataset name")
    noise_type: str = Field(default="symmetric", description="Noise type")
    noise_rate: float = Field(default=0.2, ge=0.0, le=1.0, description="Noise rate")
    
    # Model
    architecture: str = Field(default="resnet18", description="Model architecture")
    pretrained: bool = Field(default=True, description="Use pretrained weights")
    
    # Training
    epochs: int = Field(default=50, ge=1, le=500, description="Number of epochs")
    batch_size: int = Field(default=128, ge=1, le=1024, description="Batch size")
    learning_rate: float = Field(default=0.001, ge=1e-6, le=1.0, description="Learning rate")
    optimizer: str = Field(default="adam", description="Optimizer")
    
    # Uncertainty
    mc_samples: int = Field(default=10, ge=1, le=100, description="MC dropout samples")
    dropout_rate: float = Field(default=0.1, ge=0.0, le=0.9, description="Dropout rate")


# ============================================================================
# Presets
# ============================================================================

PRESETS = {
    "quick_test": {
        "name": "Quick Test",
        "description": "Fast test run with minimal epochs",
        "config": {
            "dataset": "cifar10",
            "noise_type": "symmetric",
            "noise_rate": 0.2,
            "architecture": "resnet18",
            "pretrained": True,
            "epochs": 5,
            "batch_size": 128,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "mc_samples": 5,
            "dropout_rate": 0.1,
        }
    },
    "standard": {
        "name": "Standard Training",
        "description": "Standard configuration for production",
        "config": {
            "dataset": "cifar10",
            "noise_type": "symmetric",
            "noise_rate": 0.2,
            "architecture": "resnet18",
            "pretrained": True,
            "epochs": 50,
            "batch_size": 128,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "mc_samples": 10,
            "dropout_rate": 0.1,
        }
    },
    "high_uncertainty": {
        "name": "High Uncertainty",
        "description": "Optimized for uncertainty quantification",
        "config": {
            "dataset": "cifar10",
            "noise_type": "asymmetric",
            "noise_rate": 0.4,
            "architecture": "resnet34",
            "pretrained": True,
            "epochs": 100,
            "batch_size": 64,
            "learning_rate": 0.0005,
            "optimizer": "adam",
            "mc_samples": 20,
            "dropout_rate": 0.2,
        }
    },
}


# ============================================================================
# API Client
# ============================================================================

def create_experiment(name: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create experiment via API."""
    try:
        api_url = st.session_state.get("api_base_url", "http://localhost:8000")
        response = requests.post(
            f"{api_url}/api/v1/experiments/no-auth",
            json={
                "name": name,
                "config": config,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        st.error(f"Failed to create experiment: {str(e)}")
        return None


def start_experiment(experiment_id: str) -> bool:
    """Start experiment execution."""
    try:
        api_url = st.session_state.get("api_base_url", "http://localhost:8000")
        response = requests.post(
            f"{api_url}/api/v1/experiments/no-auth/{experiment_id}/start",
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to start experiment: {e}")
        st.error(f"Failed to start experiment: {str(e)}")
        return False


def list_experiments() -> list:
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
# UI Components
# ============================================================================

def render_preset_selector() -> Optional[Dict[str, Any]]:
    """Render preset selection UI."""
    st.markdown("### 📋 Quick Start with Presets")
    
    cols = st.columns(len(PRESETS))
    
    for idx, (preset_key, preset_data) in enumerate(PRESETS.items()):
        with cols[idx]:
            st.markdown(f"**{preset_data['name']}**")
            st.caption(preset_data['description'])
            if st.button(f"Use {preset_data['name']}", key=f"preset_{preset_key}", use_container_width=True):
                return preset_data['config']
    
    return None


def render_config_form(initial_config: Optional[Dict[str, Any]] = None) -> Optional[ExperimentConfig]:
    """Render configuration form."""
    st.markdown("### ⚙️ Custom Configuration")
    
    config = initial_config or {}
    
    # Dataset Section
    with st.expander("📊 Dataset Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dataset = st.selectbox(
                "Dataset",
                options=["cifar10", "cifar100", "mnist"],
                index=0 if not config else ["cifar10", "cifar100", "mnist"].index(config.get("dataset", "cifar10")),
            )
        
        with col2:
            noise_type = st.selectbox(
                "Noise Type",
                options=["symmetric", "asymmetric", "instance"],
                index=0 if not config else ["symmetric", "asymmetric", "instance"].index(config.get("noise_type", "symmetric")),
            )
        
        with col3:
            noise_rate = st.slider(
                "Noise Rate",
                min_value=0.0,
                max_value=1.0,
                value=config.get("noise_rate", 0.2),
                step=0.05,
            )
    
    # Model Section
    with st.expander("🧠 Model Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            architecture = st.selectbox(
                "Architecture",
                options=["resnet18", "resnet34", "resnet50", "vgg16", "densenet121"],
                index=0 if not config else ["resnet18", "resnet34", "resnet50", "vgg16", "densenet121"].index(config.get("architecture", "resnet18")),
            )
        
        with col2:
            pretrained = st.checkbox(
                "Use Pretrained Weights",
                value=config.get("pretrained", True),
            )
    
    # Training Section
    with st.expander("🎯 Training Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            epochs = st.number_input(
                "Epochs",
                min_value=1,
                max_value=500,
                value=config.get("epochs", 50),
            )
            
            batch_size = st.number_input(
                "Batch Size",
                min_value=1,
                max_value=1024,
                value=config.get("batch_size", 128),
            )
        
        with col2:
            learning_rate = st.number_input(
                "Learning Rate",
                min_value=1e-6,
                max_value=1.0,
                value=config.get("learning_rate", 0.001),
                format="%.6f",
            )
            
            optimizer = st.selectbox(
                "Optimizer",
                options=["adam", "sgd", "adamw"],
                index=0 if not config else ["adam", "sgd", "adamw"].index(config.get("optimizer", "adam")),
            )
    
    # Uncertainty Section
    with st.expander("🎲 Uncertainty Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            mc_samples = st.number_input(
                "MC Dropout Samples",
                min_value=1,
                max_value=100,
                value=config.get("mc_samples", 10),
            )
        
        with col2:
            dropout_rate = st.slider(
                "Dropout Rate",
                min_value=0.0,
                max_value=0.9,
                value=config.get("dropout_rate", 0.1),
                step=0.05,
            )
    
    # Create config object
    try:
        return ExperimentConfig(
            dataset=dataset,
            noise_type=noise_type,
            noise_rate=noise_rate,
            architecture=architecture,
            pretrained=pretrained,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            optimizer=optimizer,
            mc_samples=mc_samples,
            dropout_rate=dropout_rate,
        )
    except Exception as e:
        st.error(f"Invalid configuration: {e}")
        return None


def render_experiment_list():
    """Render list of existing experiments."""
    st.markdown("### 📝 Recent Experiments")
    
    experiments = list_experiments()
    
    if not experiments:
        st.info("No experiments yet. Create your first one above!")
        return
    
    # Display as table
    import pandas as pd
    
    df = pd.DataFrame([
        {
            "Name": exp.get("name", "N/A"),
            "Status": exp.get("status", "N/A"),
            "Progress": f"{exp.get('progress', 0):.1%}",
            "Created": exp.get("created_at", "N/A")[:19] if exp.get("created_at") else "N/A",
        }
        for exp in experiments[:10]  # Show last 10
    ])
    
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================================
# Main Render Function
# ============================================================================

def render():
    """Main render function for experiment builder."""
    
    # Preset selection
    selected_preset = render_preset_selector()
    
    st.markdown("---")
    
    # Configuration form
    config = render_config_form(initial_config=selected_preset)
    
    # Experiment name and creation
    st.markdown("---")
    st.markdown("### 🚀 Create Experiment")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        experiment_name = st.text_input(
            "Experiment Name",
            value=f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Unique name for this experiment",
        )
    
    with col2:
        create_button = st.button(
            "Create",
            type="primary",
            use_container_width=True,
            disabled=config is None,
        )
    
    with col3:
        create_and_start = st.button(
            "Create & Start",
            type="secondary",
            use_container_width=True,
            disabled=config is None,
        )
    
    # Handle creation
    if create_button or create_and_start:
        if not experiment_name:
            st.error("Please provide an experiment name")
        elif config is None:
            st.error("Invalid configuration")
        else:
            with st.spinner("Creating experiment..."):
                result = create_experiment(experiment_name, config.model_dump())
                
                if result:
                    st.success(f"✅ Experiment created: {result.get('id')}")
                    
                    if create_and_start:
                        with st.spinner("Starting experiment..."):
                            if start_experiment(result.get('id')):
                                st.success("✅ Experiment started!")
                            else:
                                st.warning("Experiment created but failed to start")
                    
                    # Refresh experiment list
                    st.rerun()
    
    st.markdown("---")
    
    # Show recent experiments
    render_experiment_list()


# Made with Bob