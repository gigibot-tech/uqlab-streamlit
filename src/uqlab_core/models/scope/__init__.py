"""Backward-compatibility shim for the relocated scope module.

Implementation now lives directly under ``uqlab_core.models``:
- ``architecture``
- ``training_scope``
"""

from uqlab_core.models.architecture import (
    CanonicalArchitecture,
    TrainingScope,
    normalize_architecture,
    normalize_dinov2_model,
    scope_to_training_mode,
)
from uqlab_core.models.training_scope import (
    ResolvedTrainingScope,
    resolve_training_scope,
    validate_training_scope,
)

__all__ = [
    "CanonicalArchitecture",
    "ResolvedTrainingScope",
    "TrainingScope",
    "normalize_architecture",
    "normalize_dinov2_model",
    "resolve_training_scope",
    "scope_to_training_mode",
    "validate_training_scope",
]
