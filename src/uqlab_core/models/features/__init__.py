"""Feature extractors for embedding and end-to-end training paths."""

from uqlab_core.models.features.feature_extractors import (
    DINOv2FeatureExtractor,
    create_feature_extractor,
)

__all__ = [
    "DINOv2FeatureExtractor",
    "create_feature_extractor",
]
