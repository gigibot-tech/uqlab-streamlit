"""Tests for modular uncertainty perspective registry and mirroring."""

from __future__ import annotations

from uqlab_core.shared.config.sweep_perspectives import (
    SINGLE_SWEEP_TARGET,
    SWEEP_BOTH_TARGET,
    mirror_perspectives,
    perspective_by_id,
    perspective_by_profile,
    perspective_by_sweep_target,
    perspective_count,
    run_both_fig_labels,
)


def test_registry_has_two_perspectives():
    assert perspective_count() == 2


def test_mirror_perspectives_excludes_primary():
    primary = perspective_by_sweep_target("label_noise")
    assert primary is not None
    mirrors = mirror_perspectives(primary)
    assert len(mirrors) == perspective_count() - 1
    assert all(m.id != primary.id for m in mirrors)


def test_mirror_perspectives_single_includes_all():
    mirrors = mirror_perspectives(None)
    assert len(mirrors) == perspective_count()


def test_perspective_by_id():
    epistemic = perspective_by_id("epistemic")
    assert epistemic.sweep_target == "under_train"
    assert epistemic.profile_key == "under_train"


def test_perspective_by_profile():
    aleatoric = perspective_by_profile("noise")
    assert aleatoric.id == "aleatoric"


def test_perspective_by_sweep_target_single():
    assert perspective_by_sweep_target(SINGLE_SWEEP_TARGET) is None


def test_constants_and_labels():
    assert SINGLE_SWEEP_TARGET == "single"
    assert SWEEP_BOTH_TARGET == "sweep_both"
    assert "Fig. 3" in run_both_fig_labels()
    assert "Fig. 4" in run_both_fig_labels()
