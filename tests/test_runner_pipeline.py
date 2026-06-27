"""Tests for unified runner execute entry."""

from __future__ import annotations

from pathlib import Path

import pytest

from uqlab.runner.execute import run_from_yaml


def test_run_config_skips_yaml_load_when_config_in_context():
    from uqlab.runner.execute import RunContext, _stage_load_config

    sentinel = object()
    ctx = RunContext(data={"config": sentinel, "config_path": None})
    out = _stage_load_config(ctx)
    assert out.get("config") is sentinel


def test_run_load_stage_reads_yaml(tmp_path):
    from uqlab.runner.execute import RunContext, _stage_load_config

    yaml_path = tmp_path / "config.yaml"
    yaml_path.write_text(
        """
model:
  architecture: resnet18
  training_scope: head_only
  training_mode: feature_space
  dropout: 0.0
data:
  dataset_name: cifar10
  under_train_per_class: 100
evaluation:
  mc_passes: 0
  signals: [inverse_mass]
seed: 42
device: cpu
paths:
  results_base_dir: results
""".strip(),
        encoding="utf-8",
    )
    ctx = RunContext(data={"config_path": yaml_path})
    out = _stage_load_config(ctx)
    assert out.get("config") is not None
    assert out.get("config").model.architecture == "resnet18"


def test_run_requires_existing_config_path(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        run_from_yaml(missing, tmp_path / "out")
