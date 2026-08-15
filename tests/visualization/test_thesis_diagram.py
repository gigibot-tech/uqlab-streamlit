"""Tests for thesis schematic builder (no dataset download)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from uqlab.shared.config.classification import (
    DataConfig,
    EvaluationConfig,
    ExperimentConfig,
    ModelConfig,
    PathConfig,
    TrainingConfig,
)
from uqlab.evaluation.reporting.thesis_diagram import (
    build_thesis_figure,
    load_thesis_diagram_inputs,
    save_thesis_figure,
)


def _sample_config() -> ExperimentConfig:
    return ExperimentConfig(
        seed=42,
        data=DataConfig(
            dataset_name="cifar10",
            aleatoric_noise_percentage=25.0,
            under_supported_classes=[3, 5],
            under_train_per_class=50,
            regular_train_per_class=500,
            eval_per_group=100,
        ),
        model=ModelConfig(dropout=0.2, architecture="dinov2_mlp"),
        training=TrainingConfig(),
        evaluation=EvaluationConfig(mc_passes=10, top_k=5),
        paths=PathConfig(),
    )


def test_load_symbolic_inputs():
    inputs = load_thesis_diagram_inputs(
        _sample_config(),
        Path("."),
        seed=42,
        empirical=False,
    )
    assert inputs.empirical is False
    assert inputs.split_counts is not None
    assert inputs.split_counts["train"] > 0
    assert inputs.pool_expectations.aleatoric_pool_expected is True
    assert inputs.pool_expectations.epistemic_pool_expected is True
    assert inputs.enabled_signals


def test_build_and_save_symbolic_figure(tmp_path):
    inputs = load_thesis_diagram_inputs(
        _sample_config(),
        Path("."),
        seed=42,
        empirical=False,
    )
    fig = build_thesis_figure(inputs)
    out_pdf = save_thesis_figure(fig, tmp_path / "schematic.pdf")
    out_png = save_thesis_figure(fig, tmp_path / "schematic.png", dpi=72)
    assert out_pdf.is_file() and out_pdf.stat().st_size > 500
    assert out_png.is_file() and out_png.stat().st_size > 500

    import matplotlib.pyplot as plt

    plt.close(fig)
