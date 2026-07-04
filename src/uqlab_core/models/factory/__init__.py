"""Model factory — build_model and architecture implementations."""

from uqlab_core.models.factory.classification_models import EmbeddingDataset, EmbeddingDropoutMLP, EmbeddingMLP
from uqlab_core.models.factory.factory import (
    ResNet18MCDropout,
    SmallCNN,
    build_model,
)

__all__ = [
    "EmbeddingDataset",
    "EmbeddingDropoutMLP",
    "EmbeddingMLP",
    "ResNet18MCDropout",
    "SmallCNN",
    "build_model",
]
