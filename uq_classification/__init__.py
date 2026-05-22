"""
Uncertainty Quantification Classification Package

Professional ML Research Pipeline with 3-layer architecture and graceful degradation:
- Layer 0: Data Management (slingpy - optional)
- Layer 1: Experiment Management (py-experimenter - optional)
- Layer 2: Model Training (PyTorch Lightning - required but has fallback)
- Layer 3: Tracking (MLflow - optional)

This package provides modular components for uncertainty classification experiments
using CIFAR-10/CIFAR-10N datasets with DINOv2 features and DualXDA attribution analysis.

Modules:
    - config_schema: Type-safe configuration with validation (NEW - optional)
    - lightning_module: PyTorch Lightning training (Layer 2)
    - data_module: PyTorch Lightning data loading (Layer 2)
    - tracking: MLflow/TensorBoard/CSV logging (Layer 3)
    - experiment_manager: py-experimenter wrapper (Layer 1)
    - models: Neural network architectures (FeatureDropoutMLP, FeatureDataset)
    - data_loader: Data loading, feature extraction, and split sampling
    - attribution_signals: Attribution-based uncertainty signal computation
    - evaluation: Model evaluation metrics (AUROC, F1, confusion matrix)
    - utils: Helper functions (seed setting, device management, transforms)
    - unified_tracker: Unified experiment tracking (MLflow/JSON)
    - decision_boundary_viz: Decision boundary visualization tools
    - streamlit_viz_app: Interactive Streamlit dashboard for visualizations

Reused from src/:
    - src.metrics.mc_dropout_uq: Predictive uncertainty metrics
    - src.models.dinov2_backbone: DINOv2 feature extraction
    - src.triage.dualxda_axioms: DualXDA attribution tracing
    - src.data.cifar10n_loader: CIFAR-10N dataset loading

New Features (Optional):
    - Configuration validation with dataclasses (see config_schema.py)
    - Unit tests with pytest (see tests/)
    - Type checking with mypy (see mypy.ini)
    - See IMPROVEMENTS_GUIDE.md for details
"""

__version__ = "2.2.0"  # Bumped for new optional features

# Group constants used throughout the package
GROUP_CLEAN = 0
GROUP_ALEATORIC = 1
GROUP_EPISTEMIC = 2
GROUP_NAMES = {
    GROUP_CLEAN: "clean",
    GROUP_ALEATORIC: "aleatoric_like",
    GROUP_EPISTEMIC: "epistemic_like",
}

# Import key components for easy access
from .utils import set_seed, auto_device, dino_transform
from .models import EmbeddingDataset, EmbeddingDropoutMLP

# Aliases for backward compatibility
FeatureDataset = EmbeddingDataset
FeatureDropoutMLP = EmbeddingDropoutMLP
from .data_loader import (
    SplitSpec,
    sample_indices_for_fast_pilot,
    extract_features_for_indices,
    maybe_load_or_compute_feature_cache,
    build_feature_cache_path,
    train_feature_model,
    EmbeddingOrganizer,
)
from .attribution_signals import (
    normalized_entropy_from_labels,
    compute_attribution_structure_signals,
)
from .evaluation import (
    binary_auroc,
    confusion_matrix,
    macro_f1,
    standardize,
    train_signal_classifier,
    split_group_balanced_targets,
    evaluate_three_way_classification,
    build_results_markdown,
    save_per_sample_csv,
)

# Visualization and tracking components
from .unified_tracker import ExperimentTracker
from .decision_boundary_viz import (
    plot_decision_boundary,
    visualize_checkpoint,
    visualize_checkpoints_batch,
    reduce_dimensions,
    create_meshgrid,
    load_checkpoint,
)

__all__ = [
    # Constants
    "GROUP_CLEAN",
    "GROUP_ALEATORIC",
    "GROUP_EPISTEMIC",
    "GROUP_NAMES",
    # Utils
    "set_seed",
    "auto_device",
    "dino_transform",
    # Models
    "FeatureDataset",
    "FeatureDropoutMLP",
    # Data loading
    "SplitSpec",
    "sample_indices_for_fast_pilot",
    "extract_features_for_indices",
    "maybe_load_or_compute_feature_cache",
    "build_feature_cache_path",
    "train_feature_model",
    "EmbeddingOrganizer",
    # Attribution signals
    "normalized_entropy_from_labels",
    "compute_attribution_structure_signals",
    # Evaluation
    "binary_auroc",
    "confusion_matrix",
    "macro_f1",
    "standardize",
    "train_signal_classifier",
    "split_group_balanced_targets",
    "evaluate_three_way_classification",
    "build_results_markdown",
    "save_per_sample_csv",
    # Experiment tracking
    "ExperimentTracker",
    # Visualization
    "plot_decision_boundary",
    "visualize_checkpoint",
    "visualize_checkpoints_batch",
    "reduce_dimensions",
    "create_meshgrid",
    "load_checkpoint",
]

# Made with Bob
