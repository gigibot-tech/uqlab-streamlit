"""Tests for modular uncertainty perspective registry and mirroring."""

from __future__ import annotations

from uqlab_orchestrator.config.workflow_defaults import default_workflow
from uqlab_orchestrator.uncertainty import (
    mirror_perspectives,
    perspective_by_sweep_target,
    perspective_count,
    resolve_launch_plan,
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


def test_resolve_launch_actions_sweep_both_single_button():
    wf = default_workflow()
    wf["uncertainty_config"]["sweep_target"] = "sweep_both"
    wf["uncertainty_config"]["sweep_enabled"] = True
    wf["uncertainty_config"]["epistemic_sweep_enabled"] = True
    wf["uncertainty_config"]["aleatoric_sweep_enabled"] = True
    from uqlab_orchestrator.uncertainty import resolve_launch_actions

    actions = resolve_launch_actions(wf)
    assert len(actions) == 1
    assert actions[0].kind == "primary"
    assert "Launch both sweeps" in actions[0].label


def test_resolve_launch_plan_sweep_one():
    w = default_workflow()
    plan = resolve_launch_plan(w)
    assert plan.sweep_target == "label_noise"
    assert plan.primary["profile"] == "noise"
    assert len(plan.mirror_arms) == 1
    assert plan.mirror_arms[0]["profile"] == "under_train"
    assert len(plan.run_both_arms) == 2


def test_resolve_launch_plan_sweep_both():
    w = default_workflow()
    w["uncertainty_config"]["sweep_target"] = "sweep_both"
    plan = resolve_launch_plan(w)
    assert plan.sweep_target == "sweep_both"
    assert len(plan.run_both_arms) == 2
    assert plan.mirror_arms == ()


def test_resolve_launch_plan_single():
    w = default_workflow()
    w["uncertainty_config"]["sweep_target"] = "single"
    w["uncertainty_config"]["sweep_enabled"] = False
    plan = resolve_launch_plan(w)
    assert plan.sweep_target == "single"
    assert plan.primary["profile"] == "single"
    assert len(plan.mirror_arms) == perspective_count()
