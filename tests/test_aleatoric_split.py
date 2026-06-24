"""Aleatoric eval pool must work for plain CIFAR-10 (synthetic noise)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from uqlab.data.dataset_registry import load_classification_dataset
from uqlab.data.experiment_loader import sample_indices_for_experiment

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cifar10_synthetic_noise_populates_aleatoric_eval():
    root = PROJECT_ROOT / "data" / "cifar10n"
    if not (root / "cifar-10-batches-py").exists():
        return

    ds = load_classification_dataset(
        "cifar10",
        root=root,
        aleatoric_noise_percentage=25.0,
        download=False,
    )
    assert int(np.sum(ds.noise_mask)) > 0

    split = sample_indices_for_experiment(
        ds,
        under_supported_classes=[3, 7],
        under_train_per_class=300,
        regular_train_per_class=300,
        eval_per_group=100,
        seed=42,
        aleatoric_noise_percentage=25.0,
    )
    assert len(split.aleatoric_eval_indices) == 100
    assert len(split.clean_eval_indices) == 100
