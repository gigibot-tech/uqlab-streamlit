"""Tests for Phase 4 data pipeline wiring."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for entry in (str(SRC), str(SCRIPTS)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import yaml

from uqlab.evaluation.classification.config import ExperimentConfig
from uqlab.evaluation.classification.pipeline.data_setup import prepare_fast_pilot_data
from uqlab.facade.coordinators.data_coordinator import DataCoordinator
from uqlab.facade.config_adapter import flat_dict_to_grouped_yaml


class TestDataSetupPipeline(unittest.TestCase):
    def test_flat_dict_to_grouped_yaml_has_dataset_name(self):
        grouped = flat_dict_to_grouped_yaml(
            {"dataset_name": "cifar10", "under_supported": "3,7", "epochs": 2}
        )
        self.assertEqual(grouped["data"]["dataset_name"], "cifar10")
        self.assertEqual(grouped["training"]["epochs"], 2)

    def test_prepare_fast_pilot_data_cifar10(self):
        root = PROJECT_ROOT / "data" / "cifar10n"
        if not root.exists():
            self.skipTest("CIFAR data not available locally")

        cfg_dict = {
            "seed": 42,
            "device": "auto",
            "data": {
                "dataset_name": "cifar10",
                "noise_type": "clean_label",
                "under_supported_classes": [3, 7],
                "under_train_per_class": 30,
                "regular_train_per_class": 30,
                "eval_per_group": 20,
                "aleatoric_noise_percentage": 0.0,
            },
            "model": {
                "architecture": "resnet18_mcdropout",
                "training_mode": "end_to_end",
                "hidden_dim": 256,
                "dropout": 0.0,
            },
            "training": {"epochs": 2, "train_batch_size": 64, "feature_batch_size": 32},
            "evaluation": {"mc_passes": 0, "top_k": 5},
            "paths": {
                "data_root": str(root),
                "cifar10n_root": str(root),
                "results_base_dir": "./results",
                "feature_cache_dir": "./cache/fast_uncertainty_classification/features",
            },
        }
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            yaml.dump(cfg_dict, handle)
            path = Path(handle.name)
        try:
            config = ExperimentConfig.from_yaml(path)
            ctx = prepare_fast_pilot_data(config, PROJECT_ROOT, seed=42)
        finally:
            path.unlink(missing_ok=True)

        self.assertEqual(ctx.dataset_name, "cifar10")
        self.assertGreater(len(ctx.split_spec.train_indices), 0)
        self.assertGreater(len(ctx.split_spec.clean_eval_indices), 0)

    def test_data_coordinator_setup(self):
        root = PROJECT_ROOT / "data" / "cifar10n"
        if not root.exists():
            self.skipTest("CIFAR data not available locally")

        coordinator = DataCoordinator(
            {
                "seed": 42,
                "dataset_name": "cifar10",
                "noise_type": "clean_label",
                "under_supported": "3,7",
                "under_train_per_class": 30,
                "regular_train_per_class": 30,
                "eval_per_group": 20,
                "aleatoric_noise_percentage": 0.0,
                "model_type": "resnet",
                "training_mode": "end_to_end",
                "data_root": str(root),
                "project_root": str(PROJECT_ROOT),
            }
        )
        coordinator.setup()
        stats = coordinator.get_dataset_stats()
        self.assertEqual(stats["dataset_name"], "cifar10")
        self.assertGreater(stats["train_size"], 0)


if __name__ == "__main__":
    unittest.main()
