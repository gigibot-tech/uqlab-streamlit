"""
Trainable PyTorch models — lazy facade over subpackages.

Root orchestration: ``training.py``. Import subpackages directly for heavy/torch code.
"""

from __future__ import annotations

_LAZY = {
    "build_model": ("factory", "build_model"),
    "train_feature_model": ("training", "train_feature_model"),
    "train_image_model": ("training", "train_image_model"),
    "build_model_for_run": ("training", "build_model_for_run"),
    "create_feature_extractor": ("features.feature_extractors", "create_feature_extractor"),
    "EmbeddingDataset": ("factory.classification_models", "EmbeddingDataset"),
    "DINOv2FeatureExtractor": ("features.feature_extractors", "DINOv2FeatureExtractor"),
}

__all__ = list(_LAZY.keys())


def __getattr__(name: str):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod_name, attr = spec
    from importlib import import_module

    mod = import_module(f"{__name__}.{mod_name}")
    return getattr(mod, attr)
