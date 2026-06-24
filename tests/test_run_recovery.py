"""Tests for run recovery from zwischen artifacts."""

from __future__ import annotations

from pathlib import Path

import torch

from uqlab.evaluation.pipeline.run_recovery import (
    assess_run_recovery,
    finalize_run_from_zwischen,
    sync_run_from_disk,
)
from uqlab.run_artifacts import save_zwischen_result


def _write_minimal_zwischen(results_dir: Path, n: int = 30) -> None:
    labels = torch.tensor([0] * 10 + [1] * 10 + [2] * 10)
    save_zwischen_result(
        results_dir,
        "00_eval_setup",
        {
            "eval_group_labels": labels,
            "eval_clean_labels": labels.clone(),
            "eval_is_noisy": torch.zeros(n, dtype=torch.bool),
            "eval_noisy_labels": labels.clone(),
            "eval_dataset_index": torch.arange(n),
            "n_eval": n,
            "mc_passes": 10,
        },
    )
    save_zwischen_result(
        results_dir,
        "01_deterministic_forward",
        {
            "mean_prediction": torch.softmax(torch.randn(n, 10), dim=1),
        },
    )
    save_zwischen_result(
        results_dir,
        "05_signal_table",
        {
            "msp_uncertainty": torch.rand(n),
            "predictive_entropy": torch.rand(n),
            "inverse_coherence": torch.rand(n),
            "inverse_dominance": torch.rand(n),
            "inverse_mass": torch.rand(n),
            "inverse_logit_magnitude": torch.rand(n),
        },
    )


def test_assess_zwischen_finalize(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _write_minimal_zwischen(results_dir)
    report = assess_run_recovery(results_dir)
    assert report.tier == "zwischen_finalize"
    assert "00_eval_setup" in report.zwischen_stages
    assert "05_signal_table" in report.zwischen_stages


def test_assess_db_sync_when_summary_exists(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "summary.json").write_text('{"train_size": 1}')
    report = assess_run_recovery(results_dir)
    assert report.tier == "db_sync"
    assert report.has_summary is True


def test_finalize_from_zwischen_writes_artifacts(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp"
    results_dir = exp_dir / "results"
    results_dir.mkdir(parents=True)
    (exp_dir / "config.yaml").write_text(
        "data:\n  under_supported_classes: [3, 7]\n  eval_per_group: 10\n"
        "model:\n  dinov2_model: small\n  dropout: 0.0\n"
    )
    _write_minimal_zwischen(results_dir)

    summary = finalize_run_from_zwischen(results_dir, experiment_dir=exp_dir, seed=0, device="cpu")
    assert summary["recovered_from_zwischen"] is True
    assert (results_dir / "summary.json").is_file()
    assert (results_dir / "results.pt").is_file()
    assert (results_dir / "per_sample_signals.csv").is_file()


def test_sync_run_from_disk_results_pt(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    n = 12
    labels = torch.tensor([0] * 4 + [1] * 4 + [2] * 4)
    torch.save(
        {
            "signal_table": {"msp_uncertainty": torch.rand(n)},
            "eval_group_labels": labels,
            "auroc_rows": [("msp_uncertainty", 0.6, 0.7)],
        },
        results_dir / "results.pt",
    )
    data = sync_run_from_disk(results_dir)
    assert data["eval_sizes"]["clean"] == 4
    assert len(data["one_vs_rest_auroc"]) == 1
