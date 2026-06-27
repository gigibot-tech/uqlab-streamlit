"""Tests for summary markdown writers."""

from __future__ import annotations

import argparse

from uqlab.evaluation.reporting.result_writers import build_results_markdown
from uqlab.data.experiment_loader import SplitSpec, _label_tensors_for_indices
import numpy as np


def test_build_results_markdown_accepts_four_tuple_auroc_rows():
    args = argparse.Namespace(noise_type="worse_label", dinov2_model="small")
    split_spec = SplitSpec(
        train_indices=np.array([0]),
        clean_eval_indices=np.array([1]),
        aleatoric_eval_indices=np.array([2]),
        epistemic_eval_indices=np.array([3]),
        under_supported_classes=[3, 5],
    )
    md = build_results_markdown(
        args=args,
        split_spec=split_spec,
        train_size=1,
        eval_sizes={"clean": 1, "aleatoric_like": 1, "epistemic_like": 1},
        auroc_rows=[("msp_uncertainty", 0.5, 0.8, None)],
        clf_rows=[("combined", 0.48)],
    )
    assert "msp_uncertainty" in md
    assert "0.5000" in md


def test_label_tensors_for_indices_cifar10_synthetic_noise(tmp_path):
    from uqlab.data.loaders.cifar10_loader import CIFAR10ClassificationDataset

    root = tmp_path / "cifar"
    ds = CIFAR10ClassificationDataset(root=str(root), train=True, download=True)
    ds.inject_custom_noise(noise_percentage=20.0, seed=42)
    noisy, clean, is_noisy = _label_tensors_for_indices(ds, [0, 1, 2, 3, 4])
    assert int(is_noisy.sum()) > 0
    assert (noisy != clean).any() == bool(is_noisy.any())
