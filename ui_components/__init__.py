"""
UI Components Package

This package contains modular UI components for the Streamlit Uncertainty
Quantification application. All components are re-exported here for backward
compatibility with existing imports.

Module Organization:
- dataset.py: Dataset selection and configuration
- experiment_config.py: Single experiment configuration
- batch_config.py: Batch experiment configuration
- results.py: Experiment results visualization
- signal_visualization.py: Per-signal AUROC visualization
- utils.py: Helper functions and utilities
"""

# Dataset components
from .dataset import (
    render_dataset_selection,
    render_dataset_comparison,
)

# Experiment configuration components
from .experiment_config import (
    render_epistemic_config,
    render_epistemic_strength,
    render_aleatoric_config,
    render_aleatoric_strength,
    render_model_config,
    render_training_config,
    render_evaluation_config,
    render_evaluation_strategy,
    build_base_experiment_config,
)

# Batch configuration components
from .batch_config import (
    render_batch_sweep_config,
    render_batch_base_config,
)

# 2D Batch sweep components
from .batch_2d_sweep import (
    render_2d_sweep_config,
    render_2d_heatmap,
    render_2d_results_analysis,
)

# Results visualization components
from .results import (
    render_experiment_results,
)

# Signal visualization components
from .signal_visualization import (
    render_batch_results,
)

# Model selector components
from .model_selector import (
    render_model_selector,
    render_model_inference_panel,
)

# Data overlap analysis
from .data_overlap_analysis import (
    render_data_overlap_analysis,
)

# Experiment validation components
from .experiment_validation import (
    render_experiment_type_validation,
    render_validation_summary,
    get_validation_badge,
    validate_sweep_configuration,
)

# Utility components
from .utils import (
    render_configuration_progress,
    render_roc_explanation,
)

# Define what gets exported with "from ui_components import *"
__all__ = [
    # Dataset
    'render_dataset_selection',
    'render_dataset_comparison',
    # Experiment config
    'render_epistemic_config',
    'render_epistemic_strength',
    'render_aleatoric_config',
    'render_aleatoric_strength',
    'render_model_config',
    'render_training_config',
    'render_evaluation_config',
    'render_evaluation_strategy',
    'build_base_experiment_config',
    # Batch config
    'render_batch_sweep_config',
    'render_batch_base_config',
    # 2D Batch sweep
    'render_2d_sweep_config',
    'render_2d_heatmap',
    'render_2d_results_analysis',
    # Results
    'render_experiment_results',
    'render_batch_results',
    # Model selector
    'render_model_selector',
    'render_model_inference_panel',
    # Data overlap analysis
    'render_data_overlap_analysis',
    # Experiment validation
    'render_experiment_type_validation',
    'render_validation_summary',
    'get_validation_badge',
    'validate_sweep_configuration',
    # Utils
    'render_configuration_progress',
    'render_roc_explanation',
]

# Made with Bob
