"""Tests for pairwise region signal contrasts."""

from __future__ import annotations

import pandas as pd
import pytest

from uqlab.shared.notebook_utils.attribution_distribution_summary import (
    DEFAULT_FOUR_REGION_PAIRWISE,
    pairwise_signal_contrasts,
    pairwise_takeaway_line,
)


def _synthetic_df() -> pd.DataFrame:
    rows = []
    for group, base in (
        ("clean", 0.2),
        ("aleatoric_like", 0.8),
        ("epistemic_like", 0.5),
        ("ood_like", 0.1),
    ):
        for i in range(4):
            rows.append({"group": group, "sig_a": base + i * 0.01, "sig_b": 1.0 - base})
    return pd.DataFrame(rows)


def test_pairwise_mean_diff_signs() -> None:
    df = _synthetic_df()
    mean_diff, auroc = pairwise_signal_contrasts(df, signal_cols=["sig_a", "sig_b"])

    assert list(mean_diff.index) == [p[0] for p in DEFAULT_FOUR_REGION_PAIRWISE]
    # clean (0.2) - noisy (0.8) < 0
    assert mean_diff.loc["clean_minus_noisy", "sig_a"] == pytest.approx(-0.6, abs=0.05)
    # sparse (0.5) - clean (0.2) > 0
    assert mean_diff.loc["sparse_minus_clean", "sig_a"] == pytest.approx(0.3, abs=0.05)


def test_pairwise_auroc_numeric_when_both_groups_present() -> None:
    df = _synthetic_df()
    _, auroc = pairwise_signal_contrasts(df, signal_cols=["sig_a"])

    assert auroc.loc["clean_minus_noisy", "sig_a"] is not None
    assert 0.0 <= float(auroc.loc["clean_minus_noisy", "sig_a"]) <= 1.0
    # higher scores in aleatoric_like → AUROC < 0.5 when clean is positive
    assert float(auroc.loc["clean_minus_noisy", "sig_a"]) < 0.5


def test_pairwise_skips_empty_group() -> None:
    df = _synthetic_df()
    df = df[df["group"] != "ood_like"]
    mean_diff, auroc = pairwise_signal_contrasts(
        df,
        signal_cols=["sig_a"],
        pairs=[("sparse_minus_ood", "epistemic_like", "ood_like")],
    )
    assert pd.isna(mean_diff.loc["sparse_minus_ood", "sig_a"])
    assert pd.isna(auroc.loc["sparse_minus_ood", "sig_a"])
    assert "skip_reason" in auroc.columns
    assert pd.notna(auroc.loc["sparse_minus_ood", "skip_reason"])


def test_pairwise_takeaway_line() -> None:
    df = _synthetic_df()
    mean_diff, _ = pairwise_signal_contrasts(df, signal_cols=["sig_a"])
    line = pairwise_takeaway_line(mean_diff, signal_short="sig_a")
    assert line is not None
    assert "Largest" in line
