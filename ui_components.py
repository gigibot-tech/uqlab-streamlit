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
            help="These classes will have limited training samples, creating epistemic uncertainty"
        )
        if under_supported_list:
            st.success(f"✅ Selected: {', '.join([f'{i}:{class_names[i]}' for i in under_supported_list])}")
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
    st.markdown("**📊 Epistemic Strength Analysis**")
    
    num_under = len(under_supported_list)
    baseline_samples = regular_train_per_class
    under_samples = under_train_per_class
    
    # Calculate strength (scarcity ratio)
    scarcity_ratio = 1 - (under_samples / baseline_samples)
    strength_pct = scarcity_ratio * 100
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Strength: {strength_pct:.0f}%**")
        st.progress(strength_pct / 100)
        
        strength_label = (
            "Very High" if strength_pct > 80 else
            "High" if strength_pct > 60 else
            "Moderate" if strength_pct > 40 else
            "Low"
        )
        st.caption(
            f"🎯 {strength_label} epistemic uncertainty "
            f"({under_samples} vs {baseline_samples} samples)"
        )
    
    with col2:
        st.metric(
            "Selected Classes",
            f"{num_under}/10",
            delta=f"{num_under} under-supported"
        )


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
    st.markdown("**📊 Aleatoric Strength Analysis**")
    
    if noise_source == "Use CIFAR-10N noise" and stats:
        noise_rate = stats.get('noise_rate', 0) * 100
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Average Noise Rate: {noise_rate:.1f}%**")
            st.progress(noise_rate / 100)
            
            pattern_type = "2-label confusion" if "worse" in noise_type or "aggre" in noise_type else "all-label random"
            st.caption(
                f"📊 Pattern: {pattern_type}\n"
                f"Source: CIFAR-10N {noise_type}"
            )
        
        with col2:
            st.metric(
                "Noise Strength",
                f"{noise_rate:.1f}%",
                delta="Fixed (dataset)"
            )
        
        # Noise pattern explanation
        with st.expander("ℹ️ Understanding Noise Patterns"):
            st.markdown("""
            **2-Label Confusion** (worse_label, aggre_label):
            - Labels confused between similar classes
            - Example: cat ↔ dog, truck ↔ automobile
            - More realistic, harder to detect
            
            **All-Label Random** (random_label1/2/3):
            - Labels randomly flipped to any class
            - Less realistic, easier to detect
            - Useful for baseline comparisons
            """)
    
    else:  # Custom noise
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Custom Noise Rate: {custom_noise_rate}%**")
            st.progress(custom_noise_rate / 100)
            st.caption("⚠️ Random label flipping (all-label pattern)")
        
        with col2:
            st.metric(
                "Noise Strength",
                f"{custom_noise_rate}%",
                delta="Custom"
            )


def render_dataset_comparison(
    under_supported: str,
    under_train_per_class: int,
    regular_train_per_class: int,
    noise_source: str,
    stats: Optional[Dict],
    noise_type: str,
    custom_noise_rate: float,
    class_names: List[str]
) -> None:
    """
    Render side-by-side training vs ground truth dataset comparison.
    
    Args:
        under_supported: Under-supported classes specification
        under_train_per_class: Samples per under-supported class
        regular_train_per_class: Samples per regular class
        noise_source: Source of noise
        stats: Dataset statistics
        noise_type: Type of noise pattern
        custom_noise_rate: Custom noise rate
        class_names: List of class names
    """
    st.markdown("---")
    st.markdown("### 📈 Dataset Comparison: Training vs Ground Truth")
    
    # Calculate stats
    if under_supported.startswith("random:"):
        num_under = int(under_supported.split(":")[1])
    else:
        num_under = len(under_supported.split(",")) if under_supported else 2
    
    expected_under_samples = num_under * under_train_per_class
    expected_regular_samples = (10 - num_under) * regular_train_per_class
    expected_total_train = expected_under_samples + expected_regular_samples
    
    col_training, col_ground_truth = st.columns(2)
    
    # Training Dataset (Configured)
    with col_training:
        st.markdown("#### 🎯 Training Dataset (Configured)")
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(255,152,0,0.1), rgba(255,152,0,0.05));
                    padding: 20px; border-radius: 8px; border-left: 4px solid #FF9800;'>
        """, unsafe_allow_html=True)
        
        st.metric("Total Samples", f"{expected_total_train:,}")
        st.metric("Under-supported", f"{expected_under_samples:,}",
                  delta=f"{num_under} classes")
        st.metric("Regular Samples", f"{expected_regular_samples:,}",
                  delta=f"{10-num_under} classes")
        
        if noise_source == "Use CIFAR-10N noise" and stats:
            noise_rate = stats.get('noise_rate', 0) * 100
            st.metric("Noise Rate", f"{noise_rate:.1f}%",
                     delta="From CIFAR-10N")
        else:
            st.metric("Noise Rate", f"{custom_noise_rate}%",
                     delta="Custom flipping")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Ground Truth Dataset (Clean)
    with col_ground_truth:
        st.markdown("#### ✨ Ground Truth (Clean CIFAR-10)")
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(76,175,80,0.1), rgba(76,175,80,0.05));
                    padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
        """, unsafe_allow_html=True)
        
        st.metric("Total Samples", "50,000")
        st.metric("Per Class", "5,000", delta="Uniform")
        st.metric("Distribution", "Balanced", delta="All classes")
        st.metric("Noise Rate", "0%", delta="Clean labels")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Differences Summary
    st.markdown("#### 🔍 Key Differences")
    reduction_pct = (1 - expected_total_train / 50000) * 100
    
    # Get noise rate for differences
    if noise_source == "Use CIFAR-10N noise" and stats:
        diff_noise_rate = stats.get('noise_rate', 0) * 100
    else:
        diff_noise_rate = custom_noise_rate
    
    differences = [
        f"📉 **{reduction_pct:.1f}% reduction** in dataset size ({expected_total_train:,} vs 50,000)",
        f"⚖️ **{num_under} classes under-represented** (epistemic uncertainty)",
        f"🎲 **{diff_noise_rate:.1f}% label noise** added (aleatoric uncertainty)",
        f"🎯 **Training uses configured data**, evaluation uses separate clean samples"
    ]
    
    for diff in differences:
        st.markdown(f"- {diff}")


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
            with st.expander(f"📊 {category}", expanded=(category == "Attribution-Based (DualXDA)")):
                for signal in signals:
                    if st.checkbox(signal, value=(signal in ["inverse_coherence", "inverse_mass"]), key=f"signal_{signal}"):
                        selected_signals.append(signal)
        
        if not selected_signals:
            st.warning("⚠️ Please select at least one signal")
            selected_signals = ["inverse_coherence", "inverse_mass"]  # Defaults
        
        st.caption(f"✅ Selected {len(selected_signals)} signal(s)")
    
    eval_per_group = st.number_input(
        "Evaluation samples per group",
        min_value=100, max_value=2000, value=600,
        help="Number of samples for each evaluation group (clean, noisy, under-supported)"
    )
    
    return mc_passes, selected_signals, eval_per_group


