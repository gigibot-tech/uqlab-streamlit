"""Tests for campaign paper score aggregation (API bridge)."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from uqlab_orchestrator.campaign_paper_score import (
    aggregate_paper_point_from_results_dir,
    sweep_kind_for_profile,
)
from uqlab.evaluation.pipeline.sweep_line_plot import (
    SWEEP_KIND_DATASET_SIZE,
    SWEEP_KIND_LABEL_NOISE,
)


def _write_minimal_results(results_dir: Path) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "signal_table": {
                "expected_entropy": torch.tensor([0.2, 0.4, 0.6]),
                "mutual_info": torch.tensor([0.7, 0.5, 0.3]),
                "inverse_coherence": torch.tensor([0.2, 0.4, 0.6]),
                "inverse_mass": torch.tensor([0.7, 0.5, 0.3]),
            },
            "predictions": torch.tensor([1, 0, 1]),
            "eval_clean_labels": torch.tensor([1, 0, 1]),
        },
        results_dir / "results.pt",
    )


def test_aggregate_paper_point_from_results_dir(tmp_path):
    results_dir = tmp_path / "results"
    _write_minimal_results(results_dir)

    point = aggregate_paper_point_from_results_dir(results_dir)

    assert point is not None
    assert point["scores"] == pytest.approx(1.0)
    assert point["aleatorics"] == pytest.approx(0.4, abs=0.01)
    assert point["epistemics"] == pytest.approx(0.5, abs=0.01)


def test_aggregate_paper_point_missing_file(tmp_path):
    assert aggregate_paper_point_from_results_dir(tmp_path / "missing") is None


def test_sweep_kind_for_profile():
    assert sweep_kind_for_profile("noise") == SWEEP_KIND_LABEL_NOISE
    assert sweep_kind_for_profile("under_train") == SWEEP_KIND_DATASET_SIZE

    with pytest.raises(ValueError):
        sweep_kind_for_profile("unknown")
