"""
Shared YAML config for validation and fast-pilot runs.

Used by ``scripts/run_validation_experiments.py`` and any UI that launches
the same preset sweeps.  One schema → ``run_fast_uncertainty_classification.py``.
"""

from __future__ import annotations

from typing import Any

# Validation sweeps train one backbone; MC dropout runs at eval time as signals
# (predictive_entropy, mutual_info, msp_uncertainty), not as a separate architecture.
ARCHITECTURES: dict[str, dict[str, Any]] = {
    "dinov2_mlp": {
        "name": "DINOv2 + MLP",
        "architecture": "dinov2_mlp",
        "training_mode": "feature_space",
        "hidden_dim": 256,
        "dropout": 0.1,
        "dinov2_model": "small",
    },
}

# Folder keys from older sweeps (--rebuild-only still maps these).
LEGACY_ARCHITECTURE_LABELS: dict[str, str] = {
    "cnn_mcdropout": "CNN MC Dropout",
    "resnet18_mcdropout": "ResNet18 MC Dropout",
}

DATASET_SIZE_SWEEP: dict[str, list[int]] = {
    "quick": [50, 100, 200],
    "full": [50, 100, 200, 300, 500],
}

LABEL_NOISE_SWEEP: dict[str, list[int]] = {
    "quick": [0, 25, 50, 75, 100],
    "full": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
}

TRAINING_CONFIG: dict[str, dict[str, Any]] = {
    "quick": {
        "epochs": 2,
        "mc_passes": 10,
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "train_batch_size": 256,
        "feature_batch_size": 64,
    },
    "full": {
        "epochs": 10,
        "mc_passes": 30,
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "train_batch_size": 256,
        "feature_batch_size": 64,
    },
}

# Default data block (hypothesis-validation preset).
DEFAULT_DATA: dict[str, Any] = {
    "noise_type": "worse_label",
    "under_supported_classes": "3,5",
    "under_train_per_class": 10,
    "eval_per_group": 600,
}

# Eval pools are fixed for a given (seed, sweep knob, data block)—not per architecture.
# Matches uq_disentanglement paper benches: same test/eval split, compare UQ signals/methods.
EVAL_PROTOCOL_NOTE = (
    "architecture_invariant: clean / aleatoric / epistemic eval indices depend only on "
    "data config and seed, not on model architecture."
)

DEFAULT_PATHS: dict[str, str] = {
    "cifar10n_root": "./data/cifar10n",
    "results_base_dir": "./results",
    "feature_cache_dir": "./cache/fast_uncertainty_classification/features",
}


def create_experiment_config(
    arch_key: str,
    mode: str,
    *,
    dataset_size: int | None = None,
    noise_rate: float | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """Build the YAML-shaped dict consumed by ``run_fast_uncertainty_classification``."""
    arch_config = ARCHITECTURES[arch_key]
    train_config = TRAINING_CONFIG[mode]

    config: dict[str, Any] = {
        "seed": seed,
        "device": "auto",
        "data": {
            **DEFAULT_DATA,
            "regular_train_per_class": dataset_size if dataset_size is not None else 500,
            "aleatoric_noise_percentage": noise_rate if noise_rate is not None else 0.0,
        },
        "model": {
            "architecture": arch_config["architecture"],
            "training_mode": arch_config["training_mode"],
            "hidden_dim": arch_config["hidden_dim"],
            "dropout": arch_config["dropout"],
        },
        "training": {
            "epochs": train_config["epochs"],
            "learning_rate": train_config["learning_rate"],
            "weight_decay": train_config["weight_decay"],
            "train_batch_size": train_config["train_batch_size"],
            "feature_batch_size": train_config["feature_batch_size"],
        },
        "evaluation": {
            "mc_passes": train_config["mc_passes"],
            "top_k": 10,
        },
        "paths": dict(DEFAULT_PATHS),
    }

    if arch_key == "dinov2_mlp":
        config["model"]["dinov2_model"] = arch_config["dinov2_model"]

    return config
