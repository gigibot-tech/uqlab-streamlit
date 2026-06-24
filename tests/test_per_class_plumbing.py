"""Tests for per-class launch plumbing (run_spec emission + data_setup guard)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from uqlab.evaluation.pipeline.data_setup import (
    PilotDataRequest,
    parse_pilot_data_request,
    validate_pilot_data_request,
)
from uqlab.shared.config.classification import (
    DataConfig,
    EvaluationConfig,
    ExperimentConfig,
    ModelConfig,
    PathConfig,
    PerClassConfig,
    TrainingConfig,
)
from uqlab_orchestrator.config.workflow_defaults import default_workflow
from uqlab_orchestrator.disentanglement_launcher import launch_benchmark_primary
from uqlab_orchestrator.run_spec import build_run_yaml, generate_sweep_runs


def _minimal_per_class_config() -> dict[int, PerClassConfig]:
    config: dict[int, PerClassConfig] = {}
    for class_id in range(10):
        config[class_id] = PerClassConfig(
            train_samples=300,
            label_noise_pct=0.0,
            sweep_epistemic=False,
            sweep_aleatoric=False,
        )
    return config


def _per_class_workflow(*, sweep_epistemic: bool = False) -> dict:
    wf = default_workflow()
    wf["use_per_class_mode"] = True
    per_class = _minimal_per_class_config()
    if sweep_epistemic:
        per_class[4] = PerClassConfig(
            train_samples=300,
            label_noise_pct=0.0,
            sweep_epistemic=True,
            sweep_aleatoric=False,
        )
    wf["per_class_config"] = per_class
    wf["epistemic_sweep_preset"] = "quick"
    wf["aleatoric_sweep_preset"] = "quick"
    return wf


def test_build_run_yaml_emits_per_class_partition():
    cfg = build_run_yaml(_per_class_workflow())
    assert cfg["data"]["partition_mode"] == "per_class"
    assert "per_class_config" in cfg["data"]
    assert "0" in cfg["data"]["per_class_config"]
    assert cfg["data"]["per_class_config"]["0"]["train_samples"] == 300


def test_generate_sweep_runs_expands_per_class_epistemic_sweep():
    runs = generate_sweep_runs(_per_class_workflow(sweep_epistemic=True))
    assert len(runs) == 3
    for kind, yaml_cfg in runs:
        assert kind == "per_class_epistemic"
        assert yaml_cfg["data"]["partition_mode"] == "per_class"
        assert "per_class_config" in yaml_cfg["data"]


def test_generate_sweep_runs_single_per_class_without_sweep_flags():
    runs = generate_sweep_runs(_per_class_workflow(sweep_epistemic=False))
    assert len(runs) == 1
    kind, yaml_cfg = runs[0]
    assert kind == "single"
    assert yaml_cfg["data"]["partition_mode"] == "per_class"


def _per_class_experiment_config() -> ExperimentConfig:
    per_class = {
        0: PerClassConfig(train_samples=300, label_noise_pct=0.0),
    }
    return ExperimentConfig(
        data=DataConfig(
            dataset_name="cifar10",
            noise_type="clean_label",
            partition_mode="per_class",
            per_class_config=per_class,
            eval_per_group=100,
        ),
        model=ModelConfig(architecture="resnet18", training_mode="end_to_end", dropout=0.0),
        training=TrainingConfig(epochs=2),
        evaluation=EvaluationConfig(mc_passes=10),
        paths=PathConfig(
            data_root="./data/cifar10",
            cifar10n_root="./data/cifar10",
            feature_cache_dir="./cache",
            results_base_dir="./results",
        ),
    )


def test_validate_pilot_data_request_per_class_raises():
    config = _per_class_experiment_config()
    request = parse_pilot_data_request(config, Path("."))
    assert request.partition_mode == "per_class"
    with pytest.raises(NotImplementedError, match="partition_mode=per_class"):
        validate_pilot_data_request(request)


def test_disentanglement_launcher_has_no_per_class_launcher_import():
    source = Path(__file__).resolve().parents[1] / "src" / "uqlab_orchestrator" / "disentanglement_launcher.py"
    text = source.read_text()
    assert "per_class_launcher" not in text


@patch("uqlab_orchestrator.experiment_launcher.launch_workflow_experiments")
def test_launch_benchmark_primary_per_class_uses_experiment_launcher(mock_launch):
    mock_launch.return_value = {"ok": True, "n_created": 1}
    wf = _per_class_workflow()

    result = launch_benchmark_primary(wf, auto_start=True)

    assert result["per_class_mode"] is True
    assert "sweep_summary" in result
    mock_launch.assert_called_once_with(wf, auto_start=True, highlight_callback=None)
