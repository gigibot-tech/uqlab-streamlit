"""Tests for modular sweep 3-line plot builder."""

from __future__ import annotations

import pandas as pd
import pytest

from uqlab.evaluation.pipeline.sweep_line_plot import (
    SWEEP_KIND_DATASET_SIZE,
    SWEEP_KIND_LABEL_NOISE,
    build_sweep_line_plot,
    default_signal_for_sweep,
    infer_sweep_kind,
    list_plottable_signals,
    sweep_kind_from_group,
)


from uqlab.shared.config.signals import (
    PLOT_DEFAULT_ALEATORIC_SIGNAL,
    PLOT_DEFAULT_EPISTEMIC_SIGNAL,
)


def test_default_signal_label_noise():
    assert default_signal_for_sweep(SWEEP_KIND_LABEL_NOISE) == PLOT_DEFAULT_ALEATORIC_SIGNAL


def test_default_signal_dataset_size():
    assert default_signal_for_sweep(SWEEP_KIND_DATASET_SIZE) == PLOT_DEFAULT_EPISTEMIC_SIGNAL


def test_infer_sweep_kind_from_noise_column():
    df = pd.DataFrame({"noise_percent": [0, 25, 50]})
    assert infer_sweep_kind(df) == SWEEP_KIND_LABEL_NOISE


def test_infer_sweep_kind_prefers_under_train_from_run_names():
    """Fig 3 runs: fixed noise % but varying under-train — must not pick label noise."""
    df = pd.DataFrame(
        {
            "noise_percent": [0, 0, 0, 0, 0, 0],
            "under_train_per_class": [50, 100, 150, 200, 250, 300],
            "run_name": [
                "fast_epis_20260620_120000_under_50",
                "fast_epis_20260620_120000_under_100",
                "fast_epis_20260620_120000_under_150",
                "fast_epis_20260620_120000_under_200",
                "fast_epis_20260620_120000_under_250",
                "fast_epis_20260620_120000_under_300",
            ],
        }
    )
    assert infer_sweep_kind(df) == SWEEP_KIND_DATASET_SIZE


def test_sweep_kind_from_group_under_param():
    group = {
        "swept_param": "under",
        "experiments": [{"name": "fast_epis_20260620_120000_under_50"}],
    }
    assert sweep_kind_from_group(group) == SWEEP_KIND_DATASET_SIZE


def test_list_plottable_signals_primary_pool_only():
    alea_df = pd.DataFrame(
        columns=[
            "inverse_coherence_mean_aleatoric",
            "mutual_info_mean_epistemic",
        ]
    )
    assert list_plottable_signals(alea_df, SWEEP_KIND_LABEL_NOISE) == []

    alea_df = pd.DataFrame([{"inverse_coherence_mean_aleatoric": 0.5}])
    assert list_plottable_signals(alea_df, SWEEP_KIND_LABEL_NOISE) == [PLOT_DEFAULT_ALEATORIC_SIGNAL]

    epis_df = pd.DataFrame([{"mutual_info_mean_epistemic": 0.3}])
    assert list_plottable_signals(epis_df, SWEEP_KIND_DATASET_SIZE) == ["mutual_info"]
    assert list_plottable_signals(epis_df, SWEEP_KIND_LABEL_NOISE) == []


def test_list_plottable_signals_old_both_pools_not_required_for_noise():
    df = pd.DataFrame(
        [
            {
                "inverse_coherence_mean_aleatoric": 0.4,
                "inverse_coherence_mean_epistemic": 0.2,
            }
        ]
    )
    assert list_plottable_signals(df, SWEEP_KIND_LABEL_NOISE) == [PLOT_DEFAULT_ALEATORIC_SIGNAL]


def test_detect_facet_columns_learning_rate():
    from uqlab.evaluation.pipeline.sweep_line_plot import detect_facet_columns

    df = pd.DataFrame(
        {
            "noise_percent": [0, 25, 50, 0, 25, 50],
            "learning_rate": [0.001, 0.001, 0.001, 0.01, 0.01, 0.01],
        }
    )
    facets = detect_facet_columns(df, "noise_percent")
    assert "learning_rate" in facets
    assert facets["learning_rate"] == [0.001, 0.01]


def test_build_sweep_line_plot_from_synthetic_runs(tmp_path):
    experiments = tmp_path / "experiments"
    for noise in (0, 25, 50):
        run_id = f"run-{noise}"
        run_dir = experiments / run_id
        results = run_dir / "results"
        results.mkdir(parents=True)
        (run_dir / "config.yaml").write_text(
            f"""
data:
  aleatoric_noise_percentage: {noise}
  under_train_per_class: 300
model:
  architecture: resnet18
training:
  learning_rate: 0.001
  epochs: 12
""".strip(),
            encoding="utf-8",
        )
        import json
        import torch

        n = 30
        labels = torch.zeros(n)
        (results / "summary.json").write_text(
            json.dumps({"one_vs_rest_auroc": []}),
            encoding="utf-8",
        )
        torch.save(
            {
                "signal_table": {
                    "inverse_coherence": torch.linspace(0.1, 0.5, n),
                    "mutual_info": torch.linspace(0.2, 0.4, n),
                },
                "eval_group_labels": torch.cat(
                    [
                        torch.zeros(10),
                        torch.ones(10),
                        torch.full((10,), 2),
                    ]
                ),
                "predictions": labels,
                "eval_clean_labels": labels,
            },
            results / "results.pt",
        )

    payload = build_sweep_line_plot(
        ["run-0", "run-25", "run-50"],
        experiments,
        signal="inverse_coherence",
    )
    d = payload.to_dict()
    assert d["signal"] == PLOT_DEFAULT_ALEATORIC_SIGNAL
    assert d["x_col"] == "noise_percent"
    assert d["points"] == 3
    assert d["primary_pool"] == "aleatoric"
    assert d.get("plot_config")
    assert d["plot_config"]["signal"]["id"] == PLOT_DEFAULT_ALEATORIC_SIGNAL
    assert d["plot_config"]["x_axis"]["column"] == "noise_percent"
    left_traces = [t for t in d["traces"] if t.get("yaxis") == "left"]
    assert len(left_traces) >= 1
    assert left_traces[0]["dash"] == "solid"
    assert d["traces"][-1]["name"] == "Accuracy"
    assert d["traces"][-1]["x"] == d["traces"][0]["x"]


