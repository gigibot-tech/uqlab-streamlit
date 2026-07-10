"""Tests for Step~6 synthesis logging profile."""

from __future__ import annotations

import pandas as pd
import pytest

from uqlab_core.evaluation.reporting.attribution_distribution_summary import (
    four_region_pairwise_auroc_report,
    print_four_region_pairwise_auroc,
)
from uqlab_core.evaluation.reporting.four_region_synthesis_profile import (
    print_synthesis_backend_coh,
    print_synthesis_pool_auroc,
    print_synthesis_task2,
    synthesis_pairwise_pairs,
    synthesis_plot_metrics,
)


def _df() -> pd.DataFrame:
    rows = []
    for group, base in (
        ("aleatoric_like", 0.8),
        ("epistemic_like", 0.5),
        ("clean", 0.6),
        ("ood_like", 0.4),
    ):
        for _ in range(20):
            rows.append(
                {
                    "group": group,
                    "clean_label": 0,
                    "attribution_entropy_dualxda": base,
                    "attribution_participation_dualxda": base - 0.1,
                    "coherence_dualxda": 0.7,
                    "inverse_coherence_dualxda": 0.3,
                    "expected_entropy": base,
                }
            )
    return pd.DataFrame(rows)


def test_synthesis_pairwise_pairs_subset() -> None:
    labels = {p[0] for p in synthesis_pairwise_pairs()}
    assert "noisy_vs_sparse" in labels
    assert "clean_minus_ood" in labels
    assert "ood_minus_noisy" not in labels


def test_synthesis_plot_metrics_includes_headline_four() -> None:
    metrics = synthesis_plot_metrics()
    assert "attribution_entropy_dualxda" in metrics
    assert "attribution_participation_dualxda" in metrics
    assert "coherence_dualxda" in metrics
    assert "mutual_info" in metrics
    assert "expected_entropy" not in metrics


def test_pairwise_auroc_synthesis_log_profile(capsys) -> None:
    df = _df()
    cols = [
        "attribution_entropy_dualxda",
        "attribution_participation_dualxda",
        "coherence_dualxda",
        "inverse_coherence_dualxda",
        "expected_entropy",
    ]
    pair_auroc = four_region_pairwise_auroc_report(
        df,
        cols,
        log=False,
    )["pair_auroc"]
    print_four_region_pairwise_auroc(
        pair_auroc,
        pairs=synthesis_pairwise_pairs(),
        signals=["expected_entropy"],
        title="test",
    )
    out = capsys.readouterr().out
    assert "noisy_vs_sparse" in out
    assert "expected_entropy" in out


def test_print_synthesis_task2(capsys) -> None:
    table = pd.DataFrame(
        [
            {
                "slice": "noisy_region",
                "stratify_clean_label": None,
                "signal": "attribution_entropy_dualxda",
                "target": "label_disagreement",
                "rho": 0.71,
                "n": 300,
                "skip_reason": None,
            },
            {
                "slice": "noisy_region",
                "stratify_clean_label": None,
                "signal": "attribution_participation_dualxda",
                "target": "noisy_support_ratio",
                "rho": -0.77,
                "n": 300,
                "skip_reason": None,
            },
        ]
    )
    print_synthesis_task2(table)
    out = capsys.readouterr().out
    assert "label_disagreement" in out
    assert "+0.71" in out
    assert "-0.77" in out


def test_print_synthesis_pool_auroc_headline_and_aux(capsys) -> None:
    pair_auroc = pd.DataFrame(
        {
            "attribution_participation_dualxda": [0.698],
            "attribution_entropy_dualxda": [0.671],
            "mutual_info": [0.734],
            "coherence_dualxda": [0.578],
            "inverse_coherence_dualxda": [0.422],
            "expected_entropy": [0.880],
            "inverse_coherence_ek_fak": [0.485],
        },
        index=["noisy_vs_sparse"],
    )
    pair_auroc.loc["sparse_minus_ood"] = {
        "inverse_coherence_dualxda": 0.830,
    }
    pair_auroc.loc["clean_minus_ood"] = {
        "attribution_participation_dualxda": 0.730,
    }

    print_synthesis_pool_auroc(pair_auroc)
    out = capsys.readouterr().out
    assert "inverse_coherence_dualxda" in out
    assert "expected_entropy" in out
    assert "sparse_minus_ood" in out
    assert "clean_minus_ood" in out


def test_print_synthesis_backend_coh(capsys) -> None:
    pair_auroc = pd.DataFrame(
        {
            "inverse_coherence_dualxda": [0.422],
            "inverse_coherence_ek_fak": [0.409],
        },
        index=["noisy_vs_sparse"],
    )
    print_synthesis_backend_coh(pair_auroc)
    out = capsys.readouterr().out
    assert "DualXDA" in out
    assert "EK-FAC" in out
    assert "0.422" in out
