"""Tests for full-vector attribution distribution signals."""

from __future__ import annotations

import pytest
import torch

from uqlab.evaluation.signals.attribution_distribution import (
    attribution_entropy_row,
    attribution_participation_row,
    attribution_signed_split_row,
    compute_attribution_distribution_signals,
)
from uqlab.evaluation.signals.primitives import (
    DUALXDA_ENTROPY,
    DUALXDA_PARTICIPATION,
    DUALXDA_SIGNED_SPLIT,
    DUALXDA_VARIANCE,
    FWD_DET_LOGITS,
    FWD_MEAN_PRED,
    MC_ENTROPY,
    MC_MEAN_PRED,
    MC_MUTUAL_INFO,
)
from uqlab.evaluation.signals.registry import build_signal_table_from_store


def test_concentrated_signed_vs_uniform_low_ordering() -> None:
    n = 128
    concentrated = torch.zeros(n)
    concentrated[0] = 5.0
    concentrated[1] = -4.5
    uniform_low = torch.full((n,), 0.01)

    assert attribution_signed_split_row(concentrated) > attribution_signed_split_row(uniform_low)
    assert attribution_entropy_row(uniform_low) > attribution_entropy_row(concentrated)
    assert attribution_participation_row(uniform_low) > attribution_participation_row(concentrated)


def test_batch_helper_shapes() -> None:
    attr = torch.tensor([[1.0, -1.0, 0.0], [0.5, 0.5, 0.5]])
    out = compute_attribution_distribution_signals(attr)
    assert out["entropy"].shape == (2,)
    assert out["participation"].shape == (2,)
    assert out["signed_split"].shape == (2,)
    assert out["variance"].shape == (2,)


def test_registry_metrics_from_distribution_primitives() -> None:
    store = {
        FWD_DET_LOGITS: torch.zeros(2, 10),
        FWD_MEAN_PRED: torch.tensor([[1.0, 0.0], [1.0, 0.0]]),
        MC_MEAN_PRED: torch.tensor([[1.0, 0.0], [1.0, 0.0]]),
        MC_ENTROPY: torch.zeros(2),
        MC_MUTUAL_INFO: torch.zeros(2),
        DUALXDA_ENTROPY: torch.tensor([0.8, 0.2]),
        DUALXDA_PARTICIPATION: torch.tensor([0.7, 0.3]),
        DUALXDA_SIGNED_SPLIT: torch.tensor([0.9, 0.1]),
        DUALXDA_VARIANCE: torch.tensor([2.0, 0.1]),
    }
    table = build_signal_table_from_store(
        store,
        enabled={
            "attribution_entropy_dualxda",
            "attribution_participation_dualxda",
            "attribution_signed_split_dualxda",
            "attribution_variance_dualxda",
        },
    )
    assert set(table) == {
        "attribution_entropy_dualxda",
        "attribution_participation_dualxda",
        "attribution_signed_split_dualxda",
        "attribution_variance_dualxda",
    }
    assert table["attribution_entropy_dualxda"][0].item() == pytest.approx(0.8)
