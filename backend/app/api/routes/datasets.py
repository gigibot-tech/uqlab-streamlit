"""Dataset statistics and exploration endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import sys
import os
from typing import Any
import logging

logger = logging.getLogger(__name__)

# Configuration: Use environment variables for enterprise deployment
DTAG_ROOT_ENV = os.getenv("DTAG_ROOT")
DATA_DIR_ENV = os.getenv("CIFAR10N_DATA_DIR")

# Fail-fast: Determine paths at startup
if DTAG_ROOT_ENV:
    # Production: Use explicit environment variable
    DTAG_ROOT = Path(DTAG_ROOT_ENV)
    if not DTAG_ROOT.exists():
        raise RuntimeError(f"DTAG_ROOT path does not exist: {DTAG_ROOT}")
else:
    # Development: Try to find dtag directory
    CURRENT_FILE = Path(__file__).resolve()
    POSSIBLE_PATHS = [
        Path.home() / "Desktop" / "GigiApps" / "dtag",
        Path("/dtag"),
        CURRENT_FILE.parents[5] / "dtag" if len(CURRENT_FILE.parents) > 5 else None,
    ]
    
    DTAG_ROOT = None
    for path in POSSIBLE_PATHS:
        if path and path.exists():
            DTAG_ROOT = path
            logger.info(f"Found DTAG_ROOT at: {path}")
            break
    
    if not DTAG_ROOT:
        raise RuntimeError(
            "DTAG_ROOT not found. Set DTAG_ROOT environment variable or ensure "
            "dtag directory exists in one of: " + ", ".join(str(p) for p in POSSIBLE_PATHS if p)
        )

from app.core.ml_bootstrap import ensure_ml_paths

ensure_ml_paths()

# Optional legacy dtag on path
if DTAG_ROOT.exists():
    _dtag_entry = str(DTAG_ROOT)
    if _dtag_entry not in sys.path:
        sys.path.insert(0, _dtag_entry)

# Set data directory
if DATA_DIR_ENV:
    DATA_DIR = Path(DATA_DIR_ENV)
else:
    DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "cifar10n"

if not DATA_DIR.exists():
    logger.warning(f"Data directory does not exist: {DATA_DIR}")

os.environ["CIFAR10N_DATA_DIR"] = str(DATA_DIR)

router = APIRouter()


def _normalize_noise_type(noise_type: str) -> str:
    """Map UI aliases (``none``) to CIFAR-10N keys (``clean_label``)."""
    try:
        from uqlab.data_loaders.cifar10n_loader import normalize_noise_type

        return normalize_noise_type(noise_type)
    except ImportError:
        aliases = {"none": "clean_label", "clean": "clean_label", "no_noise": "clean_label"}
        return aliases.get(noise_type, noise_type)


# Lazy import helper - only import when needed
def _get_cifar10n_dataset():
    """Lazy import of CIFAR10NDataset to avoid startup failures."""
    try:
        from uqlab.data_loaders.cifar10n_loader import CIFAR10NDataset
        import numpy as np
        return CIFAR10NDataset, np
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"CIFAR10N dependencies not available. Error: {str(e)}"
        )

@router.get("/{dataset_name}/stats")
async def get_dataset_stats_by_name(
    dataset_name: str,
    noise_type: str = Query("clean_label", description="Noise type to analyze (CIFAR-10N only)"),
) -> dict[str, Any]:
    """
    Get dataset statistics including noise distribution.

    - ``cifar10``: original CIFAR-10 with clean labels (noise_type ignored).
    - ``cifar10n``: CIFAR-10N human-noisy labels; ``noise_type`` selects the split.
    """
    key = dataset_name.lower()
    if key not in ("cifar10", "cifar10n"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported dataset: {dataset_name}. Available: cifar10, cifar10n.",
        )

    CIFAR10NDataset, np = _get_cifar10n_dataset()
    resolved_noise = "clean_label" if key == "cifar10" else _normalize_noise_type(noise_type)

    try:
        dataset = CIFAR10NDataset(
            root=str(DATA_DIR), noise_type=resolved_noise, download=False, train=True
        )
        payload = _dataset_stats_payload(
            dataset, np, requested_noise_type=resolved_noise, dataset_name=key
        )
        return payload
    except Exception as e:
        logger.error(f"Error loading dataset stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dataset error: {str(e)}")


def _dataset_stats_payload(
    dataset, np, *, requested_noise_type: str, dataset_name: str = "cifar10n"
) -> dict[str, Any]:
    """Shared stats dict for CIFAR-10 / CIFAR-10N dataset instances."""
    total_samples = len(dataset)

    if dataset.noise_mask is not None:
        noisy_samples = int(np.sum(dataset.noise_mask))
        noise_rate = float(dataset.noise_rate)
    else:
        noisy_samples = 0
        noise_rate = 0.0

    clean_labels = np.array(dataset.cifar10.targets)
    class_counts = {int(i): int(np.sum(clean_labels == i)) for i in range(10)}

    noise_per_class = {}
    for i in range(10):
        class_mask = clean_labels == i
        if dataset.noise_mask is not None:
            class_noisy = int(np.sum(dataset.noise_mask[class_mask]))
        else:
            class_noisy = 0

        total_in_class = int(np.sum(class_mask))
        noise_per_class[int(i)] = {
            "total": total_in_class,
            "noisy": class_noisy,
            "rate": float(class_noisy / total_in_class) if total_in_class > 0 else 0.0,
        }

    class_names = dataset.cifar10.classes

    return {
        "dataset_name": dataset_name,
        "total_samples": total_samples,
        "num_classes": 10,
        "noisy_samples": noisy_samples,
        "clean_samples": total_samples - noisy_samples,
        "noise_rate": noise_rate,
        "noise_type": requested_noise_type,
        "resolved_noise_type": dataset.noise_type,
        "class_distribution": class_counts,
        "noise_per_class": noise_per_class,
        "class_names": class_names,
    }


@router.get("/cifar10n/stats")
async def get_dataset_stats(
    noise_type: str = Query("worse_label", description="Noise type to analyze")
) -> dict[str, Any]:
    """Get CIFAR-10N dataset statistics including noise distribution (legacy endpoint)."""
    CIFAR10NDataset, np = _get_cifar10n_dataset()
    resolved_noise = _normalize_noise_type(noise_type)

    try:
        dataset = CIFAR10NDataset(
            root=str(DATA_DIR), noise_type=resolved_noise, download=False, train=True
        )
        payload = _dataset_stats_payload(
            dataset, np, requested_noise_type=noise_type, dataset_name="cifar10n"
        )
        payload.pop("num_classes", None)
        return payload
    except Exception as e:
        logger.error(f"Error loading dataset stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dataset error: {str(e)}")


@router.get("/cifar10n/confusion-matrix")
async def get_confusion_matrix(
    noise_type: str = Query("worse_label", description="Noise type to analyze")
) -> dict[str, Any]:
    """Get confusion matrix showing clean vs noisy label relationships."""
    CIFAR10NDataset, np = _get_cifar10n_dataset()
    
    try:
        dataset = CIFAR10NDataset(root=str(DATA_DIR), noise_type=noise_type, download=False, train=True)

        # Get clean labels from wrapped CIFAR10 dataset
        clean_labels = np.array(dataset.cifar10.targets)
        
        # Get noisy labels if available
        if dataset.noisy_labels is not None:
            noisy_labels = dataset.noisy_labels
        else:
            noisy_labels = clean_labels

        # Build confusion matrix
        confusion = np.zeros((10, 10), dtype=int)
        for clean, noisy in zip(clean_labels, noisy_labels):
            confusion[clean, noisy] += 1

        # Get class names from CIFAR10
        class_names = dataset.cifar10.classes

        return {
            "matrix": confusion.tolist(),
            "class_names": class_names,
        }
    except Exception as e:
        logger.error(f"Error loading confusion matrix: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dataset error: {str(e)}")

# Made with Bob
