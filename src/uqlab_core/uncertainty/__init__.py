"""Uncertainty perspective registry and helpers."""

from __future__ import annotations

from uqlab_core.uncertainty.registry import (
    SINGLE_SWEEP_TARGET,
    SWEEP_BOTH_TARGET,
    UNCERTAINTY_PERSPECTIVES,
    UncertaintyPerspective,
    all_profile_keys,
    iter_perspectives,
    mirror_perspectives,
    perspective_by_id,
    perspective_by_profile,
    perspective_by_sweep_target,
    perspective_count,
    run_both_fig_labels,
)

__all__ = [
    "SINGLE_SWEEP_TARGET",
    "SWEEP_BOTH_TARGET",
    "UNCERTAINTY_PERSPECTIVES",
    "UncertaintyPerspective",
    "all_profile_keys",
    "iter_perspectives",
    "mirror_perspectives",
    "perspective_by_id",
    "perspective_by_profile",
    "perspective_by_sweep_target",
    "perspective_count",
    "run_both_fig_labels",
]
