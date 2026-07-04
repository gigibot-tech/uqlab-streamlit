"""Train/eval index splits and four-region partition logic."""

from uqlab_core.data.splits.experiment_loader import (
    EmbeddingOrganizer,
    SplitSpec,
    expects_aleatoric_eval,
    expects_epistemic_eval,
    sample_indices_for_experiment,
)
from uqlab_core.data.splits.four_region import (
    DEFAULT_FOUR_REGION_PRESET,
    ALL_REGIONS,
    REGION_CLEAN,
    REGION_NOISY,
    REGION_OOD,
    REGION_SPARSE,
    apply_region_noise,
    build_split_spec,
    normalize_class_regions,
    sample_indices_for_four_region,
    validate_class_regions,
)

__all__ = [
    "ALL_REGIONS",
    "DEFAULT_FOUR_REGION_PRESET",
    "EmbeddingOrganizer",
    "REGION_CLEAN",
    "REGION_NOISY",
    "REGION_OOD",
    "REGION_SPARSE",
    "SplitSpec",
    "apply_region_noise",
    "build_split_spec",
    "expects_aleatoric_eval",
    "expects_epistemic_eval",
    "normalize_class_regions",
    "sample_indices_for_experiment",
    "sample_indices_for_four_region",
    "validate_class_regions",
]
