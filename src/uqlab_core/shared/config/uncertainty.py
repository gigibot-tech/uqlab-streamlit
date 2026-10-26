"""
Uncertainty perspective registry — single source of truth for N sweep types.

Add a perspective to ``UNCERTAINTY_PERSPECTIVES``; Step 3, launch preview, Run both,
and Results iterate this list (mirror = all other N−1 profiles).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


# Constants for sweep targets - must be defined before UncertaintyPerspective
SINGLE_SWEEP_TARGET = "single"
SWEEP_BOTH_TARGET = "sweep_both"


@dataclass(frozen=True)
class UncertaintyPerspective:
    """One uncertainty axis that can be swept or held fixed as a mirror."""

    id: str
    """Stable id, e.g. ``epistemic``."""

    sweep_target: str
    """Step 3 ``sweep_target`` when this axis is primary: ``under_train`` | ``label_noise``."""

    profile_key: str
    """Paper arm key for ``build_paper_profile_workflow``: ``under_train`` | ``noise``."""

    fig_label: str
    """Paper figure hint, e.g. ``Fig. 3``."""

    label: str
    """Human label for UI."""

    short_label: str
    """Compact label for Results campaign strings."""

    step3_option_label: str
    """Radio option in Step 3 when sweeping this axis."""

    fixed_panel_id: str
    """Which Step 3 panel to show as fixed mirror when another axis is swept."""


UNCERTAINTY_PERSPECTIVES: tuple[UncertaintyPerspective, ...] = (
    UncertaintyPerspective(
        id="epistemic",
        sweep_target="under_train",
        profile_key="under_train",
        fig_label="Fig. 3",
        label="Epistemic (under-train)",
        short_label="under-train",
        step3_option_label="Start sweep (Fig. 3) — under-train",
        fixed_panel_id="epistemic",
    ),
    UncertaintyPerspective(
        id="aleatoric",
        sweep_target="label_noise",
        profile_key="noise",
        fig_label="Fig. 4",
        label="Aleatoric (label noise)",
        short_label="noise",
        step3_option_label="Start sweep (Fig. 4) — label noise",
        fixed_panel_id="aleatoric",
    ),
)


def iter_perspectives() -> Iterator[UncertaintyPerspective]:
    """All registered uncertainty perspectives (extensible N)."""
    yield from UNCERTAINTY_PERSPECTIVES


def perspective_count() -> int:
    return len(UNCERTAINTY_PERSPECTIVES)


def perspective_by_id(perspective_id: str) -> UncertaintyPerspective:
    for p in UNCERTAINTY_PERSPECTIVES:
        if p.id == perspective_id:
            return p
    raise KeyError(f"Unknown perspective id: {perspective_id!r}")


def perspective_by_sweep_target(sweep_target: str) -> UncertaintyPerspective | None:
    if sweep_target == SINGLE_SWEEP_TARGET:
        return None
    for p in UNCERTAINTY_PERSPECTIVES:
        if p.sweep_target == sweep_target:
            return p
    return None


def perspective_by_profile(profile_key: str) -> UncertaintyPerspective:
    for p in UNCERTAINTY_PERSPECTIVES:
        if p.profile_key == profile_key:
            return p
    raise KeyError(f"Unknown profile key: {profile_key!r}")


def mirror_perspectives(
    primary: UncertaintyPerspective | None,
) -> tuple[UncertaintyPerspective, ...]:
    """
    All perspectives to mirror when *primary* is swept (or ``None`` for single run).

    Returns the other **N−1** registry entries.
    """
    if primary is None:
        return UNCERTAINTY_PERSPECTIVES
    return tuple(p for p in UNCERTAINTY_PERSPECTIVES if p.id != primary.id)


def all_profile_keys() -> tuple[str, ...]:
    return tuple(p.profile_key for p in UNCERTAINTY_PERSPECTIVES)


def run_both_fig_labels() -> str:
    """Button suffix listing all figures, e.g. ``Fig. 3 + Fig. 4``."""
    return " + ".join(p.fig_label for p in UNCERTAINTY_PERSPECTIVES)
