"""Tests for paper-style campaign aggregation and plot payload."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import torch

from uqlab.evaluation.reporting.campaign_score import (
    build_paper_sweep_series,
    paper_correlations,
    paper_point_from_results_dir,
    percentage_from_run_row,
)
from uqlab.evaluation.reporting.paper_benchmark_plot import (
    build_paper_benchmark_plot,
)
from uqlab.evaluation.reporting.sweep_line_plot import (
    SWEEP_KIND_DATASET_SIZE,
    SWEEP_KIND_LABEL_NOISE,
)


def _write_run(
    exp_root: Path,
    run_id: str,
    *,
    noise_percent: float | None = None,
    under_train: int | None = None,
    accuracy: float = 0.9,
    alea_mean: float = 0.3,
    epi_mean: float = 0.7,
) -> None:
    run_dir = exp_root / run_id
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True)

    torch.save(
        {
            "signal_table": {
                "inverse_coherence": torch.tensor([alea_mean, alea_mean + 0.01]),
                "inverse_mass": torch.tensor([epi_mean, epi_mean - 0.01]),
            },
            "predictions": torch.tensor([1, 0]),
            "eval_clean_labels": torch.tensor([1, 1]),
        },
        results_dir / "results.pt",
    )

    data: dict = {}
    if noise_percent is not None:
        data["aleatoric_noise_percentage"] = noise_percent
    if under_train is not None:
        data["under_train_per_class"] = under_train
        data["regular_train_per_class"] = 300

    cfg = {"data": data, "seed": 42}
    (run_dir / "config.yaml").write_text(
        "data:\n"
        + (f"  aleatoric_noise_percentage: {noise_percent}\n" if noise_percent is not None else "")
        + (f"  under_train_per_class: {under_train}\n" if under_train is not None else "")
        + (f"  regular_train_per_class: 300\n" if under_train is not None else "")
    )


def test_percentage_from_run_row_label_noise():
    row = {"noise_percent": 50.0}
    assert percentage_from_run_row(row, SWEEP_KIND_LABEL_NOISE) == pytest.approx(0.5)


def test_percentage_from_run_row_dataset_size():
    row = {"under_train_per_class": 150}
    assert percentage_from_run_row(row, SWEEP_KIND_DATASET_SIZE, regular_train_per_class=300) == pytest.approx(
        0.5
    )


def test_paper_point_from_results_dir(tmp_path):
    run_dir = tmp_path / "run_a"
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True)
    torch.save(
        {
            "signal_table": {
                "inverse_coherence": torch.tensor([0.2, 0.4]),
                "inverse_mass": torch.tensor([0.6, 0.8]),
            },
            "predictions": torch.tensor([1, 0]),
            "eval_clean_labels": torch.tensor([1, 0]),
        },
        results_dir / "results.pt",
    )

    point = paper_point_from_results_dir(
        results_dir,
        aleatoric_signal="inverse_coherence",
        epistemic_signal="inverse_mass",
    )
    assert point is not None
    assert point["score"] == pytest.approx(1.0)
    assert point["aleatorics"] == pytest.approx(0.3)
    assert point["epistemics"] == pytest.approx(0.7)


@patch("uqlab.evaluation.reporting.campaign_score.build_sweep_metrics_frame")
def test_build_paper_sweep_series(mock_frame, tmp_path):
    exp_root = tmp_path / "experiments"
    _write_run(exp_root, "r0", noise_percent=0.0, accuracy=0.95, alea_mean=0.1, epi_mean=0.9)
    _write_run(exp_root, "r1", noise_percent=50.0, accuracy=0.75, alea_mean=0.4, epi_mean=0.6)

    mock_frame.return_value = pd.DataFrame(
        [
            {"run_id": "r0", "noise_percent": 0.0},
            {"run_id": "r1", "noise_percent": 50.0},
        ]
    )

    series = build_paper_sweep_series(
        ["r0", "r1"],
        exp_root,
        sweep_kind=SWEEP_KIND_LABEL_NOISE,
        aleatoric_signal="inverse_coherence",
        epistemic_signal="inverse_mass",
    )

    assert series.experiment == "Label Noise"
    assert series.percentages == [0.0, 0.5]
    assert len(series.results.scores) == 2
    wide = series.wide_dataframe()
    assert list(wide.columns) == [
        "Experiment",
        "Percentage",
        "scores",
        "aleatorics",
        "epistemics",
        "run_id",
    ]


def test_paper_correlations_label_noise():
    from uqlab.vendor.disentanglement_error.util import ExperimentResults

    from uqlab.evaluation.reporting.campaign_score import PaperSweepSeries

    series = PaperSweepSeries(
        experiment="Label Noise",
        sweep_kind=SWEEP_KIND_LABEL_NOISE,
        percentages=[0.0, 0.5, 1.0],
        results=ExperimentResults(
            scores=[0.9, 0.7, 0.5],
            aleatorics=[0.1, 0.4, 0.8],
            epistemics=[0.5, 0.5, 0.5],
        ),
        run_ids=["a", "b", "c"],
    )
    corr = paper_correlations(series)
    assert corr["primary_metric"] == "aleatorics"
    assert corr["primary_correlation"] == pytest.approx(-1.0, abs=0.01)


@patch("uqlab.evaluation.reporting.campaign_score.build_sweep_metrics_frame")
def test_build_paper_benchmark_plot_payload(mock_frame, tmp_path):
    exp_root = tmp_path / "experiments"
    _write_run(exp_root, "r0", noise_percent=0.0)
    _write_run(exp_root, "r1", noise_percent=100.0)

    mock_frame.return_value = pd.DataFrame(
        [
            {"run_id": "r0", "noise_percent": 0.0},
            {"run_id": "r1", "noise_percent": 100.0},
        ]
    )

    payload = build_paper_benchmark_plot(
        ["r0", "r1"],
        exp_root,
        sweep_kind=SWEEP_KIND_LABEL_NOISE,
        aleatoric_signal="inverse_coherence",
        epistemic_signal="inverse_mass",
    )
    data = payload.to_dict()

    assert len(data["traces"]) == 3
    assert data["points"] == 2
    assert data["x_label"] == "Percentage (0–1)"
    assert {t["metric"] for t in data["traces"]} == {"scores", "aleatorics", "epistemics"}


def test_persist_campaign_paper_plot_flat_campaign(tmp_path):
    """Flat campaign dir (validation layout) → PNG + CSV at campaign end."""
    campaign = tmp_path / "label_noise_sweep"

    def _flat(name: str, noise_pct: float) -> None:
        run_dir = campaign / name
        run_dir.mkdir(parents=True)
        torch.save(
            {
                "signal_table": {
                    "expected_entropy": torch.tensor([0.3, 0.4]),
                    "mutual_info": torch.tensor([0.7, 0.6]),
                },
                "predictions": torch.tensor([1, 0]),
                "eval_clean_labels": torch.tensor([1, 1]),
            },
            run_dir / "results.pt",
        )
        import json

        (run_dir / "summary.json").write_text(
            json.dumps({"config": {"data": {"aleatoric_noise_percentage": noise_pct}}})
        )

    _flat("arch_noise0", 0.0)
    _flat("arch_noise50", 50.0)

    pytest.importorskip("matplotlib")
    from uqlab.evaluation.reporting.paper_benchmark_plot import persist_campaign_paper_plot

    paths = persist_campaign_paper_plot(campaign, sweep_kind=SWEEP_KIND_LABEL_NOISE)
    assert paths["png"].is_file()
    assert paths["csv"].is_file()
    assert paths["png"].name == "label_noise_three_line.png"


@patch("uqlab.evaluation.reporting.campaign_score.build_sweep_metrics_frame")
def test_paper_dataframe_from_campaign_dir_wide_for_plot(mock_frame, tmp_path):
    """Wide numeric columns so the paper one-liner groupby().mean().plot() works."""
    campaign = tmp_path / "label_noise_sweep"

    def _flat(name: str, noise_pct: float) -> None:
        run_dir = campaign / name
        run_dir.mkdir(parents=True)
        torch.save(
            {
                "signal_table": {
                    "expected_entropy": torch.tensor([0.3, 0.4]),
                    "mutual_info": torch.tensor([0.7, 0.6]),
                },
                "predictions": torch.tensor([1, 0]),
                "eval_clean_labels": torch.tensor([1, 1]),
            },
            run_dir / "results.pt",
        )
        import json

        (run_dir / "summary.json").write_text(
            json.dumps({"config": {"data": {"aleatoric_noise_percentage": noise_pct}}})
        )

    _flat("arch_noise0", 0.0)
    _flat("arch_noise50", 50.0)

    from uqlab.evaluation.reporting.paper_benchmark_plot import paper_dataframe_from_campaign_dir

    df = paper_dataframe_from_campaign_dir(campaign, sweep_kind=SWEEP_KIND_LABEL_NOISE)
    assert list(df.columns) == [
        "Experiment",
        "Percentage",
        "scores",
        "aleatorics",
        "epistemics",
        "Run_Index",
    ]
    plot_df = df.drop("Run_Index", axis=1).groupby(["Experiment", "Percentage"]).mean()
    assert {"scores", "aleatorics", "epistemics"}.issubset(plot_df.columns)
