"""Architecture names and training scope resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

import torch.nn as nn

from uqlab_core.evaluation.signals.dualxda_tracer import infer_classifier_layer_name

CanonicalArchitecture = Literal["resnet18", "cnn_small", "dinov2_mlp", "pixel_mlp"]
TrainingScope = Literal["full", "head_only", "feature_space"]

_ALIASES = {
    "resnet18": "resnet18",
    "resnet18_mcdropout": "resnet18",
    "cnn_small": "cnn_small",
    "cnn_mcdropout": "cnn_small",
    "dinov2_mlp": "dinov2_mlp",
    "pixel_mlp": "pixel_mlp",
    "pixel-mlp": "pixel_mlp",
    "mlp": "pixel_mlp",
}


def normalize_architecture(name: str) -> CanonicalArchitecture:
    key = (name or "dinov2_mlp").strip().lower()
    if key not in _ALIASES:
        raise ValueError(
            f"Unsupported architecture {name!r}. "
            f"Use one of: {sorted(set(_ALIASES.values()))} (aliases: {sorted(_ALIASES)})"
        )
    return _ALIASES[key]  # type: ignore[return-value]


def normalize_dinov2_model(model_name: str) -> str:
    """Map torch.hub / legacy names to DINOv2 backbone keys (``small``, ``base``, …)."""
    from uqlab_core.models.backbones.dinov2_names import normalize_dinov2_model_name

    return normalize_dinov2_model_name(model_name)


def scope_to_training_mode(
    architecture: CanonicalArchitecture,
    training_scope: TrainingScope,
) -> str:
    """Map training_scope to legacy training_mode for existing pipeline code."""
    if architecture == "dinov2_mlp":
        if training_scope != "feature_space":
            raise ValueError("dinov2_mlp only supports training_scope=feature_space")
        return "feature_space"
    if architecture == "cnn_small":
        if training_scope != "full":
            raise ValueError("cnn_small only supports training_scope=full")
        return "end_to_end"
    if architecture == "pixel_mlp":
        if training_scope != "full":
            raise ValueError("pixel_mlp only supports training_scope=full")
        return "end_to_end"
    # resnet18
    if training_scope == "full":
        return "end_to_end"
    if training_scope in ("head_only", "feature_space"):
        return "feature_space"
    raise ValueError(f"Invalid training_scope {training_scope!r}")


def validate_scope_for_architecture(
    architecture: CanonicalArchitecture,
    training_scope: TrainingScope,
) -> None:
    scope_to_training_mode(architecture, training_scope)


def legacy_architecture_name(canonical: CanonicalArchitecture) -> str:
    """Backward-compatible YAML name for older configs."""
    return {
        "resnet18": "resnet18_mcdropout",
        "cnn_small": "cnn_mcdropout",
        "dinov2_mlp": "dinov2_mlp",
        "pixel_mlp": "pixel_mlp",
    }[canonical]


DataMode = Literal["images", "embeddings"]


@dataclass(frozen=True)
class ResolvedTrainingScope:
    scope: TrainingScope
    architecture: CanonicalArchitecture
    classifier_layer: str
    data_mode: DataMode
    training_mode: str  # legacy: feature_space | end_to_end


def _trainable_prefixes(model: nn.Module) -> tuple[str, ...]:
    return tuple(name for name, p in model.named_parameters() if p.requires_grad)


def resolve_training_scope(
    model: nn.Module,
    *,
    architecture: str,
    training_scope: TrainingScope,
) -> ResolvedTrainingScope:
    canonical = normalize_architecture(architecture)
    classifier_layer = infer_classifier_layer_name(model)

    if canonical == "dinov2_mlp":
        data_mode: DataMode = "embeddings"
        training_mode = "feature_space"
    else:
        data_mode = "images"
        training_mode = "end_to_end" if training_scope == "full" else "feature_space"

    return ResolvedTrainingScope(
        scope=training_scope,
        architecture=canonical,
        classifier_layer=classifier_layer,
        data_mode=data_mode,
        training_mode=training_mode,
    )


def validate_training_scope(model: nn.Module, resolved: ResolvedTrainingScope) -> None:
    """Ensure frozen/trainable params match declared scope."""
    trainable = _trainable_prefixes(model)
    if not trainable:
        raise ValueError("Model has no trainable parameters")

    layer = resolved.classifier_layer
    head_prefix = layer.split(".")[0]

    if resolved.scope == "full":
        frozen = [n for n, p in model.named_parameters() if not p.requires_grad]
        if frozen and resolved.architecture != "dinov2_mlp":
            raise ValueError(
                f"training_scope=full but parameters are frozen: {frozen[:5]}"
            )
        return

    if resolved.scope in ("head_only", "feature_space"):
        non_head = [n for n in trainable if not n.startswith(head_prefix) and head_prefix not in n]
        if resolved.architecture == "resnet18" and non_head:
            raise ValueError(
                f"training_scope={resolved.scope} but non-head params trainable: {non_head[:5]}"
            )


__all__ = [
    "CanonicalArchitecture",
    "DataMode",
    "ResolvedTrainingScope",
    "TrainingScope",
    "legacy_architecture_name",
    "normalize_architecture",
    "normalize_dinov2_model",
    "resolve_training_scope",
    "scope_to_training_mode",
    "validate_scope_for_architecture",
    "validate_training_scope",
]
