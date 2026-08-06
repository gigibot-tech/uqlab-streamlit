"""Model factory — build_model and architecture implementations."""

from .architecture import (
    CanonicalArchitecture,
    TrainingScope,
    normalize_architecture,
    normalize_dinov2_model,
    scope_to_training_mode,
)
from .classification_models import EmbeddingDataset, EmbeddingDropoutMLP, EmbeddingMLP
from .factory import (
    ResNet18MCDropout,
    SmallCNN,
    build_model,
)
from .training_scope import (
    ResolvedTrainingScope,
    resolve_training_scope,
    validate_training_scope,
)

__all__ = [
    "CanonicalArchitecture",
    "EmbeddingDataset",
    "EmbeddingDropoutMLP",
    "EmbeddingMLP",
    "ResNet18MCDropout",
    "ResolvedTrainingScope",
    "SmallCNN",
    "TrainingScope",
    "build_model",
    "normalize_architecture",
    "normalize_dinov2_model",
    "resolve_training_scope",
    "scope_to_training_mode",
    "validate_training_scope",
]
