"""Tests for four-region CIFAR-10 partition splits."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from uqlab.data.class_regions import (
    DEFAULT_FOUR_REGION_PRESET,
    apply_region_noise,
    inject_class_label_noise,
    sample_indices_for_four_region,
    validate_class_regions,
)
from uqlab_orchestrator.config.workflow_defaults import default_workflow
from uqlab_orchestrator.run_spec import build_run_yaml


class _MockClassificationDataset:
    """Minimal in-memory dataset (5000 samples per class, like CIFAR-10 train)."""

    def __init__(self, samples_per_class: int = 5000, num_classes: int = 10) -> None:
        self.num_classes = num_classes
        labels = [c for c in range(num_classes) for _ in range(samples_per_class)]
        self._clean = np.asarray(labels, dtype=np.int64)
        self.noisy_labels = self._clean.copy()
        self.noise_mask = np.zeros(len(self._clean), dtype=bool)
        self.noise_rate = 0.0

    @property
    def clean_labels(self) -> np.ndarray:
        return self._clean

    def __len__(self) -> int:
        return len(self._clean)


def test_validate_class_regions_covers_all_classes():
    validate_class_regions(DEFAULT_FOUR_REGION_PRESET, num_classes=10)


def test_validate_class_regions_rejects_overlap():
    bad = {
        "noisy": {"classes": [0, 1]},
        "sparse": {"classes": [1, 2]},
        "clean": {"classes": [3, 4, 5, 6, 7]},
        "ood": {"classes": [8, 9]},
    }
    with pytest.raises(ValueError):
        validate_class_regions(bad, num_classes=10)


def test_inject_class_noise_only_on_target_classes():
    ds = _MockClassificationDataset()
    inject_class_label_noise(ds, [0, 1], 50.0, seed=0)
    labels = ds.clean_labels
    mask = ds.noise_mask
    noisy_in_01 = mask[(labels == 0) | (labels == 1)].mean()
    noisy_in_rest = mask[(labels >= 2)].mean()
    assert noisy_in_01 > 0.3
    assert noisy_in_rest == 0.0


def test_four_region_split_populates_all_pools():
    ds = _MockClassificationDataset()
    apply_region_noise(ds, DEFAULT_FOUR_REGION_PRESET, seed=42)
    split = sample_indices_for_four_region(
        ds,
        DEFAULT_FOUR_REGION_PRESET,
        regular_train_per_class=500,
        eval_per_group=50,
        seed=42,
    )
    assert len(split.train_indices) > 0
    assert len(split.clean_eval_indices) > 0
    assert len(split.aleatoric_eval_indices) > 0
    assert len(split.epistemic_eval_indices) > 0
    assert len(split.ood_eval_indices) > 0
    assert set(split.under_supported_classes) == {4, 5}

    labels = ds.clean_labels
    ood_labels = labels[split.ood_eval_indices]
    assert set(ood_labels.tolist()) <= {8, 9}
    train_labels = labels[split.train_indices]
    assert 8 not in train_labels and 9 not in train_labels


def test_build_four_region_experiment_config_uses_dataset_name_and_pixel_mlp():
    from uqlab.evaluation.four_region_validation import (
        FOUR_REGION_ARCHITECTURES,
        build_four_region_experiment_config,
    )

    assert "pixel_mlp" in FOUR_REGION_ARCHITECTURES
    cfg = build_four_region_experiment_config(
        DEFAULT_FOUR_REGION_PRESET,
        dataset="fashion_mnist",
        architecture="pixel_mlp",
    )
    assert cfg["data"]["dataset_name"] == "fashion_mnist"
    assert "dataset" not in cfg["data"]
    assert cfg["model"]["architecture"] == "pixel_mlp"
    assert cfg["data"]["partition_mode"] == "four_region"


def test_build_run_yaml_four_region():
    workflow = default_workflow()
    workflow["uncertainty_config"] = {
        **workflow["uncertainty_config"],
        "partition_mode": "four_region",
        "class_regions": copy.deepcopy(DEFAULT_FOUR_REGION_PRESET),
        "sweep_enabled": False,
        "sweep_target": "single",
        "epistemic_enabled": True,
        "aleatoric_enabled": True,
        "under_supported": "4,5",
        "under_train_per_class": 30,
        "regular_train_per_class": 300,
    }
    cfg = build_run_yaml(workflow)
    assert cfg["data"]["partition_mode"] == "four_region"
    assert cfg["data"]["class_regions"]["sparse"]["classes"] == [4, 5]
    assert cfg["data"]["under_supported_classes"] == [4, 5]
    assert cfg["data"]["aleatoric_noise_percentage"] == 0.0
