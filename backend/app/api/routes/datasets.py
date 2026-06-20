"""Dataset statistics and exploration endpoints."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.ml_bootstrap import PROJECT_ROOT, ensure_ml_paths

logger = logging.getLogger(__name__)

ensure_ml_paths()

# Optional override for any dataset root (e.g. shared CIFAR cache on disk).
DATA_ROOT_OVERRIDE = os.getenv("DATA_ROOT")

router = APIRouter()


def _resolve_dataset_root(dataset_name: str) -> Path:
    """Resolve on-disk root via the shared registry (not CIFAR-10N-only)."""
    from uqlab.data.dataset_registry import resolve_data_root

    if DATA_ROOT_OVERRIDE:
        return Path(DATA_ROOT_OVERRIDE)
    return resolve_data_root(dataset_name, project_root=PROJECT_ROOT)


def _should_download(dataset_name: str, root: Path) -> bool:
    """Download torchvision data when the expected cache folder is missing."""
    if dataset_name == "mnist":
        return not (root / "MNIST").exists()
    if dataset_name in ("cifar10", "cifar10n"):
        return not (root / "cifar-10-batches-py").exists()
    return False


@router.get("")
async def list_datasets() -> dict[str, Any]:
    """List datasets registered in the plugin registry."""
    from uqlab.data.dataset_registry import DATASET_SPECS

    return {
        "datasets": [
            {
                "name": spec.name,
                "label": spec.label,
                "num_classes": spec.num_classes,
                "default_root": spec.default_root,
                "supports_human_noise": spec.supports_human_noise,
                "supports_synthetic_noise": spec.supports_synthetic_noise,
                "noise_options": list(spec.noise_options),
            }
            for spec in DATASET_SPECS.values()
        ]
    }


@router.get("/{dataset_name}/stats")
async def get_dataset_stats_by_name(
    dataset_name: str,
    noise_type: str = Query(
        "clean_label",
        description="Noise split (human noise for cifar10n; ignored for cifar10/mnist)",
    ),
) -> dict[str, Any]:
    """
    Dataset statistics via the shared registry/factory.

    Supports: ``cifar10``, ``cifar10n``, ``mnist``.
    """
    from uqlab.data.dataset_registry import compute_dataset_stats, get_dataset_spec, list_dataset_names

    key = dataset_name.lower()
    if key not in list_dataset_names():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported dataset: {dataset_name}. Available: {', '.join(list_dataset_names())}.",
        )

    spec = get_dataset_spec(key)
    if noise_type not in spec.noise_options and key != "cifar10n":
        noise_type = "clean_label"

    root = _resolve_dataset_root(key)
    root.parent.mkdir(parents=True, exist_ok=True)

    try:
        payload = compute_dataset_stats(
            key,
            noise_type,
            root=root,
            download=_should_download(key, root),
        )
        payload["source"] = "api"
        payload["data_root"] = str(root)
        return payload
    except Exception as e:
        logger.error("Error loading dataset stats for %s: %s", key, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dataset error: {e}") from e


@router.get("/cifar10n/stats")
async def get_dataset_stats(
    noise_type: str = Query("worse_label", description="Noise type to analyze"),
) -> dict[str, Any]:
    """Legacy CIFAR-10N stats endpoint."""
    payload = await get_dataset_stats_by_name("cifar10n", noise_type=noise_type)
    payload.pop("num_classes", None)
    return payload


@router.get("/cifar10n/confusion-matrix")
async def get_confusion_matrix(
    noise_type: str = Query("worse_label", description="Noise type to analyze"),
) -> dict[str, Any]:
    """Confusion matrix for CIFAR-10N human noise splits."""
    import numpy as np

    from uqlab.data.classification_dataset import dataset_clean_labels
    from uqlab.data.dataset_registry import load_classification_dataset

    root = _resolve_dataset_root("cifar10n")
    try:
        dataset = load_classification_dataset(
            "cifar10n",
            root=root,
            noise_type=noise_type,
            train=True,
            download=_should_download("cifar10n", root),
        )
        clean_labels = dataset_clean_labels(dataset)
        noisy_labels = (
            np.asarray(dataset.noisy_labels)
            if dataset.noisy_labels is not None
            else clean_labels
        )
        n_classes = dataset.num_classes
        confusion = np.zeros((n_classes, n_classes), dtype=int)
        for clean, noisy in zip(clean_labels, noisy_labels):
            confusion[int(clean), int(noisy)] += 1
        return {
            "matrix": confusion.tolist(),
            "class_names": list(dataset.class_names),
        }
    except Exception as e:
        logger.error("Error loading confusion matrix: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dataset error: {e}") from e
