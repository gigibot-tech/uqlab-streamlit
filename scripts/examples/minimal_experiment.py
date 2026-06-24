"""
Minimal Uncertainty Quantification Experiment
==============================================

This script shows the ESSENTIAL code for an UQ experiment.
Compare this to run_fast_uncertainty_classification.py (800+ lines).

The difference:
- This: ~80 lines of actual ML logic
- Full script: ~800 lines (90% is config parsing, validation, logging)

Run: python examples/minimal_experiment.py
"""

import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from uqlab.data.loaders.cifar10n_loader import CIFAR10NDataset
from uqlab.data.experiment_loader import (
    EmbeddingOrganizer,
    sample_indices_for_experiment,
    train_feature_model,
)
from uqlab.models.classification_models import EmbeddingDataset
from uqlab.evaluation.metrics import binary_auroc
from uqlab.shared.utils.classification import auto_device, dino_transform, set_seed
from uqlab.evaluation.signals.mc_dropout import calculate_mc_dropout_uncertainty


def run_minimal_experiment():
    """
    The CORE experiment in ~50 lines.
    Everything else in the full script is infrastructure.
    """
    
    # ========== 1. SETUP (3 lines) ==========
    set_seed(42)
    device = auto_device("auto")
    
    # ========== 2. LOAD DATA (5 lines) ==========
    dataset = CIFAR10NDataset(
        root="./data/cifar10n",
        noise_type="worse_label",
        train=True,
        transform=dino_transform(),
        download=True,
    )
    
    # ========== 3. SAMPLE SPLITS (5 lines) ==========
    split = sample_indices_for_experiment(
        dataset,
        under_supported_classes=[3, 5],  # Cat, Dog under-supported
        under_train_per_class=50,        # Few samples for under-supported
        regular_train_per_class=300,     # Normal samples for others
        eval_per_group=600,              # Eval samples per group
        seed=42,
    )
    
    print(f"Train samples: {len(split.train_indices)}")
    print(f"Clean eval: {len(split.clean_eval_indices)}")
    print(f"Aleatoric eval: {len(split.aleatoric_eval_indices)}")
    print(f"Epistemic eval: {len(split.epistemic_eval_indices)}")
    
    # ========== 4. EXTRACT FEATURES (10 lines) ==========
    # This is the complex part - but it's ONE abstraction
    organizer = EmbeddingOrganizer(
        dataset=dataset,
        split_spec=split,
        feature_cache_dir=Path("./cache/features"),
        noise_type="worse_label",
        dinov2_model="small",
        batch_size=64,
        device=device,
    )
    
    print("Extracting DINOv2 features (cached after first run)...")
    organizer.load_or_compute_features()
    
    train_pack = organizer.get_train_pack()
    clean_eval_pack = organizer.get_clean_eval_pack()
    aleatoric_eval_pack = organizer.get_aleatoric_eval_pack()
    epistemic_eval_pack = organizer.get_epistemic_eval_pack()
    
    # ========== 5. TRAIN MODEL (5 lines) ==========
    train_dataset = EmbeddingDataset(
        train_pack["features"],
        train_pack["noisy_labels"],
        train_pack["clean_labels"],
        train_pack["is_noisy"],
        train_pack["original_indices"],
    )
    
    print("Training classifier...")
    model = train_feature_model(
        train_dataset,
        device=device,
        num_classes=10,
        hidden_dim=256,
        dropout=0.2,
        epochs=12,
        batch_size=256,
        learning_rate=0.001,
        weight_decay=0.0001,
    )
    
    # ========== 6. COMPUTE UNCERTAINTY (10 lines) ==========
    print("Computing uncertainty scores...")
    
    # MC Dropout uncertainty for each eval group
    clean_uncertainty = calculate_mc_dropout_uncertainty(
        model.mc_forward(clean_eval_pack["features"].to(device), n_passes=20).cpu()
    )
    aleatoric_uncertainty = calculate_mc_dropout_uncertainty(
        model.mc_forward(aleatoric_eval_pack["features"].to(device), n_passes=20).cpu()
    )
    epistemic_uncertainty = calculate_mc_dropout_uncertainty(
        model.mc_forward(epistemic_eval_pack["features"].to(device), n_passes=20).cpu()
    )
    
    # ========== 7. EVALUATE (10 lines) ==========
    print("\nResults:")
    print("=" * 50)
    
    # Aleatoric: Can we detect noisy labels?
    aleatoric_auroc = binary_auroc(
        aleatoric_uncertainty["entropy"],
        aleatoric_eval_pack["is_noisy"]
    )
    print(f"Aleatoric AUROC (detect noisy labels): {aleatoric_auroc:.3f}")
    
    # Epistemic: Can we detect under-supported classes?
    # Compare epistemic vs clean uncertainty
    combined_uncertainty = torch.cat([
        epistemic_uncertainty["entropy"],
        clean_uncertainty["entropy"]
    ])
    is_epistemic = torch.cat([
        torch.ones(len(epistemic_uncertainty["entropy"]), dtype=torch.bool),
        torch.zeros(len(clean_uncertainty["entropy"]), dtype=torch.bool)
    ])
    epistemic_auroc = binary_auroc(combined_uncertainty, is_epistemic)
    print(f"Epistemic AUROC (detect under-supported): {epistemic_auroc:.3f}")
    
    print("=" * 50)
    print("\nDone! This is the CORE experiment.")
    print("Everything else in the full script is:")
    print("  - Config parsing (100 lines)")
    print("  - Validation (50 lines)")
    print("  - Logging/progress bars (100 lines)")
    print("  - Attribution signals (200 lines)")
    print("  - Result formatting (100 lines)")


if __name__ == "__main__":
    run_minimal_experiment()


# ============================================================================
# COMPARISON: What's in the full script but NOT here?
# ============================================================================
#
# 1. CONFIG PARSING (~100 lines)
#    - YAML loading
#    - CLI argument parsing
#    - Config validation
#    - Path resolution
#    → MODULAR: Use config_schema.py or Hydra
#
# 2. VALIDATION (~50 lines)
#    - Check if data exists
#    - Validate parameter ranges
#    - Check GPU availability
#    → MODULAR: Use config_schema.validate()
#
# 3. LOGGING (~100 lines)
#    - Progress bars
#    - Detailed logging
#    - Experiment tracking
#    → MODULAR: Use unified_tracker.py
#
# 4. ATTRIBUTION SIGNALS (~200 lines)
#    - DualXDA computation
#    - Multiple uncertainty signals
#    - Signal combination
#    → MODULAR: Use attribution_signals.py
#
# 5. RESULT FORMATTING (~100 lines)
#    - Markdown reports
#    - CSV exports
#    - Plots
#    → MODULAR: Use evaluation.py functions
#
# 6. ERROR HANDLING (~50 lines)
#    - Try/catch blocks
#    - Graceful failures
#    - Cleanup
#    → MODULAR: Add as needed
#
# TOTAL: ~600 lines of infrastructure
# CORE ML LOGIC: ~80 lines (this script)
#
# ============================================================================
# YOUR CODE IS WELL-DESIGNED!
# ============================================================================
#
# The "complexity" is actually GOOD ENGINEERING:
# - Modular components (can use or skip)
# - Proper error handling
# - Experiment tracking
# - Multiple uncertainty signals
#
# This minimal script shows the core is simple.
# The full script makes it production-ready.
#
# Made with Bob