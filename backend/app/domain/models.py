"""Domain models for training configuration and results."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataConfig(BaseModel):
    """Dataset and uncertainty-manipulation parameters."""

    noise_type: str = Field(default="worse_label", description="CIFAR-10N noise type")
    aleatoric_noise_percentage: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Custom uniform noise percentage (0-100). If > 0, overrides CIFAR-10N noise.",
    )
    under_supported_classes: Optional[str] = Field(
        default="3,5", description="Comma-separated class IDs"
    )
    under_train_per_class: Optional[int] = Field(default=50, ge=1, le=5000)
    regular_train_per_class: Optional[int] = Field(default=300, ge=1, le=5000)
    eval_per_group: Optional[int] = Field(default=600, ge=1, le=10000)

    class Config:
        frozen = True


class ModelConfig(BaseModel):
    """Architecture and model-shape parameters."""

    architecture: str = Field(default="resnet18_mcdropout", description="Model architecture (resnet18_mcdropout, dinov2_mlp, cnn_mcdropout)")
    training_mode: str = Field(default="feature_space", description="Training mode")
    dinov2_model: str = Field(default="small", description="DINOv2 model size (only for dinov2_mlp)")
    hidden_dim: Optional[int] = Field(default=256, ge=1, le=2048)
    dropout: Optional[float] = Field(default=0.2, ge=0.0, le=1.0)
    use_untrained_resnet: bool = Field(
        default=False,
        description="If True, use randomly initialized ResNet instead of pretrained weights",
    )
    checkpoint_path: Optional[str] = Field(default=None, description="Path to checkpoint to load (optional)")

    class Config:
        frozen = True


class TrainingRuntimeConfig(BaseModel):
    """Optimization and runtime training parameters."""

    epochs: Optional[int] = Field(default=12, ge=1, le=1000)
    learning_rate: Optional[float] = Field(default=0.001, ge=0.0, le=1.0)
    weight_decay: Optional[float] = Field(default=0.0001, ge=0.0, le=1.0)
    train_batch_size: Optional[int] = Field(default=256, ge=1, le=1024)
    feature_batch_size: int = Field(default=64, ge=1, le=4096)

    class Config:
        frozen = True


class EvaluationConfig(BaseModel):
    """Evaluation and uncertainty scoring parameters."""

    mc_passes: Optional[int] = Field(default=0, ge=0, le=1000, description="MC Dropout passes (0=disabled, baseline)")
    attribution_method: str = Field(default="dualxda", description="Attribution method")
    top_k: int = Field(default=10, ge=1, le=1000)

    class Config:
        frozen = True


class PathsConfig(BaseModel):
    """Filesystem path configuration."""

    cifar10n_root: str = Field(default="./data/cifar10n")
    feature_cache_dir: str = Field(default="./cache/fast_uncertainty_classification/features")
    results_base_dir: str = Field(default="./results")

    class Config:
        frozen = True


class ExperimentConfig(BaseModel):
    """Complete experiment configuration with nested structure.
    
    This is the NEW recommended config format that maps cleanly to folder structure:
    - config.data → 1_data/
    - config.model → 2_models/
    - config.training → 3_training/
    - config.evaluation → 4_evaluation/
    - config.paths → file paths
    """

    seed: int = Field(default=42)
    device: str = Field(default="auto")
    
    data: DataConfig = Field(default_factory=DataConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    training: TrainingRuntimeConfig = Field(default_factory=TrainingRuntimeConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to flat dict for backward compatibility."""
        return {
            "seed": self.seed,
            "device": self.device,
            # Data fields
            "noise_type": self.data.noise_type,
            "aleatoric_noise_percentage": self.data.aleatoric_noise_percentage,
            "under_supported_classes": self.data.under_supported_classes,
            "under_train_per_class": self.data.under_train_per_class,
            "regular_train_per_class": self.data.regular_train_per_class,
            "eval_per_group": self.data.eval_per_group,
            # Model fields
            "architecture": self.model.architecture,
            "training_mode": self.model.training_mode,
            "dinov2_model": self.model.dinov2_model,
            "hidden_dim": self.model.hidden_dim,
            "dropout": self.model.dropout,
            "use_untrained_resnet": self.model.use_untrained_resnet,
            # Training fields
            "epochs": self.training.epochs,
            "learning_rate": self.training.learning_rate,
            "weight_decay": self.training.weight_decay,
            "train_batch_size": self.training.train_batch_size,
            "feature_batch_size": self.training.feature_batch_size,
            # Evaluation fields
            "mc_passes": self.evaluation.mc_passes,
            "attribution_method": self.evaluation.attribution_method,
            "top_k": self.evaluation.top_k,
            # Paths
            "cifar10n_root": self.paths.cifar10n_root,
            "feature_cache_dir": self.paths.feature_cache_dir,
            "results_base_dir": self.paths.results_base_dir,
        }

    @classmethod
    def from_flat_dict(cls, flat: Dict[str, Any]) -> "ExperimentConfig":
        """Create from flat dict (backward compatibility)."""
        return cls(
            seed=flat.get("seed", 42),
            device=flat.get("device", "auto"),
            data=DataConfig(
                noise_type=flat.get("noise_type", "worse_label"),
                aleatoric_noise_percentage=flat.get("aleatoric_noise_percentage", 0.0),
                under_supported_classes=flat.get("under_supported_classes", "3,5"),
                under_train_per_class=flat.get("under_train_per_class", 50),
                regular_train_per_class=flat.get("regular_train_per_class", 300),
                eval_per_group=flat.get("eval_per_group", 600),
            ),
            model=ModelConfig(
                architecture=flat.get("architecture", "resnet18_mcdropout"),
                training_mode=flat.get("training_mode", "feature_space"),
                dinov2_model=flat.get("dinov2_model", "small"),
                hidden_dim=flat.get("hidden_dim", 256),
                dropout=flat.get("dropout", 0.2),
                use_untrained_resnet=flat.get("use_untrained_resnet", False),
                checkpoint_path=flat.get("checkpoint_path"),
            ),
            training=TrainingRuntimeConfig(
                epochs=flat.get("epochs", 12),
                learning_rate=flat.get("learning_rate", 0.001),
                weight_decay=flat.get("weight_decay", 0.0001),
                train_batch_size=flat.get("train_batch_size", 256),
                feature_batch_size=flat.get("feature_batch_size", 64),
            ),
            evaluation=EvaluationConfig(
                mc_passes=flat.get("mc_passes", 0),
                attribution_method=flat.get("attribution_method", "dualxda"),
                top_k=flat.get("top_k", 10),
            ),
            paths=PathsConfig(
                cifar10n_root=flat.get("cifar10n_root", "./data/cifar10n"),
                feature_cache_dir=flat.get("feature_cache_dir", "./cache/fast_uncertainty_classification/features"),
                results_base_dir=flat.get("results_base_dir", "./results"),
            ),
        )

    class Config:
        frozen = True


