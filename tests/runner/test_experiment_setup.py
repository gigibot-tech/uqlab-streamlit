"""Tests for experiment setup / config extraction."""

from __future__ import annotations

from uqlab.shared.config.classification import ExperimentConfig
from uqlab.runner.phases.config_view import (
    extract_run_config,
    require_complete_config,
)
from uqlab.shared.config.classification import (
    DataConfig,
    EvaluationConfig,
    ModelConfig,
    PathConfig,
    TrainingConfig,
)


def _sample_config(**data_overrides) -> ExperimentConfig:
    data = DataConfig(
        dataset_name="cifar10",
        noise_type="clean_label",
        under_supported_classes=[3, 7],
        under_train_per_class=300,
        regular_train_per_class=300,
        eval_per_group=100,
        aleatoric_noise_percentage=25.0,
    )
    for key, val in data_overrides.items():
        setattr(data, key, val)
    return ExperimentConfig(
        data=data,
        model=ModelConfig(
            architecture="resnet18_mcdropout",
            training_mode="end_to_end",
            dinov2_model="small",
            hidden_dim=256,
            dropout=0.0,
        ),
        training=TrainingConfig(
            epochs=2,
            learning_rate=0.001,
            weight_decay=0.0001,
            train_batch_size=256,
            feature_batch_size=64,
        ),
        evaluation=EvaluationConfig(mc_passes=10, top_k=10),
        paths=PathConfig(
            data_root="./data/cifar10",
            cifar10n_root="./data/cifar10",
            feature_cache_dir="./cache",
            results_base_dir="./results",
        ),
    )


def test_extract_run_config():
    view = extract_run_config(_sample_config())
    assert view.dataset_name == "cifar10"
    assert view.mc_passes == 10
    assert view.aleatoric_expected is True


def test_require_complete_config_rejects_empty():
    config = ExperimentConfig()
    config.data = None
    try:
        require_complete_config(config)
        assert False, "expected ValueError"
    except ValueError:
        pass
