"""Integration tests for campaign PDF report (timeline + sweep matplotlib plot)."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import torch
import yaml

from uqlab.evaluation.reporting.campaign_config_timeline import (
    _paginate_entries,
    build_campaign_timeline,
    config_timeline_entries,
)
from uqlab.evaluation.reporting.campaign_report import (
    CampaignExportBundle,
    CampaignReportSummary,
    _sweep_plot_figure,
    build_campaign_report_pdf,
    build_multi_campaign_report_pdf,
)
from uqlab.evaluation.reporting.campaign_sections import split_campaign_sections
from uqlab.evaluation.reporting.sweep_line_plot import (
    build_sweep_line_plot,
    resolve_sweep_trace_xy,
)


def _write_label_noise_run(
    exp_dir: Path,
    run_id: str,
    noise: float,
    *,
    name: str | None = None,
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


def _write_epistemic_run(
    exp_dir: Path,
    run_id: str,
    under_train: int,
    *,
    name: str,
) -> None:
    base = exp_dir / run_id
    results = base / "results"
    results.mkdir(parents=True)
    cfg: dict[str, Any] = {
        "seed": 42,
        "data": {
            "dataset_name": "cifar10",
            "aleatoric_noise_percentage": 0,
            "under_train_per_class": under_train,
            "under_supported_classes": [3, 7],
            "regular_train_per_class": 300,
        },
        "model": {"architecture": "resnet18_mcdropout", "dropout": 0.0},
        "training": {"learning_rate": 0.001, "epochs": 5},
    }
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
        json.dumps({"accuracy": 0.85, "config": cfg}),
        encoding="utf-8",
    )


def _pdf_page_count(pdf_bytes: bytes) -> int:
    return pdf_bytes.count(b"/Type /Page")


def assert_sweep_traces_matplotlib_safe(traces: list[dict[str, Any]]) -> None:
    shared_x = next((t.get("x") for t in traces if t.get("x")), None)
    assert shared_x, "expected at least one trace with non-empty x"
    for trace in traces:
        name = trace.get("name", "?")
        x = trace.get("x") or shared_x
        y = trace.get("y") or []
        assert len(x) == len(y), f"{name}: raw x/y length {len(x)} vs {len(y)}"
        xs, ys = resolve_sweep_trace_xy(traces, trace)
        non_null_y = [
            v for v in y if v is not None and not (isinstance(v, float) and v != v)
        ]
        if non_null_y:
            assert xs, f"{name}: matplotlib would plot {len(non_null_y)} y with empty x"
            assert len(xs) == len(ys)


def test_config_timeline_entries_are_config_only(tmp_path):
    exp_dir = tmp_path / "experiments"
    for noise in (0, 50):
        _write_label_noise_run(exp_dir, f"run-{noise}", float(noise))

    timeline = build_campaign_timeline(
        [
            {"id": "run-0", "status": "completed", "name": "run-0"},
            {"id": "run-50", "status": "completed", "name": "run-50"},
        ],
        exp_dir,
        sweep_kind="label_noise",
    )
    assert timeline.steps[0].metrics.get("accuracy") is not None
    text = "\n".join(line for line, _ in config_timeline_entries(timeline))
    assert "accuracy" not in text.lower()
    assert "msp uncertainty mean" not in text.lower()
    assert "Shared setup" in text
    assert "Δ vs previous sweep" in text


def test_paginate_many_steps_without_truncation_message(tmp_path):
    exp_dir = tmp_path / "experiments"
    noises = list(range(0, 120, 10))
    for noise in noises:
        _write_label_noise_run(exp_dir, f"run-{noise}", float(noise))

    timeline = build_campaign_timeline(
        [
            {"id": f"run-{n}", "status": "completed", "name": f"run-{n}"}
            for n in noises
        ],
        exp_dir,
        sweep_kind="label_noise",
    )
    assert timeline.n_runs == len(noises)
    pages = _paginate_entries(config_timeline_entries(timeline))
    assert len(pages) >= 2
    joined = "\n".join(t for page in pages for t, _ in page)
    assert "truncated" not in joined.lower()
    assert joined.count("Sweep ") >= len(noises)


def test_sweep_traces_xy_aligned_for_five_runs(tmp_path):
    exp_dir = tmp_path / "experiments"
    run_ids = []
    for noise in (0, 10, 25, 50, 75):
        run_id = f"run-{noise}"
        run_ids.append(run_id)
        _write_label_noise_run(exp_dir, run_id, float(noise))

    payload = build_sweep_line_plot(run_ids, exp_dir, signal="inverse_coherence")
    traces = payload.to_dict()["traces"]
    assert_sweep_traces_matplotlib_safe(traces)


def test_build_campaign_report_pdf_end_to_end(tmp_path):
    exp_dir = tmp_path / "experiments"
    run_ids = []
    for noise in (0, 25, 50):
        rid = f"run-{noise}"
        run_ids.append(rid)
        _write_label_noise_run(exp_dir, rid, float(noise))

    experiments = [{"id": rid, "status": "completed", "name": rid} for rid in run_ids]
    pdf_bytes, summary = build_campaign_report_pdf(
        experiments,
        exp_dir,
        sweep_kind="label_noise",
        signal="inverse_coherence",
        include_all_signals=True,
    )

    assert isinstance(summary, CampaignReportSummary)
    assert summary.n_runs == 3
    assert len(summary.sections) == 1
    assert len(pdf_bytes) > 2000
    assert pdf_bytes[:4] == b"%PDF"
    assert _pdf_page_count(pdf_bytes) <= 8


def test_build_campaign_report_by_metric_layout(tmp_path):
    exp_dir = tmp_path / "experiments"
    for under in (50, 100):
        _write_epistemic_run(
            exp_dir, f"epis-{under}", under, name=f"fast_epis_under_{under}"
        )
    for noise in (0, 50):
        _write_label_noise_run(
            exp_dir, f"alea-{noise}", float(noise), name=f"fast_alea_noise_{noise}"
        )
    experiments = [
        {"id": "epis-50", "status": "completed", "name": "fast_epis_under_50"},
        {"id": "epis-100", "status": "completed", "name": "fast_epis_under_100"},
        {"id": "alea-0", "status": "completed", "name": "fast_alea_noise_0"},
        {"id": "alea-50", "status": "completed", "name": "fast_alea_noise_50"},
    ]
    section_pdf, section_summary = build_campaign_report_pdf(
        experiments, exp_dir, layout="by_section"
    )
    metric_pdf, metric_summary = build_campaign_report_pdf(
        experiments, exp_dir, layout="by_metric"
    )
    assert section_summary.layout == "by_section"
    assert metric_summary.layout == "by_metric"
    assert len(metric_summary.sections) == 2
    assert _pdf_page_count(metric_pdf) < _pdf_page_count(section_pdf)


def test_build_campaign_report_includes_all_signals(tmp_path):
    exp_dir = tmp_path / "experiments"
    for noise in (0, 50):
        _write_label_noise_run(exp_dir, f"run-{noise}", float(noise))

    experiments = [
        {"id": "run-0", "status": "completed", "name": "run-0"},
        {"id": "run-50", "status": "completed", "name": "run-50"},
    ]
    full_pdf, _ = build_campaign_report_pdf(
        experiments, exp_dir, include_all_signals=True
    )
    single_pdf, _ = build_campaign_report_pdf(
        experiments, exp_dir, include_all_signals=False
    )
    assert _pdf_page_count(full_pdf) > _pdf_page_count(single_pdf)


def test_split_campaign_sections_dual_sweep(tmp_path):
    exp_dir = tmp_path / "experiments"
    for under in (50, 100):
        rid = f"epis-{under}"
        _write_epistemic_run(
            exp_dir, rid, under, name=f"fast_epis_20260620_under_{under}"
        )
    for noise in (0, 50):
        rid = f"alea-{noise}"
        _write_label_noise_run(
            exp_dir,
            rid,
            float(noise),
            name=f"fast_alea_20260620_noise_{noise}",
        )

    experiments = [
        {"id": "epis-50", "status": "completed", "name": "fast_epis_20260620_under_50"},
        {"id": "epis-100", "status": "completed", "name": "fast_epis_20260620_under_100"},
        {"id": "alea-0", "status": "completed", "name": "fast_alea_20260620_noise_0"},
        {"id": "alea-50", "status": "completed", "name": "fast_alea_20260620_noise_50"},
    ]
    sections = split_campaign_sections(experiments, experiments_dir=exp_dir)
    assert len(sections) == 2
    assert "Epistemic" in sections[0].label
    assert "Aleatoric" in sections[1].label

    pdf_bytes, summary = build_campaign_report_pdf(experiments, exp_dir)
    assert len(summary.sections) == 2
    assert summary.n_runs == 4
    assert _pdf_page_count(pdf_bytes) >= 4


def test_multi_campaign_report_pdf(tmp_path):
    exp_dir = tmp_path / "experiments"
    for noise in (0, 25):
        _write_label_noise_run(exp_dir, f"a-{noise}", float(noise), name=f"grp_a_{noise}")
    for noise in (0, 50):
        _write_label_noise_run(exp_dir, f"b-{noise}", float(noise), name=f"grp_b_{noise}")

    bundles = [
        CampaignExportBundle(
            label="Campaign A",
            experiments=(
                {"id": "a-0", "status": "completed", "name": "grp_a_0"},
                {"id": "a-25", "status": "completed", "name": "grp_a_25"},
            ),
        ),
        CampaignExportBundle(
            label="Campaign B",
            experiments=(
                {"id": "b-0", "status": "completed", "name": "grp_b_0"},
                {"id": "b-50", "status": "completed", "name": "grp_b_50"},
            ),
        ),
    ]
    pdf_bytes, summary = build_multi_campaign_report_pdf(bundles, exp_dir)
    assert len(summary.group_labels) == 2
    assert summary.n_runs == 4
    assert _pdf_page_count(pdf_bytes) >= 4


def test_timeline_shared_config_with_list_values_on_disk(tmp_path):
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
    timeline = build_campaign_timeline(experiments, exp_dir, sweep_kind="label_noise")
    assert "Under-supported classes" in timeline.shared_config
    assert timeline.shared_config["Under-supported classes"] == "{3, 7}"
