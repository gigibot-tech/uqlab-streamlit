"""Integration tests for campaign PDF report (timeline + sweep matplotlib plot).

These catch regressions like:
- list values in shared config (unhashable set elements)
- sweep traces with mismatched x/y (matplotlib ValueError)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import torch
import yaml

from uqlab.evaluation.classification.pipeline.campaign_config_timeline import (
    build_campaign_timeline,
)
from uqlab.evaluation.classification.pipeline.campaign_report import (
    _sweep_plot_figure,
    build_campaign_report_pdf,
)
from uqlab.evaluation.classification.pipeline.sweep_line_plot import (
    build_sweep_line_plot,
    resolve_sweep_trace_xy,
)


def _write_label_noise_run(
    exp_dir: Path,
    run_id: str,
    noise: float,
    *,
    under_classes: list[int] | None = None,
    accuracy: float = 0.85,
) -> None:
    base = exp_dir / run_id
    results = base / "results"
    results.mkdir(parents=True)
    cfg: dict[str, Any] = {
        "seed": 42,
        "data": {
            "dataset_name": "cifar10",
            "aleatoric_noise_percentage": noise,
            "under_train_per_class": 300,
        },
        "model": {"architecture": "resnet18_mcdropout", "dropout": 0.0},
        "training": {"learning_rate": 0.001, "epochs": 5},
    }
    if under_classes is not None:
        cfg["data"]["under_supported_classes"] = under_classes
    (base / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    n = 24
    labels = torch.zeros(n)
    torch.save(
        {
            "signal_table": {
                "inverse_coherence": torch.linspace(0.15, 0.55, n),
                "msp_uncertainty": torch.linspace(0.1, 0.45, n),
            },
            "eval_group_labels": torch.cat(
                [torch.zeros(8), torch.ones(8), torch.full((8,), 2)]
            ),
            "predictions": labels,
            "eval_clean_labels": labels,
        },
        results / "results.pt",
    )
    (results / "summary.json").write_text(
        json.dumps({"accuracy": accuracy - noise / 500, "config": cfg}),
        encoding="utf-8",
    )


def assert_sweep_traces_matplotlib_safe(traces: list[dict[str, Any]]) -> None:
    """Every trace must define x aligned with y; matplotlib path must not get empty x + data y."""
    shared_x = next((t.get("x") for t in traces if t.get("x")), None)
    assert shared_x, "expected at least one trace with non-empty x"

    for trace in traces:
        name = trace.get("name", "?")
        x = trace.get("x") or shared_x
        y = trace.get("y") or []
        assert len(x) == len(y), f"{name}: raw x/y length {len(x)} vs {len(y)}"

        xs, ys = resolve_sweep_trace_xy(traces, trace)
        non_null_y = [
            v
            for v in y
            if v is not None and not (isinstance(v, float) and v != v)
        ]
        if non_null_y:
            assert xs, f"{name}: matplotlib would plot {len(non_null_y)} y with empty x"
            assert len(xs) == len(ys), (
                f"{name}: resolved x/y length {len(xs)} vs {len(ys)}"
            )


def test_sweep_traces_xy_aligned_for_five_runs(tmp_path):
    """Reproduces the (0,) vs (5,) failure mode when Accuracy trace omitted x."""
    exp_dir = tmp_path / "experiments"
    noises = (0, 10, 25, 50, 75)
    run_ids = []
    for noise in noises:
        run_id = f"run-{noise}"
        run_ids.append(run_id)
        _write_label_noise_run(exp_dir, run_id, float(noise))

    payload = build_sweep_line_plot(run_ids, exp_dir, signal="inverse_coherence")
    traces = payload.to_dict()["traces"]
    assert_sweep_traces_matplotlib_safe(traces)

    acc = next(t for t in traces if t["name"] == "Accuracy")
    primary = next(t for t in traces if t.get("yaxis") == "left")
    assert acc["x"] == primary["x"]
    assert len(acc["x"]) == 5


def test_sweep_plot_figure_renders_payload(tmp_path):
    exp_dir = tmp_path / "experiments"
    for noise in (0, 50):
        _write_label_noise_run(exp_dir, f"run-{noise}", float(noise))

    payload = build_sweep_line_plot(
        ["run-0", "run-50"], exp_dir, signal="inverse_coherence"
    ).to_dict()
    assert_sweep_traces_matplotlib_safe(payload["traces"])

    fig = _sweep_plot_figure(payload)
    assert fig.axes
    plt.close(fig)


def test_build_campaign_report_pdf_end_to_end(tmp_path):
    """Full pipeline: disk artifacts → timeline → sweep plot → PDF bytes."""
    exp_dir = tmp_path / "experiments"
    run_ids = []
    for noise in (0, 25, 50):
        rid = f"run-{noise}"
        run_ids.append(rid)
        _write_label_noise_run(exp_dir, rid, float(noise))

    experiments = [
        {"id": rid, "status": "completed", "name": rid} for rid in run_ids
    ]

    pdf_bytes, timeline = build_campaign_report_pdf(
        experiments,
        exp_dir,
        sweep_kind="label_noise",
        signal="inverse_coherence",
    )

    assert timeline.n_runs == 3
    assert timeline.steps[1].changes_from_prev
    assert len(pdf_bytes) > 2000
    assert pdf_bytes[:4] == b"%PDF"


def test_timeline_shared_config_with_list_values_on_disk(tmp_path):
    """Regression: list config values must not blow up _shared_config (set of lists)."""
    exp_dir = tmp_path / "experiments"
    classes = [3, 7]
    for noise in (0, 50):
        _write_label_noise_run(
            exp_dir, f"run-{noise}", float(noise), under_classes=classes
        )

    experiments = [
        {"id": "run-0", "status": "completed", "name": "run-0"},
        {"id": "run-50", "status": "completed", "name": "run-50"},
    ]
    timeline = build_campaign_timeline(
        experiments, exp_dir, sweep_kind="label_noise"
    )
    assert "Under-supported classes" in timeline.shared_config
    assert timeline.shared_config["Under-supported classes"] == "{3, 7}"
