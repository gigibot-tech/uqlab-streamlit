"""Tests for modular uncertainty perspective registry and mirroring."""

from __future__ import annotations

from uqlab_core.shared.config.uncertainty_perspectives import (
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


def test_single_sweep_target_constant():
    assert SINGLE_SWEEP_TARGET == "single"


def test_sweep_both_target_constant():
    assert SWEEP_BOTH_TARGET == "sweep_both"


def test_perspective_by_id():
    epistemic = perspective_by_id("epistemic")
    assert epistemic.id == "epistemic"
    assert epistemic.sweep_target == "under_train"

    aleatoric = perspective_by_id("aleatoric")
    assert aleatoric.id == "aleatoric"
    assert aleatoric.sweep_target == "label_noise"


def test_perspective_by_profile():
    noise = perspective_by_profile("noise")
    assert noise.id == "aleatoric"

    under_train = perspective_by_profile("under_train")
    assert under_train.id == "epistemic"


def test_perspective_by_sweep_target():
    assert perspective_by_sweep_target("single") is None
    assert perspective_by_sweep_target("under_train").id == "epistemic"
    assert perspective_by_sweep_target("label_noise").id == "aleatoric"


def test_mirror_perspectives_excludes_primary():
    primary = perspective_by_sweep_target("label_noise")
    assert primary is not None
    mirrors = mirror_perspectives(primary)
    assert len(mirrors) == perspective_count() - 1
    assert all(m.id != primary.id for m in mirrors)


def test_mirror_perspectives_single_includes_all():
    mirrors = mirror_perspectives(None)
    assert len(mirrors) == perspective_count()


def test_run_both_fig_labels():
    assert "Fig. 3" in run_both_fig_labels()
    assert "Fig. 4" in run_both_fig_labels()
