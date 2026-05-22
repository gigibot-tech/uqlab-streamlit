"""
Single Experiment Configuration UI Components

This module contains UI components for configuring single experiments,
including epistemic/aleatoric uncertainty, model architecture, training,
and evaluation settings.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple, Optional, Callable, Any


def render_epistemic_config(
    class_names: List[str],
    default_under_train: int = 50,
    default_regular_train: int = 300
) -> Tuple[str, int, int, bool]:
    """
    Render epistemic uncertainty configuration section.
    
    Args:
        class_names: List of class names for the dataset
        default_under_train: Default samples per under-supported class
        default_regular_train: Default samples per regular class
    
    Returns:
        Tuple of (under_supported_str, under_train_per_class, regular_train_per_class, epistemic_complete)
    """
    st.markdown("### 🔬 Epistemic Uncertainty")
    st.info("💡 Model uncertainty from insufficient training data. Created by under-sampling classes.")

    # Random vs Manual selection
    random_under_supported = st.checkbox(
        "Select under-supported classes randomly",
        value=False,
        help="If checked, classes will be randomly selected. Otherwise, you can manually choose them."
    )
    
    if random_under_supported:
        num_under_supported = st.number_input(
            "Number of under-supported classes",
            min_value=1, max_value=5, value=2,
            help="How many classes to randomly under-sample"
        )
        st.caption(f"✨ Will randomly select {num_under_supported} classes to under-sample")
        under_supported = f"random:{num_under_supported}"
        under_supported_list = []
    else:
        under_supported_list = st.multiselect(
            "Select under-supported classes",
            options=list(range(10)),
            format_func=lambda x: f"{x}: {class_names[x]}",
            default=[3, 5],
            help="These classes will have limited training samples, creating epistemic uncertainty",
            placeholder="Click to select classes..."
        )
        if under_supported_list:
            under_supported = ",".join(map(str, under_supported_list))
        else:
            st.warning("⚠️ Please select at least one class")
            under_supported = "3,5"
    
    subcol1, subcol2 = st.columns(2)
    with subcol1:
        under_train_per_class = st.number_input(
            "Under-supported samples/class",
            min_value=10, max_value=500, value=default_under_train,
            help="Limited samples create epistemic uncertainty"
        )
    with subcol2:
        regular_train_per_class = st.number_input(
            "Regular samples/class",
            min_value=50, max_value=1000, value=default_regular_train,
            help="Well-supported classes for comparison"
        )
    
    # Epistemic Strength Indicator
    if not random_under_supported and under_supported_list:
        render_epistemic_strength(under_supported_list, under_train_per_class, regular_train_per_class)
    
    # Update epistemic progress
    epistemic_complete = (
        (random_under_supported or len(under_supported_list) > 0) and
        under_train_per_class > 0 and
        regular_train_per_class > 0
    )
    
    return under_supported, under_train_per_class, regular_train_per_class, epistemic_complete


def render_epistemic_strength(
    under_supported_list: List[int],
    under_train_per_class: int,
    regular_train_per_class: int
) -> None:
    """
    Render epistemic strength indicator with progress bar.
    
    Args:
        under_supported_list: List of under-supported class indices
        under_train_per_class: Samples per under-supported class
        regular_train_per_class: Samples per regular class
    """
    # This function is now deprecated - strength info shown in Dataset Configuration
    # Keeping function signature for backward compatibility but not rendering anything
    pass


def render_aleatoric_config(
    stats: Optional[Dict],
    noise_type: str,
    class_names: List[str],
    stats_fetcher: Callable[[str, str], Optional[Dict]],
    dataset_name: str
) -> Tuple[str, float]:
    """
    Render aleatoric uncertainty configuration section.
    
    Args:
        stats: Dataset statistics dictionary
        noise_type: Current noise type selection
        class_names: List of class names
        stats_fetcher: Function to fetch dataset statistics
        dataset_name: Name of the dataset
    
    Returns:
        Tuple of (noise_source, custom_noise_rate)
        - noise_source: Either "Use CIFAR-10N noise" or "Add random label flipping"
        - custom_noise_rate: Percentage (0-100) for custom noise, or 0 for CIFAR-10N
    """
    st.markdown("### 🎲 Aleatoric Uncertainty")
    st.info("💡 Data uncertainty from noisy or ambiguous labels. Inherent in the data.")
    
    noise_source = st.radio(
        "Noise Source",
        ["Use CIFAR-10N noise", "Add random label flipping"],
        help="Choose how to introduce label noise"
    )
    
    if noise_source == "Use CIFAR-10N noise":
        # Use noise_type from top section - no custom noise
        custom_noise_rate = 0.0
        
        # Fetch stats for the selected noise type
        with st.spinner("Loading noise statistics..."):
            stats = stats_fetcher(dataset_name, noise_type)
        
        # Show noise distribution table only for CIFAR-10N noise
        if stats:
            noise_per_class = stats.get('noise_per_class', {})
            if noise_per_class:
                with st.expander("📊 View Noise Distribution by Class"):
                    table_data = []
                    for class_id, data in noise_per_class.items():
                        class_idx = int(class_id)
                        class_name = class_names[class_idx] if class_idx < len(class_names) else f"Class {class_id}"
                        total = data.get('total', 0)
                        noisy = data.get('noisy', 0)
                        rate = data.get('rate', 0) * 100
                        
                        table_data.append({
                            "Class": class_name,
                            "Total": total,
                            "Noisy": noisy,
                            "Rate": f"{rate:.1f}%"
                        })
                    
                    df = pd.DataFrame(table_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Random label flipping
        noise_type = "random_flipping"  # Internal marker for random noise
        custom_noise_rate = st.slider(
            "Random label flip percentage",
            min_value=0, max_value=50, value=10,
            help="Percentage of labels to randomly flip"
        )
        st.caption(f"⚠️ Will randomly flip {custom_noise_rate}% of labels")
        stats = None  # No pre-computed stats for random flipping
    
    # Aleatoric Strength Indicator
    render_aleatoric_strength(noise_source, stats, noise_type, custom_noise_rate)
    
    return noise_source, custom_noise_rate


def render_aleatoric_strength(
    noise_source: str,
    stats: Optional[Dict],
    noise_type: str,
    custom_noise_rate: float
) -> None:
    """
    Render aleatoric strength indicator with progress bar.
    
    Args:
        noise_source: Source of noise (CIFAR-10N or custom)
        stats: Dataset statistics dictionary
        noise_type: Type of noise pattern
        custom_noise_rate: Custom noise rate if applicable
    """
    # This function is now deprecated - strength info shown in Dataset Configuration
    # Keeping function signature for backward compatibility but not rendering anything
    pass


def render_model_config() -> Tuple[str, int, float, bool]:
    """
    Render model architecture configuration.
    
    Returns:
        Tuple of (dinov2_model, hidden_dim, dropout, use_untrained_resnet)
    """
    # Feature extractor selection
    use_untrained_resnet = st.checkbox(
        "🔬 Use Untrained ResNet-50 (Experimental)",
        value=False,
        help="Use untrained ResNet-50 instead of pretrained DINOv2. Useful for baseline comparisons to understand if pretrained features help."
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if use_untrained_resnet:
            st.info("Using ResNet-50 (untrained)")
            dinov2_model = "resnet50_untrained"  # Placeholder, won't be used
        else:
            dinov2_model = st.selectbox("DINOv2 Backbone", ["small", "base", "large"], index=0)
    with col2:
        hidden_dim = st.number_input("Hidden Dimension", min_value=64, max_value=1024, value=256, step=64)
    with col3:
        dropout = st.number_input("Dropout Rate", min_value=0.0, max_value=0.9, value=0.2, step=0.1)
    
    if use_untrained_resnet:
        st.warning("⚠️ **Untrained ResNet-50**: Features will be random. Expect poor performance. This is useful for understanding the importance of pretrained features.")
    
    return dinov2_model, hidden_dim, dropout, use_untrained_resnet


def render_training_config() -> Tuple[int, float, float, int]:
    """
    Render training hyperparameters configuration.
    
    Returns:
        Tuple of (epochs, learning_rate, weight_decay, train_batch_size)
    """
    st.markdown("**Training Hyperparameters**")
    col1, col2, col3 = st.columns(3)
    with col1:
        epochs = st.number_input("Training Epochs", min_value=1, max_value=100, value=12)
    with col2:
        learning_rate = st.number_input("Learning Rate", min_value=0.0001, max_value=0.1, value=0.001, format="%.4f")
    with col3:
        weight_decay = st.number_input("Weight Decay", min_value=0.0, max_value=0.01, value=0.0001, format="%.5f")
    
    train_batch_size = st.number_input("Batch Size", min_value=16, max_value=512, value=256, step=16)
    
    return epochs, learning_rate, weight_decay, train_batch_size


def render_evaluation_config(
    under_supported_list: Optional[List[int]] = None,
    under_train_per_class: int = 50,
    regular_train_per_class: int = 300,
    noise_rate: float = 0.0,
    key_prefix: str = "default"
) -> Tuple[int, List[str], int]:
    """
    Render evaluation configuration section with dynamic sampling explanation.
    
    Args:
        under_supported_list: List of under-supported class indices (optional, for display)
        under_train_per_class: Samples per under-supported class
        regular_train_per_class: Samples per regular class
        noise_rate: Noise rate for aleatoric pool estimation
        key_prefix: Prefix for widget keys to avoid duplicates (e.g., "single", "batch")
    
    Returns:
        Tuple of (mc_passes, selected_signals, eval_per_group)
    """
    available_signals = {
        "Predictive Uncertainty (Baseline)": [
            "msp_uncertainty",
            "predictive_entropy",
            "mutual_info"
        ],
        "Attribution-Based (DualXDA)": [
            "inverse_coherence",
            "dominance"
        ],
        "Logit-Based (Representer Theorem)": [
            "inverse_mass",
            "inverse_logit_magnitude"
        ]
    }
    
    col1, col2 = st.columns(2)
    with col1:
        mc_passes = st.number_input(
            "MC Dropout Passes",
            min_value=5, max_value=100, value=20,
            help="Number of forward passes with dropout enabled to estimate epistemic uncertainty. Range: 5-100 (Quick: 10-20, Thorough: 50-100)",
            key=f"{key_prefix}_mc_passes"
        )
    with col2:
        st.markdown("**Attribution Signals**")
        st.caption("Select which uncertainty signals to compute")
        
        # Expandable sections for each signal category
        selected_signals = []
        for category, signals in available_signals.items():
            with st.expander(f"📊 {category}", expanded=True):  # Expand all by default
                for signal in signals:
                    # Select all signals by default
                    if st.checkbox(signal, value=True, key=f"{key_prefix}_signal_{signal}"):
                        selected_signals.append(signal)
        
        if not selected_signals:
            st.warning("⚠️ Please select at least one signal")
            # Default to all signals if none selected
            selected_signals = [s for signals in available_signals.values() for s in signals]
    
    eval_per_group = st.number_input(
        "Evaluation samples per group",
        min_value=100, max_value=2000, value=100, step=100,
        help="Number of samples for each evaluation group (clean, noisy, under-supported). Default: 100 for faster evaluation. Increase for more robust AUROC estimates.",
        key=f"{key_prefix}_eval_per_group"
    )
    
    st.info("""
    💡 **Why 100 samples per group?**
    - **3 evaluation groups**: 🟢 Clean, 🟡 Aleatoric (noisy), 🔴 Epistemic (under-supported)
    - **Fast evaluation**: 300 total samples (3 groups × 100) processes quickly
    - **Sufficient for AUROC**: 100 samples per group provides reliable uncertainty ranking
    - **Balanced trade-off**: Good statistical power without excessive computation
    - **Increase if needed**: Use 500-1000 for publication-quality results
    
    Note: The "3" is always 3 groups (Clean/Aleatoric/Epistemic), not the number of under-supported classes.
    """)
    
    # Add dynamic sampling explanation if configuration is provided
    if under_supported_list is not None:
        num_under = len(under_supported_list)
        num_regular = 10 - num_under
        
        # Calculate training samples
        under_train_total = num_under * under_train_per_class
        regular_train_total = num_regular * regular_train_per_class
        total_train = under_train_total + regular_train_total
        
        # Estimate evaluation pools (from remaining 50,000 - total_train samples)
        remaining_samples = 50000 - total_train
        
        # Estimate pool sizes (approximate)
        samples_per_class = 5000
        regular_remaining_per_class = samples_per_class - regular_train_per_class
        under_remaining_per_class = samples_per_class - under_train_per_class
        
        clean_pool_estimate = int(num_regular * regular_remaining_per_class * (1 - noise_rate))
        aleatoric_pool_estimate = int(num_regular * regular_remaining_per_class * noise_rate)
        epistemic_pool_estimate = int(num_under * under_remaining_per_class)
        
        with st.expander("📊 Evaluation Sampling Details (Based on Your Configuration)", expanded=False):
            st.markdown(f"""
            **Training Dataset:**
            - Under-supported: {num_under} classes × {under_train_per_class} samples = **{under_train_total:,}** training
            - Regular: {num_regular} classes × {regular_train_per_class} samples = **{regular_train_total:,}** training
            - **Total training: {total_train:,} samples**
            
            **Evaluation Pools** (from remaining {remaining_samples:,} samples):
            - 🟢 **Clean pool**: ~{clean_pool_estimate:,} clean samples from {num_regular} regular classes
            - 🟡 **Aleatoric pool**: ~{aleatoric_pool_estimate:,} noisy samples from {num_regular} regular classes
            - 🔴 **Epistemic pool**: ~{epistemic_pool_estimate:,} clean samples from {num_under} under-supported classes
            
            **Sampled for Evaluation:**
            - {eval_per_group} from clean pool → 🟢 Clean group
            - {eval_per_group} from aleatoric pool → 🟡 Aleatoric group
            - {eval_per_group} from epistemic pool → 🔴 Epistemic group
            - **Total: {3 * eval_per_group:,} evaluation samples**
            
            ⚠️ **Note**: All evaluation samples are held out from training. If requested samples exceed pool size, you'll get fewer samples.
            """)
    
    return mc_passes, selected_signals, eval_per_group


def render_evaluation_strategy(
    eval_per_group: int,
    under_supported: str,
    class_names: list[str]
) -> None:
    """
    Render evaluation dataset strategy explanation with crystal-clear group assignment logic.
    
    Args:
        eval_per_group: Number of samples per evaluation group
        under_supported: Under-supported classes configuration (e.g., "0,1" or "random:2")
        class_names: List of class names for display
    """
    # This function is now deprecated - evaluation strategy is shown in Dataset Configuration
    # Keeping function signature for backward compatibility but not rendering anything
    pass


def build_base_experiment_config(
    noise_type: str,
    under_supported: str,
    under_train_per_class: int,
    regular_train_per_class: int,
    dinov2_model: str,
    hidden_dim: int,
    dropout: float,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    train_batch_size: int,
    eval_per_group: int,
    mc_passes: int,
    use_untrained_resnet: bool = False,
    aleatoric_noise_percentage: float = 0.0,
) -> Dict[str, Any]:
    """
    Build the API-ready base config shared by single and batch experiments.
    
    Args:
        noise_type: Type of CIFAR-10N noise (e.g., "worse_label", "aggre_label")
        under_supported: Under-supported classes configuration
        under_train_per_class: Training samples per under-supported class
        regular_train_per_class: Training samples per regular class
        dinov2_model: DINOv2 model size
        hidden_dim: Hidden layer dimension
        dropout: Dropout rate
        epochs: Number of training epochs
        learning_rate: Learning rate
        weight_decay: Weight decay
        train_batch_size: Training batch size
        eval_per_group: Evaluation samples per group
        mc_passes: Monte Carlo dropout passes
        use_untrained_resnet: Whether to use untrained ResNet-50
        aleatoric_noise_percentage: Custom noise percentage (0-100). If > 0,
            overrides CIFAR-10N noise with uniform random label flipping.
    
    Returns:
        Configuration dictionary for experiment creation
    """
    return {
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
        "attribution_method": "dualxda",
        "use_untrained_resnet": use_untrained_resnet,
        "aleatoric_noise_percentage": aleatoric_noise_percentage,
    }

# Made with Bob
