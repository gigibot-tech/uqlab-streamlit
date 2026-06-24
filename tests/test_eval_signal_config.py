"""Tests for EvalSignalConfig factories."""

from __future__ import annotations

from pathlib import Path

from uqlab.shared.config.classification import (
    DataConfig,
    EvaluationConfig,
    ExperimentConfig,
    ModelConfig,
    PathConfig,
    TrainingConfig,
)
from uqlab.evaluation.pipeline.eval_signal_config import EvalSignalConfig
from uqlab.evaluation.pipeline.experiment_setup import extract_run_config


def test_from_run_config_maps_eval_fields():
    view = extract_run_config(
        ExperimentConfig(
            data=DataConfig(aleatoric_noise_percentage=25.0),
            model=ModelConfig(dropout=0.3),
            training=TrainingConfig(train_batch_size=128),
            evaluation=EvaluationConfig(mc_passes=5, top_k=7, attribution_method="dualxda"),
            paths=PathConfig(),
        )
    )
    cfg = EvalSignalConfig.from_run_config(
        view,
        results_dir=Path("/tmp/results"),
        run_cache_dir=Path("/tmp/cache"),
    )

    assert cfg.train_batch_size == 128
    assert cfg.mc_passes == 5
    assert cfg.top_k == 7
    assert cfg.dropout == 0.3
    assert cfg.attribution_method == "dualxda"
    assert cfg.results_dir == Path("/tmp/results")
    assert cfg.run_cache_dir == Path("/tmp/cache")
    assert cfg.resolved_enabled_signals()  # pruned but non-empty


def test_from_experiment_config_matches_run_config_factory():
    experiment = ExperimentConfig(
        training=TrainingConfig(train_batch_size=64),
        evaluation=EvaluationConfig(mc_passes=10, top_k=3),
        paths=PathConfig(),
    )
    results_dir = Path("/out/run")
    run_cache_dir = Path("/out/run/cache")

    from_view = EvalSignalConfig.from_run_config(
        extract_run_config(experiment),
        results_dir=results_dir,
        run_cache_dir=run_cache_dir,
    )
    from_experiment = EvalSignalConfig.from_experiment_config(
        experiment,
        results_dir=results_dir,
        run_cache_dir=run_cache_dir,
    )

    assert from_experiment == from_view
