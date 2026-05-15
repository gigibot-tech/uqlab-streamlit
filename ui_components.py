"""
UI Components for Streamlit Uncertainty Quantification App

This module contains reusable UI components for the experiment configuration interface.
Separates presentation logic from business logic for better maintainability.
"""

import streamlit as st
import pandas as pd
import requests
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable


def render_dataset_selection(
    dataset_name: str,
    noise_type: str,
    stats_fetcher: Callable[[str, str], Optional[Dict]]
) -> Tuple[str, str, Optional[Dict]]:
    """
    Render dataset selection section at the top of the page.
    
    Args:
        dataset_name: Default dataset name
        noise_type: Default noise type
        stats_fetcher: Function to fetch dataset statistics
    
    Returns:
        Tuple of (dataset_name, noise_type, stats_dict)
    """
    col_selector, col_description = st.columns([1, 2])
    
    with col_selector:
        dataset_name = st.selectbox(
            "Select Dataset",
            ["cifar10n"],
            help="Choose the base dataset for training"
        )
        
        noise_type = st.selectbox(
            "Noise Type",
            ["worse_label", "aggre_label", "random_label1", "random_label2", "random_label3"],
            help="Pre-defined noise patterns in CIFAR-10N"
        )
    
    with col_description:
        st.info(f"""
        **CIFAR-10N Dataset**
        - 📦 50,000 training images across 10 classes
        - 🎲 Synthetic label noise for uncertainty research
        - ✨ Ground truth: Original CIFAR-10 clean labels
        - 🏷️ Classes: airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck
        """)
        
        # Fetch stats
        stats = stats_fetcher(dataset_name, noise_type)
        if stats:
            noise_rate = stats.get('noise_rate', 0) * 100
            st.metric("Average Noise Rate", f"{noise_rate:.1f}%")
    
    st.markdown("---")
    
    return dataset_name, noise_type, stats


