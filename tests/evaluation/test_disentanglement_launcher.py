"""Tests for disentanglement benchmark launcher (workflow → Config grid → API payloads)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from uqlab_orchestrator.disentanglement_launcher import (
    build_benchmark_arm_workflow,
    launch_benchmark_arm,
    launch_benchmark_primary,
    launch_disentanglement_benchmark,
    workflow_to_config_grid,
)
from uqlab_orchestrator.config.workflow_defaults import default_workflow


def test_workflow_to_config_grid_quick_fractions():
    wf = default_workflow()
    wf["uncertainty_config"]["sweep_mode"] = "quick"
    wf["uncertainty_config"]["regular_train_per_class"] = 300

    config = workflow_to_config_grid(wf)

    assert config.label_noises[0] == pytest.approx(0.0)
    assert config.label_noises[-1] == pytest.approx(1.0)
    assert all(0.0 <= p <= 1.0 for p in config.label_noises)
    assert all(0.0 < p <= 1.0 for p in config.dataset_sizes)


def test_build_benchmark_arm_noise_grid():
    wf = default_workflow()
    wf["uncertainty_config"]["sweep_mode"] = "quick"

    arm = build_benchmark_arm_workflow(wf, "noise")
    uc = arm["uncertainty_config"]

    assert uc["sweep_kind"] == "label_noise"
    assert uc["aleatoric_sweep_values"] == [0, 25, 50, 75, 100]


def test_build_benchmark_arm_under_train_grid():
    wf = default_workflow()
    wf["uncertainty_config"]["sweep_mode"] = "quick"
    wf["uncertainty_config"]["regular_train_per_class"] = 300

    arm = build_benchmark_arm_workflow(wf, "under_train")
    uc = arm["uncertainty_config"]

    assert uc["sweep_kind"] == "dataset_size"
    assert len(uc["epistemic_sweep_values"]) == 5
    assert max(uc["epistemic_sweep_values"]) <= 300


@patch("uqlab_orchestrator.experiment_launcher.launch_workflow_experiments")
def test_launch_benchmark_arm_delegates(mock_launch):
    mock_launch.return_value = {"ok": True, "n_created": 5}
    wf = default_workflow()

    result = launch_benchmark_arm(wf, "noise", auto_start=True)

    assert result["ok"] is True
    mock_launch.assert_called_once()
    arm = mock_launch.call_args[0][0]
    assert arm["uncertainty_config"]["sweep_kind"] == "label_noise"


@patch("uqlab_orchestrator.experiment_launcher.merge_launch_results")
@patch("uqlab_orchestrator.disentanglement_launcher.launch_benchmark_arm")
def test_launch_disentanglement_benchmark_both_arms(mock_arm, mock_merge):
    mock_arm.side_effect = [{"ok": True}, {"ok": True}]
    mock_merge.return_value = {"ok": True, "n_created": 10}
    wf = default_workflow()

    launch_disentanglement_benchmark(wf, auto_start=False, profiles=["noise", "under_train"])

    assert mock_arm.call_count == 2
    mock_merge.assert_called_once()


@patch("uqlab_orchestrator.disentanglement_launcher.launch_benchmark_arm")
def test_launch_benchmark_primary_sweep(mock_arm):
    mock_arm.return_value = {"ok": True}
    wf = default_workflow()
    wf["uncertainty_config"]["sweep_target"] = "label_noise"
    wf["uncertainty_config"]["sweep_enabled"] = True
    wf["uncertainty_config"]["sweep_kind"] = "label_noise"
    wf["uncertainty_config"]["aleatoric_enabled"] = True
    wf["uncertainty_config"]["aleatoric_sweep_enabled"] = True

    launch_benchmark_primary(wf, auto_start=True)

    mock_arm.assert_called_once()
    assert mock_arm.call_args[0][1] == "noise"
