"""Domain models for training configuration and results."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TrainingConfig(BaseModel):
    """Training configuration value object."""

    # Data parameters
    noise_type: str = Field(default="worse_label", description="CIFAR-10N noise type")
    under_supported_classes: str = Field(default="3,5", description="Comma-separated class IDs")
    under_train_per_class: int = Field(default=50, ge=10, le=500)
    regular_train_per_class: int = Field(default=300, ge=50, le=1000)
    eval_per_group: int = Field(default=600, ge=100, le=2000)

    # Model parameters
    dinov2_model: str = Field(default="small", description="DINOv2 model size")
    hidden_dim: int = Field(default=256, ge=64, le=1024)
    dropout: float = Field(default=0.2, ge=0.0, le=0.9)

    # Training parameters
    epochs: int = Field(default=12, ge=1, le=100)
    learning_rate: float = Field(default=0.001, ge=0.0001, le=0.1)
    weight_decay: float = Field(default=0.0001, ge=0.0, le=0.01)
    train_batch_size: int = Field(default=256, ge=16, le=512)

    # Evaluation parameters
    mc_passes: int = Field(default=20, ge=5, le=100)
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
    best_signals: Dict[str, float] = Field(
        default_factory=dict, description="Best performing signals and their scores"
    )
    results_path: Optional[str] = Field(None, description="Path to detailed results")

    class Config:
        """Pydantic config."""

        frozen = True  # Immutable value object


# Made with Bob