"""Tests for four-region eval scoring (OOD AUROC, N-way classifier)."""

from __future__ import annotations

import torch

from uqlab.runner.phases.eval import score_uncertainty_signals
from uqlab.run_artifacts import GROUP_ALEATORIC, GROUP_CLEAN, GROUP_EPISTEMIC, GROUP_OOD


def test_group_ood_scored_when_labels_present(tmp_path):
    n_per_group = 20
    labels = torch.tensor(
        [GROUP_CLEAN] * n_per_group
        + [GROUP_ALEATORIC] * n_per_group
        + [GROUP_EPISTEMIC] * n_per_group
        + [GROUP_OOD] * n_per_group
    )
    signal_table = {
        "test_signal": torch.linspace(0.0, 1.0, len(labels)),
    }
    n = len(labels)
    zeros = torch.zeros(n, dtype=torch.long)
    summary = score_uncertainty_signals(
        signal_table=signal_table,
        eval_group_labels=labels,
        eval_clean_labels=zeros,
        eval_is_noisy=torch.zeros(n, dtype=torch.bool),
        eval_noisy_labels=zeros,
        eval_dataset_index=torch.arange(n),
        results_dir=tmp_path,
        device=torch.device("cpu"),
        seed=0,
    )
    row = summary["one_vs_rest_auroc"][0]
    assert row["signal"] == "test_signal"
    assert row["ood_like_auroc"] is not None
    assert row["ood_like_auroc"] > 0.5
    assert row.get("ood_vs_clean_auroc") is not None
    assert row.get("noisy_vs_clean_auroc") is not None
    assert row.get("sparse_vs_clean_auroc") is not None
    assert len(summary["clf_rows"]) >= 1
