"""Regression: ClassificationImageDataset must work with DataLoader workers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class TestDataLoaderWorkers(unittest.TestCase):
    def test_classification_image_dataset_dataloader_workers(self):
        from torch.utils.data import DataLoader

        from uqlab.data.dataset_registry import load_classification_dataset
        from uqlab.data.image_dataset import ClassificationImageDataset
        from uqlab.data.preprocessing import get_dataset_image_transform

        root = PROJECT_ROOT / "data" / "cifar10n"
        if not root.exists():
            self.skipTest("CIFAR data not present locally")

        ds = load_classification_dataset(
            "cifar10", root=root, noise_type="clean_label", train=True, download=False
        )
        transform = get_dataset_image_transform("cifar10")
        subset = ClassificationImageDataset(ds, list(range(16)), transform=transform)
        loader = DataLoader(subset, batch_size=4, num_workers=2)
        images, labels = next(iter(loader))
        self.assertEqual(tuple(images.shape), (4, 3, 32, 32))
        self.assertEqual(tuple(labels.shape), (4,))


    def test_fashion_mnist_transform_dataloader_workers(self):
        from torch.utils.data import DataLoader

        from uqlab.data.dataset_registry import load_classification_dataset
        from uqlab.data.image_dataset import ClassificationImageDataset
        from uqlab.data.preprocessing import get_dataset_image_transform

        root = PROJECT_ROOT / "data" / "fashion_mnist"
        ds = load_classification_dataset(
            "fashion_mnist",
            root=root,
            noise_type="clean_label",
            train=True,
            download=False,
        )
        transform = get_dataset_image_transform("fashion_mnist")
        subset = ClassificationImageDataset(ds, list(range(8)), transform=transform)
        loader = DataLoader(subset, batch_size=4, num_workers=2)
        images, labels = next(iter(loader))
        self.assertEqual(tuple(images.shape), (4, 3, 32, 32))
        self.assertEqual(tuple(labels.shape), (4,))


if __name__ == "__main__":
    unittest.main()
