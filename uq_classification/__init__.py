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
    - lightning_module: PyTorch Lightning training (Layer 2)
    - data_module: PyTorch Lightning data loading (Layer 2)
    - tracking: MLflow/TensorBoard/CSV logging (Layer 3)
    - experiment_manager: py-experimenter wrapper (Layer 1)
    - models: Neural network architectures (FeatureDropoutMLP, FeatureDataset)
    - data_loader: Data loading, feature extraction, and split sampling
    - attribution_signals: Attribution-based uncertainty signal computation
    - evaluation: Model evaluation metrics (AUROC, F1, confusion matrix)
    - utils: Helper functions (seed setting, device management, transforms)

Reused from src/:
    - src.metrics.mc_dropout_uq: Predictive uncertainty metrics
    - src.models.dinov2_backbone: DINOv2 feature extraction
    - src.triage.dualxda_axioms: DualXDA attribution tracing
    - src.data.cifar10n_loader: CIFAR-10N dataset loading
"""

__version__ = "2.0.0"

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
from .models import FeatureDataset, FeatureDropoutMLP
from .data_loader import (
    SplitSpec,
    sample_indices_for_fast_pilot,
    extract_features_for_indices,
    maybe_load_or_compute_feature_cache,
    build_feature_cache_path,
    train_feature_model,
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
]

# Made with Bob