def test_build_sweep_line_plot_100pct_noise_no_epistemic_mirror(tmp_path):
    experiments = tmp_path / "experiments"
    for noise in (50, 100):
        run_id = f"run-{noise}"
        run_dir = experiments / run_id
        results = run_dir / "results"
        results.mkdir(parents=True)
        (run_dir / "config.yaml").write_text(
            f"""
data:
  aleatoric_noise_percentage: {noise}
  under_train_per_class: 300
model:
  architecture: resnet18
""".strip(),
            encoding="utf-8",
        )
        import json
        import torch

        n = 20
        labels = torch.zeros(n)
        (results / "summary.json").write_text("{}", encoding="utf-8")
        group_labels = torch.ones(n) if noise >= 100 else torch.cat(
            [torch.zeros(10), torch.ones(10), torch.full((10,), 2)]
        )
        torch.save(
            {
                "signal_table": {"inverse_coherence": torch.linspace(0.1, 0.5, len(group_labels))},
                "eval_group_labels": group_labels,
                "predictions": labels[: len(group_labels)],
                "eval_clean_labels": labels[: len(group_labels)],
            },
            results / "results.pt",
        )

    payload = build_sweep_line_plot(
        ["run-50", "run-100"],
        experiments,
        signal="inverse_coherence",
    )
    d = payload.to_dict()
    left_traces = [t for t in d["traces"] if t.get("yaxis") == "left"]
    solid = [t for t in left_traces if t.get("dash") == "solid"]
    assert len(solid) == 1
    assert solid[0]["dash"] == "solid"
    assert d["signal"] == PLOT_DEFAULT_ALEATORIC_SIGNAL
    # run-50 still has an epistemic eval pack, so a dashed mirror can appear in the sweep frame.
    assert d["has_mirror_line"] is True


def test_build_sweep_line_plot_facet_slice(tmp_path):
    experiments = tmp_path / "experiments"
    for noise, lr in ((0, 0.001), (50, 0.001), (0, 0.01), (50, 0.01)):
        run_id = f"run-{noise}-{lr}"
        run_dir = experiments / run_id
        results = run_dir / "results"
        results.mkdir(parents=True)
        (run_dir / "config.yaml").write_text(
            f"""
data:
  aleatoric_noise_percentage: {noise}
model:
  architecture: resnet18
training:
  learning_rate: {lr}
""".strip(),
            encoding="utf-8",
        )
        import json
        import torch

        n = 30
        labels = torch.zeros(n)
        (results / "summary.json").write_text("{}", encoding="utf-8")
        torch.save(
            {
                "signal_table": {"inverse_coherence": torch.linspace(0.1, 0.5, n)},
                "eval_group_labels": torch.cat(
                    [torch.zeros(10), torch.ones(10), torch.full((10,), 2)]
                ),
                "predictions": labels,
                "eval_clean_labels": labels,
            },
            results / "results.pt",
        )

    all_ids = ["run-0-0.001", "run-50-0.001", "run-0-0.01", "run-50-0.01"]
    sliced = build_sweep_line_plot(
        all_ids,
        experiments,
        signal="inverse_coherence",
        facet_filters={"learning_rate": 0.001},
    )
    assert sliced.to_dict()["points"] == 2
    assert sliced.facet_filters == {"learning_rate": 0.001}


def test_build_sweep_line_plot_raises_without_results(tmp_path):
    with pytest.raises(ValueError, match="No completed runs"):
        build_sweep_line_plot(["missing-id"], tmp_path / "empty")


def test_run_ids_for_experiments_skips_missing_artifacts(tmp_path, monkeypatch):
    from uqlab.ui_components.visualization.sweeps.sweep_line_plot_viz import (
        run_ids_for_experiments,
    )

    monkeypatch.setattr(
        "uqlab.runtime_paths.experiments_root",
        lambda: tmp_path,
    )

    good = tmp_path / "run-a"
    (good / "results").mkdir(parents=True)
    (good / "results" / "summary.json").write_text("{}", encoding="utf-8")

    tmp_path.joinpath("run-b", "results").mkdir(parents=True)

    exps = [
        {"id": "run-a", "status": "completed"},
        {"id": "run-b", "status": "completed"},
    ]
    assert run_ids_for_experiments(exps) == ["run-a"]
