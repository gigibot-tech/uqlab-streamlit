"""Tests for modular uncertainty perspective registry and mirroring."""

from __future__ import annotations

from uqlab_core.shared.config.uncertainty import (
    UNCERTAINTY_PERSPECTIVES,
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
    assert epistemic.id == "epistemic"


def test_perspective_by_profile():
    noise = perspective_by_profile("noise")
    assert noise.profile_key == "noise"


def test_perspective_by_sweep_target_single():
    assert perspective_by_sweep_target("single") is None


def test_run_both_fig_labels():
    assert run_both_fig_labels() == "Fig. 3 + Fig. 4"


def test_uncertainty_perspectives_immutable():
    assert UNCERTAINTY_PERSPECTIVES[0].sweep_target == "under_train"
    assert UNCERTAINTY_PERSPECTIVES[1].sweep_target == "label_noise"
