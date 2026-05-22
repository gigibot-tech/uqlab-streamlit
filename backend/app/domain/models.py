"""Domain models for training configuration and results."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TrainingConfig(BaseModel):
    """Training configuration value object.
    
    Parameters being swept in batch experiments should be set to None.
    The batch service will fill in the swept values for each run.
    """

    # Data parameters
    noise_type: str = Field(default="worse_label", description="CIFAR-10N noise type")
    under_supported_classes: Optional[str] = Field(default="3,5", description="Comma-separated class IDs")
    under_train_per_class: Optional[int] = Field(default=50, ge=1, le=5000)
    regular_train_per_class: Optional[int] = Field(default=300, ge=1, le=5000)
    eval_per_group: Optional[int] = Field(default=600, ge=1, le=10000)

    # Model parameters
    dinov2_model: str = Field(default="small", description="DINOv2 model size")
    hidden_dim: Optional[int] = Field(default=256, ge=1, le=2048)
    dropout: Optional[float] = Field(default=0.2, ge=0.0, le=1.0)

    # Training parameters
    epochs: Optional[int] = Field(default=12, ge=1, le=1000)
    learning_rate: Optional[float] = Field(default=0.001, ge=0.0, le=1.0)
    weight_decay: Optional[float] = Field(default=0.0001, ge=0.0, le=1.0)
    train_batch_size: Optional[int] = Field(default=256, ge=1, le=1024)

    # Evaluation parameters
    mc_passes: Optional[int] = Field(default=20, ge=1, le=1000)
    attribution_method: str = Field(default="dualxda", description="Attribution method")

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-compatible dictionary for ML script."""
        return {
            "seed": 42,
            "device": "auto",
            "data": {
                "noise_type": self.noise_type,
                "under_supported_classes": self.under_supported_classes,
                "under_train_per_class": self.under_train_per_class,
                "regular_train_per_class": self.regular_train_per_class,
                "eval_per_group": self.eval_per_group,
            },
            "model": {
                "dinov2_model": self.dinov2_model,
                "hidden_dim": self.hidden_dim,
                "dropout": self.dropout,
            },
            "training": {
                "epochs": self.epochs,
                "learning_rate": self.learning_rate,
                "weight_decay": self.weight_decay,
                "train_batch_size": self.train_batch_size,
                "feature_batch_size": 64,
            },
            "evaluation": {
                "mc_passes": self.mc_passes,
                "top_k": 10,
            },
            "paths": {
                "cifar10n_root": "./data/cifar10n",
                "feature_cache_dir": "./cache/fast_uncertainty_classification/features",
                "results_base_dir": "./results",
            },
        }

    class Config:
        """Pydantic config."""

        frozen = True  # Immutable value object


class TrainingResult(BaseModel):
    """Training results value object."""

    aleatoric_auroc: float = Field(description="AUROC for aleatoric uncertainty detection")
    epistemic_auroc: float = Field(description="AUROC for epistemic uncertainty detection")
    train_size: int = Field(description="Number of training samples")
    eval_sizes: Dict[str, int] = Field(description="Evaluation set sizes per group")
    best_signals: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict, description="Best performing signals with per-signal AUROC data (7×2 structure)"
    )
    results_path: Optional[str] = Field(None, description="Path to detailed results")

    class Config:
        """Pydantic config."""

        frozen = True  # Immutable value object


# Made with Bob