class TrainingPresetName(str, Enum):
    """Supported named presets for training configuration."""

    QUICK = "quick"
    THOROUGH = "thorough"


class TrainingPreset(BaseModel):
    """Named preset for recommended experiment values."""

    name: TrainingPresetName
    description: str
    config: "TrainingConfig"

    class Config:
        frozen = True


class TrainingConfig(BaseModel):
    """DEPRECATED: Use ExperimentConfig instead.
    
    Training configuration value object with flat API and grouped YAML export.
    This class is kept for backward compatibility but will be removed in future versions.
    """

    seed: int = Field(default=42)
    device: str = Field(default="auto")

    # Data parameters
    noise_type: str = Field(default="worse_label", description="CIFAR-10N noise type")
    aleatoric_noise_percentage: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Custom uniform noise percentage (0-100). If > 0, overrides CIFAR-10N noise.",
    )
    under_supported_classes: Optional[str] = Field(default="3,5", description="Comma-separated class IDs")
    under_train_per_class: Optional[int] = Field(default=50, ge=1, le=5000)
    regular_train_per_class: Optional[int] = Field(default=300, ge=1, le=5000)
    eval_per_group: Optional[int] = Field(default=600, ge=1, le=10000)

    # Model parameters
    architecture: str = Field(default="resnet18_mcdropout", description="Model architecture")
    training_mode: str = Field(default="feature_space", description="Training mode")
    dinov2_model: str = Field(default="small", description="DINOv2 model size")
    hidden_dim: Optional[int] = Field(default=256, ge=1, le=2048)
    dropout: Optional[float] = Field(default=0.2, ge=0.0, le=1.0)
    use_untrained_resnet: bool = Field(
        default=False,
        description="If True, use randomly initialized ResNet instead of pretrained weights",
    )

    # Training parameters
    epochs: Optional[int] = Field(default=12, ge=1, le=1000)
    learning_rate: Optional[float] = Field(default=0.001, ge=0.0, le=1.0)
    weight_decay: Optional[float] = Field(default=0.0001, ge=0.0, le=1.0)
    train_batch_size: Optional[int] = Field(default=256, ge=1, le=1024)
    feature_batch_size: int = Field(default=64, ge=1, le=4096)

    # Evaluation parameters
    mc_passes: Optional[int] = Field(default=0, ge=0, le=1000, description="MC Dropout passes (0=disabled)")
    attribution_method: str = Field(default="dualxda", description="Attribution method")
    top_k: int = Field(default=10, ge=1, le=1000)

    # Path parameters
    cifar10n_root: str = Field(default="./data/cifar10n")
    feature_cache_dir: str = Field(default="./cache/fast_uncertainty_classification/features")
    results_base_dir: str = Field(default="./results")

    @property
    def data(self) -> DataConfig:
        return DataConfig(
            noise_type=self.noise_type,
            aleatoric_noise_percentage=self.aleatoric_noise_percentage,
            under_supported_classes=self.under_supported_classes,
            under_train_per_class=self.under_train_per_class,
            regular_train_per_class=self.regular_train_per_class,
            eval_per_group=self.eval_per_group,
        )

    @property
    def model(self) -> ModelConfig:
        return ModelConfig(
            architecture=self.architecture,
            training_mode=self.training_mode,
            dinov2_model=self.dinov2_model,
            hidden_dim=self.hidden_dim,
            dropout=self.dropout,
            use_untrained_resnet=self.use_untrained_resnet,
        )

    @property
    def training(self) -> TrainingRuntimeConfig:
        return TrainingRuntimeConfig(
            epochs=self.epochs,
            learning_rate=self.learning_rate,
            weight_decay=self.weight_decay,
            train_batch_size=self.train_batch_size,
            feature_batch_size=self.feature_batch_size,
        )

    @property
    def evaluation(self) -> EvaluationConfig:
        return EvaluationConfig(
            mc_passes=self.mc_passes,
            attribution_method=self.attribution_method,
            top_k=self.top_k,
        )

    @property
    def paths(self) -> PathsConfig:
        return PathsConfig(
            cifar10n_root=self.cifar10n_root,
            feature_cache_dir=self.feature_cache_dir,
            results_base_dir=self.results_base_dir,
        )

    @classmethod
    def from_legacy_flat_dict(cls, payload: Dict[str, Any]) -> "TrainingConfig":
        """Build flat config from flat or grouped payloads."""
        if any(key in payload for key in ("data", "model", "training", "evaluation", "paths")):
            data = payload.get("data", {})
            model = payload.get("model", {})
            training = payload.get("training", {})
            evaluation = payload.get("evaluation", {})
            paths = payload.get("paths", {})
            return cls(
                seed=payload.get("seed", 42),
                device=payload.get("device", "auto"),
                noise_type=data.get("noise_type", "worse_label"),
                aleatoric_noise_percentage=data.get("aleatoric_noise_percentage", 0.0),
                under_supported_classes=data.get("under_supported_classes", "3,5"),
                under_train_per_class=data.get("under_train_per_class", 50),
                regular_train_per_class=data.get("regular_train_per_class", 300),
                eval_per_group=data.get("eval_per_group", 600),
                architecture=model.get("architecture", "dinov2_mlp"),
                training_mode=model.get("training_mode", "feature_space"),
                dinov2_model=model.get("dinov2_model", "small"),
                hidden_dim=model.get("hidden_dim", 256),
                dropout=model.get("dropout", 0.2),
                use_untrained_resnet=model.get("use_untrained_resnet", False),
                epochs=training.get("epochs", 12),
                learning_rate=training.get("learning_rate", 0.001),
                weight_decay=training.get("weight_decay", 0.0001),
                train_batch_size=training.get("train_batch_size", 256),
                feature_batch_size=training.get("feature_batch_size", 64),
                mc_passes=evaluation.get("mc_passes", 20),
                attribution_method=evaluation.get("attribution_method", "dualxda"),
                top_k=evaluation.get("top_k", 10),
                cifar10n_root=paths.get("cifar10n_root", "./data/cifar10n"),
                feature_cache_dir=paths.get(
                    "feature_cache_dir", "./cache/fast_uncertainty_classification/features"
                ),
                results_base_dir=paths.get("results_base_dir", "./results"),
            )

        return cls(**payload)

    def to_flat_dict(self) -> Dict[str, Any]:
        """Flatten config for legacy sweep/UI code paths."""
        return self.model_dump()

    def with_flat_override(self, parameter: str, value: int | float) -> "TrainingConfig":
        """Apply a sweep override using flat names or dotted grouped paths."""
        if "." not in parameter:
            updated = self.to_flat_dict()
            updated[parameter] = value
            return TrainingConfig(**updated)

        grouped = self.to_yaml_dict()
        target: Dict[str, Any] = grouped
        parts = parameter.split(".")

        for part in parts[:-1]:
            next_value = target.get(part)
            if not isinstance(next_value, dict):
                raise ValueError(f"Unknown dotted config path: {parameter}")
            target = next_value

        leaf = parts[-1]
        if leaf not in target:
            raise ValueError(f"Unknown dotted config path: {parameter}")

        target[leaf] = value
        return TrainingConfig.from_legacy_flat_dict(grouped)

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to grouped YAML-compatible dictionary for ML script."""
        return {
            "seed": self.seed,
            "device": self.device,
            "data": self.data.model_dump(),
            "model": self.model.model_dump(),
            "training": self.training.model_dump(),
            "evaluation": self.evaluation.model_dump(),
            "paths": self.paths.model_dump(),
        }

    @classmethod
    def quick_preset(cls) -> TrainingPreset:
        """Recommended values for quick experiments (5-10 min)."""
        return TrainingPreset(
            name=TrainingPresetName.QUICK,
            description="Quick experiments (5-10 min)",
            config=cls(
                under_train_per_class=40,
                regular_train_per_class=250,
                eval_per_group=500,
                dinov2_model="small",
                epochs=10,
                mc_passes=15,
                top_k=8,
            ),
        )

    @classmethod
    def thorough_preset(cls) -> TrainingPreset:
        """Recommended values for thorough experiments (30-60 min)."""
        return TrainingPreset(
            name=TrainingPresetName.THOROUGH,
            description="Thorough experiments (30-60 min)",
            config=cls(
                under_train_per_class=150,
                regular_train_per_class=750,
                eval_per_group=1500,
                dinov2_model="base",
                epochs=24,
                mc_passes=75,
                top_k=30,
            ),
        )

    @classmethod
    def recommended_presets(cls) -> list[TrainingPreset]:
        """Return named recommended presets."""
        return [cls.quick_preset(), cls.thorough_preset()]

    @classmethod
    def preset_config(cls, preset: TrainingPresetName) -> "TrainingConfig":
        """Resolve a named preset into a concrete training config."""
        if preset == TrainingPresetName.QUICK:
            return cls.quick_preset().config
        if preset == TrainingPresetName.THOROUGH:
            return cls.thorough_preset().config
        raise ValueError(f"Unsupported preset: {preset}")

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