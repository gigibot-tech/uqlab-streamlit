"""Tests for campaign config timeline builder."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd

from uqlab.evaluation.classification.pipeline.campaign_config_timeline import (
    build_campaign_timeline,
    build_campaign_timeline_figure,
)


def test_build_campaign_timeline_noise_sweep(monkeypatch, tmp_path):
    exp_dir = tmp_path / "experiments"
    root = tmp_path

    run_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    run_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    def _write_run(run_id: str, noise: float) -> None:
        base = exp_dir / run_id
        (base / "results").mkdir(parents=True)
        cfg = {
            "seed": 42,
            "data": {
                "dataset_name": "cifar10",
                "aleatoric_noise_percentage": noise,
                "under_train_per_class": 300,
            },
            "model": {"architecture": "resnet18_mcdropout", "dropout": 0.0},
            "training": {"learning_rate": 0.001, "epochs": 5},
            "evaluation": {"mc_passes": 7},
        }
        import yaml

        with open(base / "config.yaml", "w") as f:
            yaml.safe_dump(cfg, f)
        with open(base / "results" / "summary.json", "w") as f:
            import json

            json.dump({"config": cfg, "accuracy": 0.9 - noise / 200}, f)

    _write_run(run_a, 0.0)
    _write_run(run_b, 50.0)

    df = pd.DataFrame(
        [
            {
                "run_id": run_a,
                "noise_percent": 0.0,
                "accuracy": 0.90,
                "msp_uncertainty_aleatoric_like_mean": 0.4,
            },
            {
                "run_id": run_b,
                "noise_percent": 50.0,
                "accuracy": 0.65,
                "msp_uncertainty_aleatoric_like_mean": 0.55,
            },
        ]
    )

    monkeypatch.setattr(
        "uqlab.evaluation.classification.pipeline.campaign_config_timeline.build_sweep_metrics_frame",
        lambda _ids, _dir: df,
    )
    monkeypatch.setattr(
        "uqlab.evaluation.classification.pipeline.campaign_config_timeline.run_ids_for_experiments",
        lambda exps, **kw: [str(e["id"]) for e in exps],
    )

    experiments = [
        {"id": run_a, "status": "completed", "name": "run_a"},
        {"id": run_b, "status": "completed", "name": "run_b"},
    ]

    timeline = build_campaign_timeline(
        experiments,
        exp_dir,
        project_root=root,
        sweep_kind="label_noise",
    )

    assert timeline.n_runs == 2
    assert timeline.steps[0].is_baseline
    assert not timeline.steps[0].changes_from_prev
    assert timeline.steps[1].changes_from_prev
    assert timeline.steps[1].changes_from_prev[0].key == "data.aleatoric_noise_percentage"
    assert "Architecture" in timeline.shared_config or "Dataset" in timeline.shared_config

    fig = build_campaign_timeline_figure(timeline)
    import matplotlib.pyplot as plt

    plt.close(fig)


def test_shared_config_with_list_values():
    from uqlab.evaluation.classification.pipeline.campaign_config_timeline import _shared_config

    flat_a = {
        "data.under_supported_classes": [3, 7],
        "data.dataset_name": "cifar10",
        "model.architecture": "resnet18_mcdropout",
    }
    flat_b = {
        "data.under_supported_classes": [3, 7],
        "data.dataset_name": "cifar10",
        "model.architecture": "resnet18_mcdropout",
    }
    shared = _shared_config([flat_a, flat_b])
    assert "Under-supported classes" in shared
    assert shared["Under-supported classes"] == "{3, 7}"