def render_evaluation_strategy(eval_per_group: int) -> None:
    """
    Render evaluation dataset strategy explanation.
    
    Args:
        eval_per_group: Number of samples per evaluation group
    """
    st.markdown("### 🎯 Evaluation Dataset Strategy")
    
    st.info("""
    **How Evaluation Works:**
    
    The evaluation dataset is **separate from training** and consists of three balanced groups:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🟢 Clean Group")
        st.markdown(f"""
        - **{eval_per_group}** samples
        - From **well-supported** classes
        - **Clean labels** (no noise)
        - Purpose: Baseline performance
        """)
    
    with col2:
        st.markdown("#### 🟡 Aleatoric Group")
        st.markdown(f"""
        - **{eval_per_group}** samples
        - From **well-supported** classes
        - **Noisy labels** (data uncertainty)
        - Purpose: Test noise detection
        """)
    
    with col3:
        st.markdown("#### 🔴 Epistemic Group")
        st.markdown(f"""
        - **{eval_per_group}** samples
        - From **under-supported** classes
        - **Clean labels** (model uncertainty)
        - Purpose: Test OOD detection
        """)
    
    st.warning("""
    ⚠️ **Important**: Evaluation samples are **never used in training**. This ensures unbiased measurement of the model's uncertainty detection capabilities.
    """)


def render_roc_explanation() -> None:
    """
    Render ROC calculation walkthrough in collapsible expander.
    """
    with st.expander("📐 Understanding ROC Calculation (Click to Expand)"):
        st.markdown("### How We Calculate AUROC Scores")
        
        st.markdown("""
        **ROC (Receiver Operating Characteristic)** measures how well uncertainty signals
        distinguish between different sample groups.
        """)
        
        # Step-by-step explanation
        st.markdown("#### Step 1: Collect Uncertainty Scores")
        st.code("""
# For each evaluation sample, compute uncertainty signal
uncertainty_scores = model.predict_uncertainty(eval_samples)

# Example scores (higher = more uncertain):
sample_1: 0.85  # High uncertainty (likely noisy or OOD)
sample_2: 0.23  # Low uncertainty (likely clean)
sample_3: 0.67  # Medium uncertainty
        """, language="python")
        
        st.markdown("#### Step 2: Compare to Ground Truth Groups")
        
        # Sample data preview
        sample_data = pd.DataFrame({
            'Sample': ['img_001', 'img_002', 'img_003', 'img_004', 'img_005'],
            'True Group': ['Clean', 'Aleatoric', 'Epistemic', 'Clean', 'Aleatoric'],
            'Uncertainty Score': [0.23, 0.85, 0.67, 0.19, 0.91],
            'Predicted Label': ['cat', 'dog', 'bird', 'cat', 'dog'],
            'Ground Truth': ['cat', 'cat', 'bird', 'cat', 'dog']
        })
        
        st.dataframe(sample_data, use_container_width=True)
        
        st.markdown("#### Step 3: Calculate AUROC")
        st.markdown("""
        **Aleatoric AUROC** (Detecting Noisy Labels):
        - Positive class: Aleatoric group (noisy samples)
        - Negative class: Clean + Epistemic groups
        - Question: Can we detect mislabeled data?
        
        **Epistemic AUROC** (Detecting OOD Samples):
        - Positive class: Epistemic group (under-supported)
        - Negative class: Clean + Aleatoric groups
        - Question: Can we detect unfamiliar classes?
        """)
        
        st.markdown("#### Interpretation")
        st.success("""
        **AUROC = 1.0**: Perfect separation (all uncertain samples detected)
        **AUROC = 0.9**: Excellent (90% of uncertain samples ranked higher)
        **AUROC = 0.7**: Good (70% correct ranking)
        **AUROC = 0.5**: Random guessing (no discrimination)
        """)
        
        st.info("""
        💡 **In Practice**: We compute AUROC for each uncertainty signal
        (e.g., predictive entropy, inverse coherence) to find which signals
        best detect aleatoric vs epistemic uncertainty.
        """)


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
