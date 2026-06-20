"""Tests for run artifact loading and metrics row building."""

from __future__ import annotations

import json

from uqlab.run_artifacts import RunArtifacts, metrics_row_from_run


def test_auroc_by_signal_tolerates_null_auroc_fields():
    artifacts = RunArtifacts(
        run_dir=__import__("pathlib").Path("/tmp"),
        summary_path=None,
        per_sample_path=None,
        results_pt_path=None,
        one_vs_rest_auroc=[
            {
                "signal": "inverse_coherence",
                "aleatoric_like_auroc": None,
                "epistemic_like_auroc": None,
            }
        ],
        source="summary.json",
    )
    scores = artifacts.auroc_by_signal()
    assert scores["inverse_coherence"] == {"aleatoric": 0.0, "epistemic": 0.0}


def test_metrics_row_from_run_with_null_auroc_summary(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    summary = {
        "one_vs_rest_auroc": [
            {
                "signal": "inverse_mass",
                "aleatoric_like_auroc": None,
                "epistemic_like_auroc": 0.82,
            }
        ]
    }
    (results_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

    row = metrics_row_from_run(results_dir)
    assert row["inverse_mass_aleatoric_auroc"] == 0.0
    assert row["inverse_mass_epistemic_auroc"] == 0.82