def render_configuration_progress(
    config_progress: Dict[str, bool],
    api_base_url: str
) -> None:
    """
    Render configuration progress sidebar with checkmarks and progress bar.
    
    Args:
        config_progress: Dictionary with completion status for each section
        api_base_url: API endpoint URL to display
    """
    dataset_icon = "✅" if config_progress['dataset'] else "⭕"
    epistemic_icon = "✅" if config_progress['epistemic'] else "⭕"
    aleatoric_icon = "✅" if config_progress['aleatoric'] else "⭕"
    model_icon = "✅" if config_progress['model'] else "⭕"
    evaluation_icon = "✅" if config_progress['evaluation'] else "⭕"
    
    st.markdown(f"{dataset_icon} Dataset")
    st.markdown(f"{epistemic_icon} Epistemic")
    st.markdown(f"{aleatoric_icon} Aleatoric")
    st.markdown(f"{model_icon} Model")
    st.markdown(f"{evaluation_icon} Evaluation")
    
    # Calculate overall completion
    completed = sum(config_progress.values())
    total = len(config_progress)
    progress_pct = completed / total
    
    st.progress(progress_pct)
    st.caption(f"{int(progress_pct * 100)}% Complete")
    
    st.markdown("---")
    st.markdown(f"**API Endpoint:** `{api_base_url}`")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()


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
        st.caption("💡 Selection updates when you submit the form")
        if under_supported_list:
            # Display selected classes with consistent formatting (space after colon)
            st.success(f"✅ Selected: {', '.join([f'{i}: {class_names[i]}' for i in under_supported_list])}")
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
    """
    st.markdown("### 🎲 Aleatoric Uncertainty")
    st.info("💡 Data uncertainty from noisy or ambiguous labels. Inherent in the data.")
    
    noise_source = st.radio(
        "Noise Source",
        ["Use CIFAR-10N noise", "Add random label flipping"],
        help="Choose how to introduce label noise"
    )
    
    if noise_source == "Use CIFAR-10N noise":
        # Use noise_type from top section
        st.success(f"✅ Using pre-defined noise: **{noise_type}**")
        st.caption("(Selected in Dataset Overview above)")
        custom_noise_rate = 0
        
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


def render_dataset_comparison(
    under_supported: str,
    under_train_per_class: int,
    regular_train_per_class: int,
    noise_source: str,
    stats: Optional[Dict],
    noise_type: str,
    custom_noise_rate: float,
    class_names: List[str],
    eval_per_group: int
) -> None:
    """
    Render dynamic dataset calculations based on user configuration.
    All values are computed from actual configuration parameters - no hardcoded examples.
    
    Args:
        under_supported: Under-supported classes specification
        under_train_per_class: Samples per under-supported class
        regular_train_per_class: Samples per regular class
        noise_source: Source of noise
        stats: Dataset statistics (only for total dataset info)
        noise_type: Type of noise pattern
        custom_noise_rate: Custom noise rate
        class_names: List of class names
        eval_per_group: Samples per evaluation group
    """
    st.markdown("---")
    st.markdown("### 📊 Dataset Configuration (Fully Dynamic)")
    
    # Parse under-supported classes and get actual indices
    if under_supported.startswith("random:"):
        num_under = int(under_supported.split(":")[1])
        under_supported_list = []  # Random selection, indices not yet determined
        under_classes_display = f"{num_under} randomly selected classes"
    else:
        under_supported_list = [int(x.strip()) for x in under_supported.split(",") if x.strip()]
        num_under = len(under_supported_list)
        # Show actual class names
        if under_supported_list:
            class_display = ", ".join([f"{i} ({class_names[i]})" for i in under_supported_list])
            under_classes_display = class_display
        else:
            under_classes_display = "None selected"
    
    num_regular = 10 - num_under
    
    # Get actual noise rate from configuration
    if noise_source == "Use CIFAR-10N noise" and stats:
        noise_rate = stats.get('noise_rate', 0)
        noise_source_display = f"CIFAR-10N {noise_type}"
    else:
        noise_rate = custom_noise_rate / 100.0
        noise_source_display = f"Random label flipping at {custom_noise_rate}%"
    
    # Calculate training dataset sizes dynamically
    under_samples = num_under * under_train_per_class
    regular_clean_samples = int(num_regular * regular_train_per_class * (1 - noise_rate))
    regular_noisy_samples = int(num_regular * regular_train_per_class * noise_rate)
    total_regular_samples = num_regular * regular_train_per_class
    total_train = under_samples + total_regular_samples
    
    # Calculate evaluation dataset sizes dynamically
    total_eval = 3 * eval_per_group
    
    st.info("""
    **CIFAR-10 Base Dataset:**
    - Training: 50,000 samples (5,000 per class)
    - Test: 10,000 samples (1,000 per class)
    
    Your configuration creates custom training and evaluation splits from this base.
    """)
    
    # Show selected classes
    st.markdown("#### 🎯 Class Distribution")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        **Under-supported Classes ({num_under}):**
        {under_classes_display}
        """)
    with col_b:
        st.markdown(f"""
        **Regular Classes ({num_regular}):**
        All remaining classes
        """)
    
    # Training Dataset Section
    st.markdown("#### 🎯 Training Dataset (Based on Your Configuration)")
    st.markdown(f"""
    **Formula:** `Total = (Under-supported samples) + (Regular samples)`
    
    **Calculation:**
    ```
    Under-supported: {num_under} classes × {under_train_per_class} samples = {under_samples:,} samples
    Regular classes: {num_regular} classes × {regular_train_per_class} samples = {total_regular_samples:,} samples
      ├─ Clean: {total_regular_samples:,} × {(1-noise_rate):.1%} = {regular_clean_samples:,} samples
      └─ Noisy: {total_regular_samples:,} × {noise_rate:.1%} = {regular_noisy_samples:,} samples
    
    Total Training = {under_samples:,} + {total_regular_samples:,} = {total_train:,} samples
    ```
    
    **Noise Source:** {noise_source_display}
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Training", f"{total_train:,}")
    with col2:
        st.metric("Under-supported", f"{under_samples:,}",
                  delta=f"{num_under} classes")
    with col3:
        st.metric("Regular (Clean+Noisy)", f"{total_regular_samples:,}",
                  delta=f"{num_regular} classes")
    
    # Evaluation Dataset Section
    st.markdown("#### 📊 Evaluation Dataset (3 Groups)")
    st.markdown(f"""
    **Formula:** `Total = 3 × {eval_per_group:,} samples per group`
    
    **Group Assignment:**
    ```
    🟢 Clean Group:      {eval_per_group:,} samples from regular classes (clean labels)
    🟡 Aleatoric Group:  {eval_per_group:,} samples from regular classes (noisy labels)
    🔴 Epistemic Group:  {eval_per_group:,} samples from under-supported classes (clean labels)
    
    Total Evaluation = 3 × {eval_per_group:,} = {total_eval:,} samples
    ```
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Evaluation", f"{total_eval:,}")
    with col2:
        st.metric("🟢 Clean", f"{eval_per_group:,}")
    with col3:
        st.metric("🟡 Aleatoric", f"{eval_per_group:,}")
    with col4:
        st.metric("🔴 Epistemic", f"{eval_per_group:,}")
    
    st.warning("""
    ⚠️ **Important**: Evaluation samples are **separate from training** and never overlap.
    This ensures unbiased measurement of uncertainty detection capabilities.
    """)


def render_model_config() -> Tuple[str, int, float]:
    """
    Render model architecture configuration.
    
    Returns:
        Tuple of (dinov2_model, hidden_dim, dropout)
    """
    col1, col2, col3 = st.columns(3)
    with col1:
        dinov2_model = st.selectbox("DINOv2 Backbone", ["small", "base", "large"], index=0)
    with col2:
        hidden_dim = st.number_input("Hidden Dimension", min_value=64, max_value=1024, value=256, step=64)
    with col3:
        dropout = st.number_input("Dropout Rate", min_value=0.0, max_value=0.9, value=0.2, step=0.1)
    
    return dinov2_model, hidden_dim, dropout


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


def render_evaluation_config() -> Tuple[int, List[str], int]:
    """
    Render evaluation configuration section.
    
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
            help="Number of forward passes with dropout enabled to estimate epistemic uncertainty. Range: 5-100 (Quick: 10-20, Thorough: 50-100)"
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
                    if st.checkbox(signal, value=True, key=f"signal_{signal}"):
                        selected_signals.append(signal)
        
        if not selected_signals:
            st.warning("⚠️ Please select at least one signal")
            # Default to all signals if none selected
            selected_signals = [s for signals in available_signals.values() for s in signals]
        
        st.caption(f"✅ Selected {len(selected_signals)} signal(s)")
    
    eval_per_group = st.number_input(
        "Evaluation samples per group",
        min_value=100, max_value=2000, value=100, step=100,
        help="Number of samples for each evaluation group (clean, noisy, under-supported). Default: 100 for faster evaluation. Increase for more robust AUROC estimates."
    )
    
    st.info("""
    💡 **Why 100 samples per group?**
    - **Fast evaluation**: 300 total samples (3 groups × 100) processes quickly
    - **Sufficient for AUROC**: 100 samples per group provides reliable uncertainty ranking
    - **Balanced trade-off**: Good statistical power without excessive computation
    - **Increase if needed**: Use 500-1000 for publication-quality results
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


def render_roc_explanation(
    under_supported: str,
    class_names: list[str],
    noise_source: str,
    custom_noise_rate: float
) -> None:
    """
    Render ROC calculation walkthrough with crystal-clear configuration-based explanation.
    
    Args:
        under_supported: Under-supported classes configuration
        class_names: List of class names for display
        noise_source: Noise source selection ("Use CIFAR-10N noise" or "Random noise")
        custom_noise_rate: Custom noise rate if random noise is used
    """
    with st.expander("📐 Understanding AUROC Calculation (Click to Expand)"):
        st.markdown("### How AUROC Measures Uncertainty Detection")
        
        # Parse under-supported classes for display
        if under_supported.startswith("random:"):
            num_under = int(under_supported.split(":")[1])
            under_classes_display = f"random {num_under} classes"
            under_indices = []
        else:
            under_indices = [int(idx.strip()) for idx in under_supported.split(",") if idx.strip()]
            num_under = len(under_indices)
            under_classes_display = ", ".join([f"{class_names[idx]}" for idx in under_indices])
        
        num_regular = 10 - num_under
        
        # Configuration context
        st.info("""
        **AUROC (Area Under ROC Curve)** measures how well uncertainty signals can
        **rank samples by their uncertainty** based on your specific configuration.
        """)
        
        # Display configuration context
        st.markdown("#### 🎯 AUROC Calculation Based on Your Configuration")
        
        noise_desc = "CIFAR-10N synthetic noise" if noise_source == "Use CIFAR-10N noise" else f"{custom_noise_rate}% random label flipping"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **🟡 Aleatoric AUROC** (Detecting Noisy Labels)
            
            **Positive Class (should have HIGH uncertainty):**
            - 🟡 Aleatoric group
            - Regular classes + noisy labels
            - {num_regular} well-supported classes with {noise_desc}
            
            **Negative Class (should have LOW uncertainty):**
            - 🟢 Clean group (regular classes, clean labels)
            - 🔴 Epistemic group (under-supported classes, clean labels)
            
            **Question:** Can we detect mislabeled data in well-supported classes?
            """)
        
        with col2:
            st.markdown(f"""
            **🔴 Epistemic AUROC** (Detecting Unfamiliar Classes)
            
            **Positive Class (should have HIGH uncertainty):**
            - 🔴 Epistemic group
            - Under-supported classes: {under_classes_display}
            - Clean labels but model undertrained
            
            **Negative Class (should have LOW uncertainty):**
            - 🟢 Clean group (regular classes, clean labels)
            - 🟡 Aleatoric group (regular classes, noisy labels)
            
            **Question:** Can we detect samples from undertrained classes?
            """)
        
        st.warning("""
        ⚠️ **Key Point**: AUROC scores depend entirely on your configuration.
        Different under-supported classes or noise rates will produce different results.
        """)
        
        st.markdown("---")
        
        # Step-by-step explanation
        st.markdown("#### 📊 How AUROC is Calculated")
        
        st.markdown("**Step 1: Compute Uncertainty Scores**")
        st.code("""
# For each evaluation sample, compute uncertainty signal
for sample in evaluation_dataset:
    uncertainty_score = model.compute_uncertainty(sample)
    
# Higher score = more uncertain
# Example:
#   Clean sample (regular class):     0.15 (low uncertainty)
#   Aleatoric sample (noisy label):   0.82 (high uncertainty)
#   Epistemic sample (under-trained): 0.91 (high uncertainty)
        """, language="python")
        
        st.markdown("**Step 2: Rank Samples by Uncertainty**")
        
        # Sample data preview
        sample_data = pd.DataFrame({
            'Sample': ['img_001', 'img_002', 'img_003', 'img_004', 'img_005', 'img_006'],
            'True Group': ['🟢 Clean', '🟡 Aleatoric', '🔴 Epistemic', '🟢 Clean', '🟡 Aleatoric', '🔴 Epistemic'],
            'Uncertainty': [0.15, 0.82, 0.91, 0.19, 0.78, 0.88],
            'Rank': [1, 4, 6, 2, 3, 5]
        })
        
        st.dataframe(sample_data, use_container_width=True)
        
        st.markdown("**Step 3: Calculate AUROC**")
        
        st.markdown("""
        AUROC measures: **"What fraction of positive samples are ranked higher than negative samples?"**
        
        For **Aleatoric AUROC**:
        - Positive = 🟡 Aleatoric (should rank high)
        - Negative = 🟢 Clean + 🔴 Epistemic (should rank low)
        - Perfect score: All aleatoric samples ranked above all clean/epistemic
        
        For **Epistemic AUROC**:
        - Positive = 🔴 Epistemic (should rank high)
        - Negative = 🟢 Clean + 🟡 Aleatoric (should rank low)
        - Perfect score: All epistemic samples ranked above all clean/aleatoric
        """)
        
        st.markdown("#### 📈 Interpretation")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.success("""
            **AUROC Scores:**
            - **1.0**: Perfect detection
            - **0.9**: Excellent (90% correct ranking)
            - **0.7**: Good (70% correct ranking)
            - **0.5**: Random guessing (no signal)
            """)
        with col_b:
            st.info("""
            **What This Means:**
            - High Aleatoric AUROC → Can detect bad labels
            - High Epistemic AUROC → Can detect knowledge gaps
            - Compare signals to find best uncertainty measure
            """)
        
        st.markdown("---")
        st.markdown("#### 💡 Practical Example")
        st.code("""
# Your configuration creates these groups:
Clean:      600 samples from regular classes (clean)
Aleatoric:  600 samples from regular classes (noisy)
Epistemic:  600 samples from under-supported classes (clean)

# Model computes uncertainty for all 1800 samples
# AUROC tells us: "Can uncertainty scores separate the groups?"

# Good Aleatoric AUROC (0.85):
#   → 85% of noisy samples ranked higher than clean samples
#   → Uncertainty signal detects mislabeled data well

# Good Epistemic AUROC (0.92):
#   → 92% of under-supported samples ranked higher
#   → Uncertainty signal detects unfamiliar classes well
        """, language="python")


def render_experiment_results(
    api_base_url: str,
    get_headers_func: Callable[[], Dict],
    auto_refresh: bool
) -> bool:
    """
    Render experiment results section with auto-refresh.
    
    Args:
        api_base_url: Base URL for API requests
        get_headers_func: Function to get request headers
        auto_refresh: Current auto-refresh state
    
    Returns:
        Updated auto_refresh state
    """
    col1, col2, col3 = st.columns(3)
    with col1:
        auto_refresh = st.checkbox(
            "🔄 Enable Auto-Refresh (5s)",
            value=auto_refresh,
            key="auto_refresh_checkbox",
            help="Automatically refresh experiment status every 5 seconds"
        )
    with col2:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
    with col3:
        if st.button("🛑 Stop Refresh", use_container_width=True):
            auto_refresh = False
            st.rerun()
    
    try:
        # Fetch experiments using no-auth endpoint
        response = requests.get(
            f"{api_base_url}/api/v1/experiments/no-auth",
            headers=get_headers_func(),
            timeout=10
        )
        response.raise_for_status()
        experiments = response.json()
        
        if not experiments:
            st.info("No experiments found. Create one using the form above!")
        else:
            # Display experiments table with start button
            exp_data = []
            for exp in experiments:
                exp_data.append({
                    "ID": exp["id"],
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
            
            # Expandable details for each experiment
            st.markdown("### 📋 Experiment Details")
            for exp in experiments:
                _render_experiment_detail(exp, api_base_url, get_headers_func)
            
            # Start training button for queued experiments
            _render_start_training_buttons(experiments, api_base_url, get_headers_func)
            
            # Enterprise-grade auto-refresh using st.empty() placeholder
            if auto_refresh:
                # Use a placeholder for countdown
                refresh_placeholder = st.empty()
                import time
                for remaining in range(5, 0, -1):
                    refresh_placeholder.info(f"🔄 Auto-refreshing in {remaining} seconds...")
                    time.sleep(1)
                refresh_placeholder.empty()
                st.rerun()
        
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch experiments: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Response: {e.response.text}")
    
    return auto_refresh


def _render_experiment_detail(
    exp: Dict,
    api_base_url: str,
    get_headers_func: Callable[[], Dict]
) -> None:
    """
    Render detailed view for a single experiment.
    
    Args:
        exp: Experiment data dictionary
        api_base_url: Base URL for API requests
        get_headers_func: Function to get request headers
    """
    # Try to load results from files
    results_data = None
    results_path = f"/tmp/walaris_experiments/{exp['id']}/results"
    summary_file = f"{results_path}/summary.json"
    
    try:
        if Path(summary_file).exists():
            with open(summary_file) as f:
                results_data = json.load(f)
    except Exception:
        pass  # Results not available yet
    
    status_emoji = {
        "queued": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌"
    }.get(exp['status'], "❓")
    
    with st.expander(f"{status_emoji} {exp['name']} ({exp['status'].upper()})"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Info**")
            st.json({
                "ID": exp["id"],
                "Name": exp["name"],
                "Status": exp["status"],
                "Progress": f"{exp.get('progress', 0):.1%}",
                "Message": exp.get("progress_message", "N/A"),
                "Created": exp["created_at"],
                "Started": exp.get("started_at", "N/A"),
                "Completed": exp.get("completed_at", "N/A"),
            })
        
        with col2:
            st.markdown("**Configuration**")
            config = exp.get("config_yaml", {})
            st.json({
                "Noise Type": config.get("noise_type", "N/A"),
                "Epochs": config.get("epochs", "N/A"),
                "Model": config.get("dinov2_model", "N/A"),
                "Hidden Dim": config.get("hidden_dim", "N/A"),
                "Dropout": config.get("dropout", "N/A"),
            })
        
        # Show results from files if available
        if results_data:
            _render_experiment_results_data(results_data)
        elif exp['status'] == 'completed':
            st.warning("⚠️ Results files not found. Check results_path.")
            st.code(f"Expected: {summary_file}")
        
        # Delete button
        st.markdown("---")
        if st.button(f"🗑️ Delete Experiment", key=f"delete_{exp['id']}", type="secondary"):
            try:
                delete_response = requests.delete(
                    f"{api_base_url}/api/v1/experiments/no-auth/{exp['id']}",
                    headers=get_headers_func(),
                    timeout=10
                )
                delete_response.raise_for_status()
                st.success(f"✅ Experiment '{exp['name']}' deleted successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete experiment: {str(e)}")


def _render_experiment_results_data(results_data: Dict) -> None:
    """
    Render experiment results data from summary file.
    
    Args:
        results_data: Results dictionary from summary.json
    """
    st.markdown("---")
    st.markdown("### 📊 Results (from files)")
    
    # Best signals
    aurocs = results_data.get("one_vs_rest_auroc", [])
    if aurocs:
        st.markdown("**🎯 Best Uncertainty Signals:**")
        
        # Find best aleatoric and epistemic signals
        best_aleatoric = max(aurocs, key=lambda x: x.get("aleatoric_like_auroc", 0))
        best_epistemic = max(aurocs, key=lambda x: x.get("epistemic_like_auroc", 0))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Best Aleatoric Signal",
                f"{best_aleatoric['aleatoric_like_auroc']:.4f}",
                delta=best_aleatoric['signal']
            )
        with col2:
            st.metric(
                "Best Epistemic Signal",
                f"{best_epistemic['epistemic_like_auroc']:.4f}",
                delta=best_epistemic['signal']
            )
        
        # All signals table
        st.markdown("**All Signals:**")
        signals_df = pd.DataFrame(aurocs)
        signals_df = signals_df.rename(columns={
            "signal": "Signal",
            "aleatoric_like_auroc": "Aleatoric AUROC",
            "epistemic_like_auroc": "Epistemic AUROC"
        })
        st.dataframe(signals_df, use_container_width=True, hide_index=True)
    
    # Macro F1 scores
    macro_f1 = results_data.get("macro_f1", [])
    if macro_f1:
        st.markdown("**🎯 3-Way Classification F1 Scores:**")
        f1_df = pd.DataFrame(macro_f1)
        f1_df = f1_df.rename(columns={
            "signal_set": "Signal Set",
            "macro_f1": "Macro F1"
        })
        st.dataframe(f1_df, use_container_width=True, hide_index=True)
    
    # Dataset info
    st.markdown("**📦 Dataset Info:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Train Size", results_data.get("train_size", "N/A"))
    with col2:
        eval_sizes = results_data.get("eval_sizes", {})
        st.metric("Clean Eval", eval_sizes.get("clean", "N/A"))
    with col3:
        st.metric("Noisy Eval", eval_sizes.get("aleatoric_like", "N/A"))


def _render_start_training_buttons(
    experiments: List[Dict],
    api_base_url: str,
    get_headers_func: Callable[[], Dict]
) -> None:
    """
    Render start training buttons for queued experiments.
    
    Args:
        experiments: List of experiment dictionaries
        api_base_url: Base URL for API requests
        get_headers_func: Function to get request headers
    """
    queued_exps = [e for e in experiments if e["status"] == "queued"]
    if queued_exps:
        st.markdown("### 🚀 Start Training")
        for exp in queued_exps:
            if st.button(f"Start: {exp['name']}", key=f"start_{exp['id']}"):
                try:
                    start_response = requests.post(
                        f"{api_base_url}/api/v1/experiments/no-auth/{exp['id']}/start",
                        headers=get_headers_func(),
                        timeout=30
                    )
                    start_response.raise_for_status()
                    st.success(f"✅ Training started for {exp['name']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start training: {str(e)}")

# Made with Bob
