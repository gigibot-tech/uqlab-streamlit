"""Tests for four-region Aspect 7 validation sweeps and correlation reporting."""

from __future__ import annotations

import copy

import pytest
import torch
import torch.nn as nn

from uqlab.data.class_regions import DEFAULT_FOUR_REGION_PRESET
from uqlab.evaluation.four_region_validation import (
    NOISE_SWEEP_PCTS,
    SPARSITY_SWEEP_PCTS,
    build_correlation_report,
    mock_sweep_metric_rows,
    noise_sweep_regions,
    sparsity_sweep_regions,
)
from uqlab.evaluation.signals.graddot import compute_graddot_structure_signals
from uqlab.evaluation.signals.primitives import namespaced_attribution_store
from uqlab.evaluation.signals.registry import build_signal_table_from_store


class _TinyTrainDataset:
    def __init__(self) -> None:
        self.features = torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        self.targets = torch.tensor([0, 1, 0])


def test_noise_sweep_presets_cover_axis():
    specs = noise_sweep_regions()
    assert [pct for pct, _ in specs] == list(NOISE_SWEEP_PCTS)
    for pct, regions in specs:
        assert regions["noisy"]["label_flip_pct"] == float(pct)
        assert regions["sparse"]["train_fraction"] == pytest.approx(0.10)


def test_sparsity_sweep_presets_cover_axis():
    specs = sparsity_sweep_regions()
    assert [pct for pct, _ in specs] == list(SPARSITY_SWEEP_PCTS)
    for pct, regions in specs:
        assert regions["sparse"]["train_fraction"] == pytest.approx(pct / 100.0)


def test_mock_correlation_report_monotonic_and_orthogonal():
    noise_rows, sparsity_rows = mock_sweep_metric_rows()
    report = build_correlation_report(noise_rows, sparsity_rows)
    assert report.monotonic_passed
    assert report.orthogonal_passed
    assert report.to_dict()["passed"] is True


def test_correlation_report_flags_bad_orthogonal_pattern():
    noise_rows, sparsity_rows = mock_sweep_metric_rows()
    bad_noise = copy.deepcopy(noise_rows)
    for row in bad_noise:
        row["inverse_mass_graddot"] = 0.1 + 0.01 * row["noise_pct"]
    report = build_correlation_report(bad_noise, sparsity_rows)
    assert not report.orthogonal_passed


def test_graddot_metrics_from_primitives():
    n = 4
    coherence = torch.linspace(0.2, 0.8, n)
    store = namespaced_attribution_store(
        "graddot",
        coherence,
        torch.ones(n) * 2.0,
        torch.ones(n) * 0.25,
    )
    table = build_signal_table_from_store(
        store,
        enabled={
            "inverse_coherence_graddot",
            "inverse_mass_graddot",
            "inverse_dominance_graddot",
        },
    )
    assert torch.allclose(table["inverse_coherence_graddot"], 1.0 - coherence)
    assert torch.allclose(table["inverse_mass_graddot"], 1.0 / (torch.ones(n) * 2.0 + 1e-8))
    assert torch.allclose(table["inverse_dominance_graddot"], torch.full((n,), 0.75))


def test_graddot_pairwise_scores_tiny_model(tmp_path):
    model = nn.Sequential(nn.Linear(2, 2), nn.ReLU(), nn.Linear(2, 2))
    train_ds = _TinyTrainDataset()
    eval_x = torch.tensor([[0.5, 0.5], [1.0, 0.0]])
    mean_pred = torch.softmax(torch.tensor([[0.2, 0.8], [0.9, 0.1]]), dim=1)
    raw = compute_graddot_structure_signals(
        model,
        train_ds,
        eval_x,
        mean_pred,
        device=torch.device("cpu"),
        top_k=2,
        run_cache_dir=tmp_path,
    )
    assert raw["coherence"].shape == (2,)
    assert raw["mass"].shape == (2,)
    assert raw["dominance"].shape == (2,)
    assert raw["mass"][0] >= 0
