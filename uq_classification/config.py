"""Configuration management for uncertainty classification experiments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class DataConfig:
    """Data loading and splitting configuration."""
    noise_type: str = "worst"
    under_supported_classes: List[int] = None
    under_train_per_class: int = 10
    regular_train_per_class: int = 500
    eval_per_group: int = 600
    
    def __post_init__(self):
        if self.under_supported_classes is None:
            self.under_supported_classes = [3, 5]


@dataclass
class ModelConfig:
    """Model architecture configuration."""
    dinov2_model: str = "dinov2_vitb14"
    hidden_dim: int = 256
    dropout: float = 0.2


@dataclass
class TrainingConfig:
    """Training hyperparameters."""
    epochs: int = 12
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    train_batch_size: int = 256
    feature_batch_size: int = 64


@dataclass
class EvaluationConfig:
    """Evaluation settings."""
    mc_passes: int = 20
    top_k: int = 10


@dataclass
class PathConfig:
    """File paths."""
    cifar10n_root: Path = Path("./data/cifar10n")
    results_base_dir: Path = Path("./results")
    feature_cache_dir: Path = Path("./cache/fast_uncertainty_classification/features")


@dataclass
class ExperimentConfig:
    """Complete experiment configuration."""
    seed: int = 42
    device: str = "auto"
    data: DataConfig = None
    model: ModelConfig = None
    training: TrainingConfig = None
    evaluation: EvaluationConfig = None
    paths: PathConfig = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = DataConfig()
        if self.model is None:
            self.model = ModelConfig()
        if self.training is None:
            self.training = TrainingConfig()
        if self.evaluation is None:
            self.evaluation = EvaluationConfig()
        if self.paths is None:
            self.paths = PathConfig()
    
    @classmethod
    def from_yaml(cls, path: Path) -> ExperimentConfig:
        """Load configuration from YAML file."""
        with open(path) as f:
            config_dict = yaml.safe_load(f)
        
        # Parse data config
        data_dict = config_dict.get("data", {})
        under_classes_str = data_dict.get("under_supported_classes", "3,5")
        under_classes = [int(x.strip()) for x in under_classes_str.split(",") if x.strip()]
        data_config = DataConfig(
            noise_type=data_dict.get("noise_type", "worst"),
            under_supported_classes=under_classes,
            under_train_per_class=data_dict.get("under_train_per_class", 10),
            regular_train_per_class=data_dict.get("regular_train_per_class", 500),
            eval_per_group=data_dict.get("eval_per_group", 600),
        )
        
        # Parse model config
        model_dict = config_dict.get("model", {})
        model_config = ModelConfig(
            dinov2_model=model_dict.get("dinov2_model", "dinov2_vitb14"),
            hidden_dim=model_dict.get("hidden_dim", 256),
            dropout=model_dict.get("dropout", 0.2),
        )
        
        # Parse training config
        training_dict = config_dict.get("training", {})
        training_config = TrainingConfig(
            epochs=training_dict.get("epochs", 12),
            learning_rate=training_dict.get("learning_rate", 1e-3),
            weight_decay=training_dict.get("weight_decay", 1e-4),
            train_batch_size=training_dict.get("train_batch_size", 256),
            feature_batch_size=training_dict.get("feature_batch_size", 64),
        )
        
        # Parse evaluation config
        eval_dict = config_dict.get("evaluation", {})
        eval_config = EvaluationConfig(
            mc_passes=eval_dict.get("mc_passes", 20),
            top_k=eval_dict.get("top_k", 10),
        )
        
        # Parse paths config
        paths_dict = config_dict.get("paths", {})
        paths_config = PathConfig(
            cifar10n_root=Path(paths_dict.get("cifar10n_root", "./data/cifar10n")),
            results_base_dir=Path(paths_dict.get("results_base_dir", "./results")),
            feature_cache_dir=Path(paths_dict.get("feature_cache_dir", "./cache/fast_uncertainty_classification/features")),
        )
        
        return cls(
            seed=config_dict.get("seed", 42),
            device=config_dict.get("device", "auto"),
            data=data_config,
            model=model_config,
            training=training_config,
            evaluation=eval_config,
            paths=paths_config,
        )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fast uncertainty classification with DualXDA attribution signals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/fast_uq_classification.yaml",
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed (overrides config)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to use (overrides config)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Output directory (overrides config)"
    )
    return parser.parse_args()

# Made with Bob
