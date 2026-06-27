"""Tests for EvalRunArtifacts — evaluation read contract for results.pt."""

from __future__ import annotations

from pathlib import Path

import torch

from uqlab.evaluation.metrics.artifacts import EvalRunArtifacts, uncertainty_vectors_from_results_pt


def test_eval_run_artifacts_from_results_pt(tmp_path: Path) -> None:
    n = 12
    path = tmp_path / "results.pt"
    torch.save(
        {
            "signal_table": {
                "expected_entropy": torch.linspace(0.2, 0.8, n),
                "mutual_info": torch.linspace(0.1, 0.4, n),
            },
            "predictions": torch.arange(n) % 10,
        },
        path,
    )

    art = EvalRunArtifacts.from_results_pt(path)
    assert art.results_path == path
    assert len(art.predictions) == n
    assert set(art.signal_table) >= {"expected_entropy", "mutual_info"}

    pred, alea, epi = art.disentangling_vectors(
        aleatoric_signal="expected_entropy",
        epistemic_signal="mutual_info",
    )
    assert pred.shape == (n,)
    assert alea.shape == (n,)
    assert epi.shape == (n,)


def test_uncertainty_vectors_wrapper_matches_artifacts(tmp_path: Path) -> None:
    n = 8
    path = tmp_path / "results.pt"
    torch.save(
        {
            "signal_table": {
                "inverse_coherence": torch.ones(n) * 0.3,
                "inverse_mass": torch.ones(n) * 0.7,
            },
            "predictions": torch.zeros(n, dtype=torch.long),
        },
        path,
    )

    a = EvalRunArtifacts.from_results_pt(path).disentangling_vectors(
        aleatoric_signal="inverse_coherence",
        epistemic_signal="inverse_mass",
    )
    b = uncertainty_vectors_from_results_pt(
        path,
        aleatoric_signal="inverse_coherence",
        epistemic_signal="inverse_mass",
    )
    assert a[0].tolist() == b[0].tolist()
    assert a[1].tolist() == b[1].tolist()
    assert a[2].tolist() == b[2].tolist()
