"""DINOv2 model name constants — no torch/transformers imports."""

from __future__ import annotations

DINOV2_AVAILABLE_MODELS: dict[str, str] = {
    "small": "facebook/dinov2-small",
    "base": "facebook/dinov2-base",
    "large": "facebook/dinov2-large",
    "giant": "facebook/dinov2-giant",
    "small-reg": "facebook/dinov2-small-reg",
    "base-reg": "facebook/dinov2-base-reg",
    "large-reg": "facebook/dinov2-large-reg",
    "giant-reg": "facebook/dinov2-giant-reg",
}

DINOV2_FEATURE_DIMS: dict[str, int] = {
    "small": 384,
    "base": 768,
    "large": 1024,
    "giant": 1536,
}

DINOV2_LEGACY_ALIASES: dict[str, str] = {
    "dinov2_vits14": "small",
    "dinov2_vits14_reg": "small-reg",
    "dinov2_vitb14": "base",
    "dinov2_vitb14_reg": "base-reg",
    "dinov2_vitl14": "large",
    "dinov2_vitl14_reg": "large-reg",
    "dinov2_vitg14": "giant",
    "dinov2_vitg14_reg": "giant-reg",
}


def normalize_dinov2_model_name(model_name: str) -> str:
    """Map torch.hub / legacy names to ``DINOV2_AVAILABLE_MODELS`` keys."""
    if not model_name:
        return "small"
    key = model_name.strip().lower()
    if key in DINOV2_AVAILABLE_MODELS:
        return key
    if key in DINOV2_LEGACY_ALIASES:
        return DINOV2_LEGACY_ALIASES[key]
    if "vits14" in key or key.endswith("-small"):
        return "small-reg" if "reg" in key else "small"
    if "vitb14" in key or key.endswith("-base"):
        return "base-reg" if "reg" in key else "base"
    if "vitl14" in key or key.endswith("-large"):
        return "large-reg" if "reg" in key else "large"
    if "vitg14" in key or key.endswith("-giant"):
        return "giant-reg" if "reg" in key else "giant"
    return key


__all__ = [
    "DINOV2_AVAILABLE_MODELS",
    "DINOV2_FEATURE_DIMS",
    "DINOV2_LEGACY_ALIASES",
    "normalize_dinov2_model_name",
]
