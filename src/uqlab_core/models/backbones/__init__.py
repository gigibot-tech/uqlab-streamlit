"""Model backbones and baseline architectures."""

from uqlab_core.models.backbones.dinov2_backbone import DINOv2Backbone, create_dinov2_model

__all__ = ["create_dinov2_model", "DINOv2Backbone"]
