"""Model factory — build_model and architecture implementations."""

from uqlab_core.models.factory.classification_models import EmbeddingDataset, EmbeddingDropoutMLP, EmbeddingMLP
from uqlab_core.models.factory.factory import (
    ResNet18MCDropout,
    SmallCNN,
    build_model,
)
from uqlab_core.models.factory.scope import (
    CanonicalArchitecture,
    ResolvedTrainingScope,
    TrainingScope,
    legacy_architecture_name,
    normalize_architecture,
    normalize_dinov2_model,
    resolve_training_scope,
    scope_to_training_mode,
    validate_scope_for_architecture,
    validate_training_scope,
)

__all__ = [
    "CanonicalArchitecture",
    "EmbeddingDataset",
    "EmbeddingDropoutMLP",
    "EmbeddingMLP",
    "ResolvedTrainingScope",
    "ResNet18MCDropout",
    "SmallCNN",
    "TrainingScope",
    "build_model",
    "legacy_architecture_name",
    "normalize_architecture",
    "normalize_dinov2_model",
    "resolve_training_scope",
    "scope_to_training_mode",
    "validate_scope_for_architecture",
    "validate_training_scope",
]
