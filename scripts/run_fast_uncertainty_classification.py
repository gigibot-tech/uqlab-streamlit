"""
Fast uncertainty-classification pilot using CIFAR-10/CIFAR-10N and DualXDA.

Goal:
  Distinguish clean, aleatoric-like, and epistemic-like samples quickly in a
  controlled setting, without starting from AURC or active learning.

Design:
  - Aleatoric-like: CIFAR-10N points with noisy_label != clean_label
  - Epistemic-like: clean points from intentionally under-supported classes
  - Clean: clean points from well-supported classes

Runtime strategy:
  - frozen DINOv2 features on a selected subset only
  - tiny dropout MLP on top of features
  - DualXDA on feature-level model / feature-level train dataset
"""

from __future__ import annotations

# Standard library
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Third-party
import numpy as np
import torch
import torch.nn as nn

# Setup logger
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add src directory to path for uqlab imports
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ============================================================================
# MODULAR IMPORTS: Explicit, specific imports from each module
# ============================================================================

# Data loading
from uqlab.data.loaders.cifar10n_loader import CIFAR10NDataset
from torch.utils.data import Dataset
from torchvision import datasets, transforms

# Uncertainty metrics
from uqlab.mc_dropout_uq import calculate_mc_dropout_uncertainty, mc_forward_efficient

# Attribution methods
from uqlab.triage.dualxda_axioms import DualXDATracer, infer_classifier_layer_name

# UQ Classification package - Constants
GROUP_CLEAN = 0
GROUP_ALEATORIC = 1
GROUP_EPISTEMIC = 2
GROUP_NAMES: dict[int, str] = {
    GROUP_CLEAN: "clean",
    GROUP_ALEATORIC: "aleatoric_like",
    GROUP_EPISTEMIC: "epistemic_like",
}

# UQ Classification package - Models
from uq_classification.models import EmbeddingDataset
from uq_classification.config import ExperimentConfig
from uq_classification.model_factory import build_model
from uq_classification.feature_extractor import create_feature_extractor, DINOv2FeatureExtractor

# UQ Classification package - Utils
from uq_classification.utils import auto_device, dino_transform, set_seed

# UQ Classification package - Data loading
from uq_classification.data_loader import (
    EmbeddingOrganizer,
    SplitSpec,
    sample_indices_for_fast_pilot,
)

from uq_classification.signal_formula_specs import build_signal_formula_manifest

# UQ Classification package - Evaluation
from uq_classification.evaluation import (
    binary_auroc,
    build_results_markdown,
    save_per_sample_csv,
    save_training_data_csv,
    split_group_balanced_targets,
    train_signal_classifier,
)

# UQLab artifacts
from uqlab.run_artifacts import save_zwischen_result

# UQLab classification - Attribution signals
from uqlab.classification.attribution_signals import (
    build_fast_pilot_signal_table,
    compute_attribution_structure_signals,
)


class CIFAR10NImageDataset(Dataset):
    """Subset wrapper returning image data with labels/metadata for end-to-end training."""

    def __init__(self, base_dataset: CIFAR10NDataset, indices, transform=None):
        self.base_dataset = base_dataset
        self.indices = np.asarray(indices, dtype=np.int64)
        self.transform = transform

        clean_labels = np.asarray(base_dataset.cifar10.targets)
        if base_dataset.noisy_labels is not None and base_dataset.noise_mask is not None:
            noisy_labels = np.asarray(base_dataset.noisy_labels)
            is_noisy = np.asarray(base_dataset.noise_mask, dtype=bool)
        else:
            noisy_labels = clean_labels.copy()
            is_noisy = np.zeros(len(base_dataset), dtype=bool)

        self.targets = torch.as_tensor(noisy_labels[self.indices], dtype=torch.long)
        self.clean_labels = torch.as_tensor(clean_labels[self.indices], dtype=torch.long)
        self.is_noisy = torch.as_tensor(is_noisy[self.indices], dtype=torch.bool)
        self.original_indices = torch.as_tensor(self.indices, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, item: int):
        dataset_index = int(self.indices[item])
        image = self.base_dataset.cifar10.data[dataset_index]
        image = transforms.ToPILImage()(image)

        if self.transform is not None:
            image = self.transform(image)

        return image, self.targets[item]


def get_data_loading_mode(config: ExperimentConfig) -> str:
    """Determine data loading mode from config."""
    model_config = config.model
    if model_config is None:
        raise ValueError("ExperimentConfig.model must be set")

    if model_config.training_mode == "feature_space":
        return "embeddings"
    if model_config.training_mode == "end_to_end":
        return "images"
    raise ValueError(f"Unknown training mode: {model_config.training_mode}")


def load_image_datasets(
    dataset: CIFAR10NDataset,
    split_spec: SplitSpec,
) -> tuple[CIFAR10NImageDataset, dict[str, dict[str, torch.Tensor]]]:
    """Load CIFAR-10N subsets as image datasets for end-to-end training."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(
            (0.4914, 0.4822, 0.4465),
            (0.2023, 0.1994, 0.2010),
        ),
    ])

    train_dataset = CIFAR10NImageDataset(dataset, split_spec.train_indices, transform=transform)

    def build_eval_pack(indices: np.ndarray) -> dict[str, torch.Tensor]:
        subset = CIFAR10NImageDataset(dataset, indices, transform=transform)
        images = torch.stack([subset[i][0] for i in range(len(subset))], dim=0) if len(subset) > 0 else torch.empty((0, 3, 32, 32), dtype=torch.float32)
        return {
            "inputs": images,
            "features": images,
            "noisy_labels": subset.targets,
            "clean_labels": subset.clean_labels,
            "is_noisy": subset.is_noisy,
            "original_indices": subset.original_indices,
        }

    eval_packs = {
        "clean": build_eval_pack(split_spec.clean_eval_indices),
        "aleatoric": build_eval_pack(split_spec.aleatoric_eval_indices),
        "epistemic": build_eval_pack(split_spec.epistemic_eval_indices),
    }

    return train_dataset, eval_packs


def prepare_eval_data(
    clean_eval_pack: dict[str, torch.Tensor],
    aleatoric_eval_pack: dict[str, torch.Tensor],
    epistemic_eval_pack: dict[str, torch.Tensor],
) -> dict[str, torch.Tensor]:
    """Concatenate eval packs and build shared eval metadata tensors."""
    eval_inputs = torch.cat(
        [
            clean_eval_pack["features"],
            aleatoric_eval_pack["features"],
            epistemic_eval_pack["features"],
        ],
        dim=0,
    )
    eval_group_labels = torch.cat(
        [
            torch.full((len(clean_eval_pack["features"]),), GROUP_CLEAN, dtype=torch.long),
            torch.full((len(aleatoric_eval_pack["features"]),), GROUP_ALEATORIC, dtype=torch.long),
            torch.full((len(epistemic_eval_pack["features"]),), GROUP_EPISTEMIC, dtype=torch.long),
        ],
        dim=0,
    )
    eval_clean_labels = torch.cat(
        [
            clean_eval_pack["clean_labels"],
            aleatoric_eval_pack["clean_labels"],
            epistemic_eval_pack["clean_labels"],
        ],
        dim=0,
    )
    eval_is_noisy = torch.cat(
        [
            clean_eval_pack["is_noisy"],
            aleatoric_eval_pack["is_noisy"],
            epistemic_eval_pack["is_noisy"],
        ],
        dim=0,
    )
    eval_noisy_labels = torch.cat(
        [
            clean_eval_pack["noisy_labels"],
            aleatoric_eval_pack["noisy_labels"],
            epistemic_eval_pack["noisy_labels"],
        ],
        dim=0,
    )
    eval_dataset_index = torch.cat(
        [
            clean_eval_pack["original_indices"],
            aleatoric_eval_pack["original_indices"],
            epistemic_eval_pack["original_indices"],
        ],
        dim=0,
    )
    return {
        "eval_inputs": eval_inputs,
        "eval_group_labels": eval_group_labels,
        "eval_clean_labels": eval_clean_labels,
        "eval_is_noisy": eval_is_noisy,
        "eval_noisy_labels": eval_noisy_labels,
        "eval_dataset_index": eval_dataset_index,
    }


def compute_eval_signals(
    *,
    model: nn.Module,
    train_dataset,
    eval_inputs: torch.Tensor,
    device: torch.device,
    train_batch_size: int,
    mc_passes: int,
    top_k: int,
    run_cache_dir: Path,
    results_dir: Path,
) -> dict[str, object]:
    """Run deterministic eval, attribution signals, MC dropout, and build the signal table."""
    eval_x = eval_inputs.to(device)
    eval_batch_size = train_batch_size

    print("Deterministic eval forward (DualXDA targets)...")
    det_logits_chunks: list[torch.Tensor] = []
    with torch.no_grad():
        model.eval()
        for start in range(0, int(eval_x.shape[0]), eval_batch_size):
            end = min(start + eval_batch_size, int(eval_x.shape[0]))
            det_logits_chunks.append(model(eval_x[start:end]).cpu())
    det_logits = torch.cat(det_logits_chunks, dim=0)
    mean_pred_det = torch.softmax(det_logits, dim=1)

    save_zwischen_result(
        results_dir,
        "01_deterministic_forward",
        {
            "det_logits": det_logits,
            "mean_prediction": mean_pred_det,
        },
    )

    tracer = DualXDATracer(
        model=model,
        train_dataset=train_dataset,
        layer_name=infer_classifier_layer_name(model),
        device=str(device),
        cache_dir=str(run_cache_dir / "dualxda"),
    )
    print("DualXDA attribution signals...")
    attribution_signals = compute_attribution_structure_signals(
        tracer,
        model,
        eval_inputs,
        mean_pred_det,
        train_dataset,
        device=device,
        batch_size=train_batch_size,
        top_k=top_k,
        num_classes=10,
    )
    save_zwischen_result(
        results_dir,
        "02_attribution_signals",
        {k: v.cpu() if hasattr(v, "cpu") else v for k, v in attribution_signals.items()},
    )

    logit_magnitude = torch.abs(det_logits).sum(dim=1)
    save_zwischen_result(
        results_dir,
        "03_logit_signals",
        {
            "det_logits": det_logits,
            "logit_magnitude": logit_magnitude,
        },
    )

    # MC Dropout uncertainty quantification (skip if mc_passes=0)
    if mc_passes > 0:
        print(f"MC Dropout ({mc_passes} passes, batched eval)...")
        mc_predictions = mc_forward_efficient(
            model,
            eval_x,
            mc_passes,
            sample_batch_size=eval_batch_size,
        ).cpu()
        uq = calculate_mc_dropout_uncertainty(mc_predictions)
        save_zwischen_result(
            results_dir,
            "04_mc_dropout",
            {
                "entropy": uq["entropy"].cpu(),
                "mutual_info": uq["mutual_info"].cpu(),
                "mean_variance": uq["mean_variance"].cpu(),
                "mean_prediction": uq["mean_prediction"].cpu(),
                "n_passes": mc_passes,
            },
        )
    else:
        print("⚠️  MC Dropout disabled (mc_passes=0) - using deterministic predictions only")
        # Create dummy mc_predictions and UQ dict with zeros for compatibility
        n_samples = eval_x.shape[0]
        n_classes = det_logits.shape[1]
        # mc_predictions shape: (n_passes=1, n_samples, n_classes) - use deterministic prediction
        mc_predictions = mean_pred_det.unsqueeze(0)  # Add pass dimension
        uq = {
            "entropy": torch.zeros(n_samples),
            "mutual_info": torch.zeros(n_samples),
            "mean_variance": torch.zeros(n_samples),
            "mean_prediction": mean_pred_det,  # Use deterministic prediction
        }
        save_zwischen_result(
            results_dir,
            "04_mc_dropout",
            {
                "entropy": uq["entropy"],
                "mutual_info": uq["mutual_info"],
                "mean_variance": uq["mean_variance"],
                "mean_prediction": uq["mean_prediction"],
                "n_passes": 0,
                "note": "MC Dropout disabled - all uncertainty metrics are zero",
            },
        )

    signal_table = build_fast_pilot_signal_table(
        attribution_signals=attribution_signals,
        mc_uq=uq,
        logit_magnitude=logit_magnitude,
    )
    save_zwischen_result(
        results_dir,
        "05_signal_table",
        {k: v.cpu() if hasattr(v, "cpu") else v for k, v in signal_table.items()},
    )

    return {
        "eval_x": eval_x,
        "det_logits": det_logits,
        "mean_pred_det": mean_pred_det,
        "attribution_signals": attribution_signals,
        "logit_magnitude": logit_magnitude,
        "mc_predictions": mc_predictions,
        "uq": uq,
        "signal_table": signal_table,
    }


def summarize_eval_signals(
    *,
    signal_table: dict[str, torch.Tensor],
    eval_group_labels: torch.Tensor,
    eval_clean_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    eval_noisy_labels: torch.Tensor,
    eval_dataset_index: torch.Tensor,
    results_dir: Path,
    device: torch.device,
    seed: int,
) -> dict[str, list]:
    """Compute eval summaries and write per-sample signal artifacts."""
    aleatoric_positive = eval_group_labels == GROUP_ALEATORIC
    epistemic_positive = eval_group_labels == GROUP_EPISTEMIC

    auroc_rows = []
    for name, values in signal_table.items():
        auroc_rows.append(
            (
                name,
                binary_auroc(values, aleatoric_positive),
                binary_auroc(values, epistemic_positive),
            )
        )

    from uq_classification.evaluation import evaluate_three_way_classification

    clf_rows = evaluate_three_way_classification(
        signal_table=signal_table,
        eval_group_labels=eval_group_labels,
        device=device,
        seed=seed,
        train_fraction=0.5,
    )

    save_per_sample_csv(
        results_dir / "per_sample_signals.csv",
        eval_group_labels,
        eval_clean_labels,
        eval_is_noisy,
        signal_table,
        GROUP_NAMES,
        eval_noisy_labels=eval_noisy_labels,
        eval_dataset_index=eval_dataset_index,
    )

    return {
        "auroc_rows": auroc_rows,
        "clf_rows": clf_rows,
    }


def train_feature_model(
    model: torch.nn.Module,
    train_dataset: Dataset,
    training_config,
    device: torch.device,
) -> torch.nn.Module:
    """Train a model on embedding datasets."""
    from torch.utils.data import DataLoader

    loader = DataLoader(
        train_dataset,
        batch_size=training_config.train_batch_size,
        shuffle=True,
        num_workers=0,
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=training_config.learning_rate,
        weight_decay=training_config.weight_decay,
    )
    criterion = nn.CrossEntropyLoss()

    model = model.to(device)
    model.train()
    for epoch in range(training_config.epochs):
        total_loss = 0.0
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())
        if (epoch + 1) % max(1, training_config.epochs // 3) == 0 or epoch == training_config.epochs - 1:
            print(
                f"  Epoch {epoch + 1}/{training_config.epochs}, "
                f"loss={total_loss / max(1, len(loader)):.4f}"
            )

    return model


def train_image_model(
    model: nn.Module,
    train_dataset: Dataset,
    training_config,
    device: torch.device,
) -> nn.Module:
    """Train model end-to-end on images."""
    from torch.utils.data import DataLoader
    import torch.optim as optim

    train_loader = DataLoader(
        train_dataset,
        batch_size=training_config.train_batch_size,
        shuffle=True,
        num_workers=4,
    )

    optimizer = optim.Adam(
        model.parameters(),
        lr=training_config.learning_rate,
        weight_decay=training_config.weight_decay,
    )

    criterion = nn.CrossEntropyLoss()

    model = model.to(device)
    model.train()
    for epoch in range(training_config.epochs):
        total_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            total_loss += float(loss.item())

        print(
            f"Epoch {epoch + 1}/{training_config.epochs}, "
            f"Loss: {total_loss / max(1, len(train_loader)):.4f}"
        )

    return model


def main() -> None:
    """
    Main experiment workflow for fast uncertainty classification.
    
    Configuration Structure:
    ------------------------
    The experiment is controlled by a YAML config file with the following sections:
    
    1. DATA PARAMETERS (data.*):
       - noise_type: Which CIFAR-10N noise labels to use
       - under_supported_classes: Classes with reduced training samples (creates epistemic uncertainty)
       - under_train_per_class: Training samples for under-supported classes
       - regular_train_per_class: Training samples for well-supported classes
       - eval_per_group: Evaluation samples per uncertainty group
       
       Effect: Controls the dataset split and how uncertainty groups are created.
       Lower under_train_per_class → stronger epistemic uncertainty signal.
    
    2. MODEL PARAMETERS (model.*):
       - dinov2_model: Size of frozen feature extractor ("small", "base", "large", "giant")
       - hidden_dim: Size of trainable MLP classifier on top of features
       - dropout: Dropout rate for MC Dropout uncertainty estimation
       
       Effect: Controls model capacity and uncertainty estimation quality.
       Larger models → better features but slower. Higher dropout → more uncertainty.
    
    3. TRAINING PARAMETERS (training.*):
       - epochs: Number of training epochs for the classifier
       - learning_rate: Adam optimizer learning rate
       - weight_decay: L2 regularization strength
       - train_batch_size: Batch size for classifier training
       - feature_batch_size: Batch size for feature extraction
       
       Effect: Controls training speed and model convergence.
       More epochs → better convergence. Larger batches → faster but less stable.
    
    4. EVALUATION PARAMETERS (evaluation.*):
       - mc_passes: Number of Monte Carlo forward passes for uncertainty
       - top_k: Number of top training samples for attribution analysis
       
       Effect: Controls uncertainty and attribution quality vs. speed.
       More mc_passes → more stable uncertainty. Higher top_k → richer attribution context.
    
    5. PATH PARAMETERS (paths.*):
       - cifar10n_root: Location of CIFAR-10N dataset
       - feature_cache_dir: Where to cache extracted features
       - results_base_dir: Where to save experiment results
       
       Effect: Controls data locations and caching behavior.
    
    CLI Arguments:
    --------------
    Only essential arguments are exposed via CLI (others come from config):
    - --config: Path to YAML config file (default: experiments/configs/fast_uq_classification.yaml)
    - --seed: Random seed for reproducibility
    - --device: Device to use (auto/cpu/cuda/mps)
    - --output_dir: Override output directory (optional)
    
    Recommended Values / Presets:
    -----------------------------
    The backend now exposes named presets that resolve to concrete flat config values
    before being written into this grouped YAML structure.

    Quick preset (5-10 min):
      - under_train_per_class: 40
      - regular_train_per_class: 250
      - eval_per_group: 500
      - dinov2_model: "small"
      - epochs: 10
      - mc_passes: 15
      - top_k: 8

    Thorough preset (30-60 min):
      - under_train_per_class: 150
      - regular_train_per_class: 750
      - eval_per_group: 1500
      - dinov2_model: "base"
      - epochs: 24
      - mc_passes: 75
      - top_k: 30

    API usage:
      - single experiment endpoints accept either:
        * preset = "quick" | "thorough"
        * or an explicit config payload
      - batch experiment endpoints accept either:
        * preset = "quick" | "thorough"
        * or an explicit base_config payload
    """
    # Parse arguments (minimal CLI interface)
    parser = argparse.ArgumentParser(
        description="Fast uncertainty classification pilot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python run_fast_uncertainty_classification.py
  
  # Run with custom config
  python run_fast_uncertainty_classification.py --config my_config.yaml
  
  # Override seed and device
  python run_fast_uncertainty_classification.py --seed 123 --device cuda
  
  # Custom output directory
  python run_fast_uncertainty_classification.py --output_dir ./my_results
        """
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(PROJECT_ROOT / "experiments" / "configs" / "fast_uq_classification.yaml"),
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (overrides config if provided)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to use (overrides config if provided)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Override output directory (default: results/fast_uncertainty_classification_TIMESTAMP)"
    )
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Please create a config file or use the default at:\n"
            f"  {PROJECT_ROOT / 'experiments' / 'configs' / 'fast_uq_classification.yaml'}"
        )
    
    config = ExperimentConfig.from_yaml(config_path)
    if config.data is None or config.model is None or config.training is None or config.evaluation is None or config.paths is None:
        raise ValueError("ExperimentConfig is incomplete; data/model/training/evaluation/paths must be defined")

    # Extract parameters from config with CLI overrides
    seed = args.seed if args.seed is not None else config.seed
    device_str = args.device if args.device is not None else config.device
    
    # Setup
    set_seed(seed)
    device = auto_device(device_str)

    # Setup directories
    if args.output_dir:
        results_dir = Path(args.output_dir)
    else:
        results_base = PROJECT_ROOT / config.paths.results_base_dir
        results_dir = results_base / f"fast_uncertainty_classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    feature_cache_dir = PROJECT_ROOT / config.paths.feature_cache_dir
    run_cache_dir = results_dir / "cache"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Extract data parameters
    data_config = config.data
    noise_type = data_config.noise_type
    under_supported_classes = data_config.under_supported_classes or []
    under_supported_classes_str = ",".join(str(x) for x in under_supported_classes)
    under_train_per_class = data_config.under_train_per_class
    regular_train_per_class = data_config.regular_train_per_class
    eval_per_group = data_config.eval_per_group
    aleatoric_noise_percentage = data_config.aleatoric_noise_percentage

    # Extract model parameters
    model_config = config.model
    dinov2_model = model_config.dinov2_model
    hidden_dim = model_config.hidden_dim
    dropout = model_config.dropout

    # Extract training parameters
    training_config = config.training
    epochs = training_config.epochs
    learning_rate = training_config.learning_rate
    weight_decay = training_config.weight_decay
    train_batch_size = training_config.train_batch_size
    feature_batch_size = training_config.feature_batch_size

    # Extract evaluation parameters
    eval_config = config.evaluation
    mc_passes = eval_config.mc_passes
    top_k = eval_config.top_k
    
    # Validate mc_passes - warn if 0 (MC Dropout disabled)
    if mc_passes < 0:
        raise ValueError(
            f"mc_passes must be >= 0, got {mc_passes}. "
            f"Set to 0 to disable MC Dropout (faster but no uncertainty), "
            f"or use 5-10 for efficient uncertainty estimation (recommended: 10-50 for accuracy)."
        )
    elif mc_passes == 0:
        logger.warning(
            "⚠️  MC Dropout disabled (mc_passes=0): No uncertainty quantification will be performed. "
            "This is faster but provides no epistemic uncertainty estimates. "
            "Consider using mc_passes=5-10 for efficient uncertainty estimation."
        )

    # Aleatoric control happens here:
    # - `aleatoric_noise_percentage == 0` -> ALWAYS use clean labels (ignore noise_type)
    # - `aleatoric_noise_percentage > 0` -> custom random flips
    # - `aleatoric_noise_percentage is None` -> use CIFAR-10N noise from `noise_type`
    cifar10n_root = Path(config.paths.cifar10n_root)
    if not cifar10n_root.is_absolute():
        cifar10n_root = PROJECT_ROOT / cifar10n_root

    # ============================================================================
    # EXPERIMENT CONFIGURATION SUMMARY
    # ============================================================================
    print("\n" + "="*80)
    print("EXPERIMENT CONFIGURATION")
    print("="*80)
    print(f"📊 Dataset Configuration:")
    print(f"   • Noise type: {noise_type}")
    print(f"   • Aleatoric noise: {aleatoric_noise_percentage}%")
    print(f"   • Under-supported classes: {under_supported_classes_str or 'None'}")
    print(f"   • Under-train per class: {under_train_per_class}")
    print(f"   • Regular-train per class: {regular_train_per_class}")
    print(f"   • Eval per group: {eval_per_group}")
    print(f"\n🧠 Model Configuration:")
    print(f"   • DINOv2 model: {dinov2_model}")
    print(f"   • Hidden dim: {hidden_dim}")
    print(f"   • Dropout: {dropout}")
    print(f"\n🎯 Training Configuration:")
    print(f"   • Epochs: {epochs}")
    print(f"   • Learning rate: {learning_rate}")
    print(f"   • Weight decay: {weight_decay}")
    print(f"   • Train batch size: {train_batch_size}")
    print(f"\n📈 Evaluation Configuration:")
    print(f"   • MC passes: {mc_passes}")
    print(f"   • Top-k attribution: {top_k}")
    print(f"\n💡 Expected Behavior:")
    if aleatoric_noise_percentage == 0:
        print(f"   ⚠️  Aleatoric AUROC will be NaN (no noisy samples in eval set)")
        print(f"   ✅ Epistemic AUROC will be calculated (under-supported vs regular classes)")
    elif aleatoric_noise_percentage > 0 and not under_supported_classes:
        print(f"   ✅ Aleatoric AUROC will be calculated (noisy vs clean samples)")
        print(f"   ⚠️  Epistemic AUROC may be weak (no under-supported classes)")
    else:
        print(f"   ✅ Both Aleatoric and Epistemic AUROC will be calculated")
    print("="*80 + "\n")

    from uqlab.data.loaders.cifar10n_loader import (
        apply_clean_training_labels,
        is_clean_training_noise_type,
    )

    # FIXED: When aleatoric_noise_percentage is explicitly set to 0, use clean labels
    # regardless of noise_type setting
    if aleatoric_noise_percentage == 0:
        print(
            "\n🎯 Fig. 3 / epistemic benchmark: clean labels only "
            "(aleatoric_noise_percentage=0%)"
        )
        dataset = CIFAR10NDataset(
            root=str(cifar10n_root),
            noise_type="clean_label",
            train=True,
            transform=dino_transform(),
            download=True,
        )
        apply_clean_training_labels(dataset)
        print(f"   ✅ {len(dataset)} training samples, 0% injected label noise")
    elif aleatoric_noise_percentage > 0:
        print(
            f"\n🎯 Fig. 4 / aleatoric benchmark: injecting {aleatoric_noise_percentage}% "
            "uniform label noise"
        )
        dataset = CIFAR10NDataset(
            root=str(cifar10n_root),
            noise_type="clean_label",
            train=True,
            transform=dino_transform(),
            download=True,
        )
        apply_clean_training_labels(dataset)
        dataset.inject_custom_noise(noise_percentage=aleatoric_noise_percentage, seed=42)
        print(
            f"   ✅ Custom noise: {len(dataset)} samples, {aleatoric_noise_percentage}% flipped"
        )
    elif is_clean_training_noise_type(noise_type):
        print(f"\n🎯 Loading CIFAR-10 with clean training labels (noise_type={noise_type})")
        dataset = CIFAR10NDataset(
            root=str(cifar10n_root),
            noise_type=noise_type,
            train=True,
            transform=dino_transform(),
            download=True,
        )
        apply_clean_training_labels(dataset)
        print(f"   ✅ Clean training labels: {len(dataset)} samples")
    else:
        print(f"\n🎯 Loading CIFAR-10N with existing noise (type: {noise_type})")
        dataset = CIFAR10NDataset(
            root=str(cifar10n_root),
            noise_type=noise_type,
            train=True,
            transform=dino_transform(),
            download=True,
        )
        if dataset.noise_mask is None or float(dataset.noise_rate) == 0.0:
            raise RuntimeError(
                "CIFAR-10N noisy labels are not available or the selected noise split "
                f"`{noise_type}` resolved to zero noise. For label-noise sweeps use "
                "`clean_label` with aleatoric_noise_percentage > 0. Otherwise place "
                f"`CIFAR-10_human.pt` under `{cifar10n_root / 'cifar-10-batches-py'}`."
            )

    # ============================================================================
    # ENTERPRISE VALIDATION: Fail Fast with Clear Error Messages
    # ============================================================================
    # Validate configuration BEFORE attempting data sampling
    # This catches invalid configs early and provides actionable error messages
    
    # Validate regular_train_per_class
    if regular_train_per_class is not None and regular_train_per_class < 0:
        raise ValueError(
            f"❌ Invalid regular_train_per_class={regular_train_per_class}. "
            f"Must be None or >= 0."
        )
    
    # Validate under_train_per_class
    if under_train_per_class < 0:
        raise ValueError(
            f"❌ Invalid under_train_per_class={under_train_per_class}. "
            f"Must be >= 0."
        )
    
    # Validate eval_per_group
    if eval_per_group <= 0:
        raise ValueError(
            f"❌ Invalid eval_per_group={eval_per_group}. "
            f"Must be > 0."
        )
    
    # Validate under_supported_classes
    if not under_supported_classes or len(under_supported_classes) == 0:
        raise ValueError(
            f"❌ Invalid under_supported_classes={under_supported_classes}. "
            f"Must specify at least one class (e.g., [3, 5])."
        )
    
    for cls in under_supported_classes:
        if cls < 0 or cls >= 10:
            raise ValueError(
                f"❌ Invalid class {cls} in under_supported_classes. "
                f"Must be in range [0, 9] for CIFAR-10."
            )
    
    # Log configuration
    logger.info("=" * 80)
    logger.info("CONFIGURATION VALIDATION")
    logger.info("=" * 80)
    logger.info(f"regular_train_per_class: {regular_train_per_class}")
    logger.info(f"under_train_per_class: {under_train_per_class}")
    logger.info(f"eval_per_group: {eval_per_group}")
    logger.info(f"under_supported_classes: {under_supported_classes}")
    logger.info("=" * 80)
    
    # IMPORTANT EXPERIMENT CONTROL:
    # This call hands the prepared dataset state to the split builder.
    #
    # By this point:
    # - noisy vs clean labels have already been decided above
    # - under-supported classes have already been chosen in config
    #
    # The split builder then:
    # - downsamples the under-supported classes for training
    # - builds clean / aleatoric / epistemic evaluation pools
    #
    # Key implementation file:
    #   src/uqlab/classification/data_loader.py
    # Key function:
    #   sample_indices_for_fast_pilot(...)
    split_spec: SplitSpec = sample_indices_for_fast_pilot(
        dataset,
        under_supported_classes=under_supported_classes,
        under_train_per_class=under_train_per_class,
        regular_train_per_class=regular_train_per_class,
        eval_per_group=eval_per_group,
        seed=args.seed,
        aleatoric_noise_percentage=aleatoric_noise_percentage,
    )
    
    # ============================================================================
    # POST-SAMPLING VALIDATION: Verify We Have Usable Data
    # ============================================================================
    
    # Log actual eval sizes
    logger.info("=" * 80)
    logger.info("EVALUATION SPLITS CREATED")
    logger.info("=" * 80)
    logger.info(f"Clean: {len(split_spec.clean_eval_indices)} samples")
    logger.info(f"Aleatoric: {len(split_spec.aleatoric_eval_indices)} samples")
    logger.info(f"Epistemic: {len(split_spec.epistemic_eval_indices)} samples")
    logger.info(f"Training: {len(split_spec.train_indices)} samples")
    logger.info("=" * 80)
    
    # Enterprise check: Fail fast if ALL eval groups are empty
    all_empty = (
        len(split_spec.clean_eval_indices) == 0 and
        len(split_spec.aleatoric_eval_indices) == 0 and
        len(split_spec.epistemic_eval_indices) == 0
    )
    
    if all_empty:
        raise RuntimeError(
            f"❌ CRITICAL: All evaluation groups are empty!\n"
            f"Configuration:\n"
            f"  - regular_train_per_class: {regular_train_per_class}\n"
            f"  - under_train_per_class: {under_train_per_class}\n"
            f"  - eval_per_group: {eval_per_group}\n"
            f"  - under_supported_classes: {under_supported_classes}\n"
            f"\n"
            f"This configuration leaves no samples for evaluation.\n"
            f"Possible fixes:\n"
            f"  1. Set regular_train_per_class to a valid number (e.g., 300)\n"
            f"  2. Reduce eval_per_group (currently {eval_per_group})\n"
            f"  3. Reduce under_train_per_class (currently {under_train_per_class})\n"
            f"  4. Use correct under_supported_classes (recommended: [3, 5])"
        )
    
    from uqlab.classification.benchmark_axes import (
        expects_aleatoric_eval,
        expects_epistemic_eval,
    )

    aleatoric_expected = expects_aleatoric_eval(aleatoric_noise_percentage)
    epistemic_expected = expects_epistemic_eval(
        under_supported_classes,
        under_train_per_class=under_train_per_class,
        regular_train_per_class=regular_train_per_class,
    )

    # Warn only when an expected benchmark axis has no eval samples.
    if len(split_spec.clean_eval_indices) == 0:
        logger.warning(
            "⚠️  Clean evaluation group is empty — clean AUROC will be NaN."
        )
    if len(split_spec.aleatoric_eval_indices) == 0:
        if aleatoric_expected:
            raise RuntimeError(
                f"❌ Aleatoric benchmark requested ({aleatoric_noise_percentage}% label noise) "
                "but the aleatoric eval pool is empty. "
                "Check aleatoric_noise_percentage and noise_type=clean_label in config."
            )
        logger.info(
            "ℹ️  Aleatoric AUROC skipped (0% label noise — this is normal for Fig. 3 runs)."
        )
    if len(split_spec.epistemic_eval_indices) == 0:
        if epistemic_expected:
            logger.warning(
                "⚠️  Epistemic evaluation group is empty — epistemic AUROC will be NaN."
            )
        else:
            logger.info(
                "ℹ️  Epistemic AUROC skipped (balanced training — normal for Fig. 4 runs)."
            )

    mode = get_data_loading_mode(config)
    
    # IMPORTANT: ResNet in feature_space mode works differently than DINOv2:
    # - DINOv2: Uses pre-computed cached features (embeddings mode)
    # - ResNet: Uses images directly but with frozen backbone (images mode)
    # Both achieve "feature space" training, but through different mechanisms
    if config.model.architecture == "resnet18_mcdropout" and mode == "embeddings":
        logger.info(
            "ResNet with feature_space mode: Using images with frozen backbone "
            "(ResNet doesn't support feature caching like DINOv2)"
        )
        mode = "images"  # Use images, but model will have freeze_backbone=True

    feature_extractor = None
    feature_dim = None

    if mode == "embeddings":
        # Only DINOv2 supports embeddings mode with feature caching
        feature_extractor = create_feature_extractor(
            config.model,
            device=device,
            dataset=dataset,
            split_spec=split_spec,
            feature_cache_dir=feature_cache_dir,
            noise_type=noise_type,
            batch_size=feature_batch_size,
        )
        
        if not isinstance(feature_extractor, DINOv2FeatureExtractor):
            raise TypeError("Expected DINOv2FeatureExtractor for feature_space mode")
        
        feature_extractor.organizer.load_or_compute_features()

        train_pack = feature_extractor.get_train_pack()
        clean_eval_pack = feature_extractor.get_clean_eval_pack()
        aleatoric_eval_pack = feature_extractor.get_aleatoric_eval_pack()
        epistemic_eval_pack = feature_extractor.get_epistemic_eval_pack()

        train_dataset = EmbeddingDataset(
            train_pack["features"],
            train_pack["noisy_labels"],
            train_pack["clean_labels"],
            train_pack["is_noisy"],
            train_pack["original_indices"],
        )
        eval_data = prepare_eval_data(
            clean_eval_pack,
            aleatoric_eval_pack,
            epistemic_eval_pack,
        )
        eval_inputs = eval_data["eval_inputs"]
        feature_dim = int(train_pack["features"].shape[1])
    elif mode == "images":
        train_dataset, eval_packs = load_image_datasets(dataset, split_spec)
        clean_eval_pack = eval_packs["clean"]
        aleatoric_eval_pack = eval_packs["aleatoric"]
        epistemic_eval_pack = eval_packs["epistemic"]
        eval_data = prepare_eval_data(
            clean_eval_pack,
            aleatoric_eval_pack,
            epistemic_eval_pack,
        )
        eval_inputs = eval_data["eval_inputs"]
    else:
        raise ValueError(f"Unsupported data loading mode: {mode}")

    # Build the model
    model = build_model(
        config=config.model,
        num_classes=10,
        feature_dim=feature_dim if mode == "embeddings" else None,
    )
    model = model.to(device)

    if mode == "images":
        feature_extractor = create_feature_extractor(
            config.model,
            device=device,
            model=model,
            batch_size=feature_batch_size,
        )

    print(f"Using device: {device}")
    print(f"Results directory: {results_dir}")
    print(f"Train samples: {len(train_dataset)}")
    print(
        "Eval groups: "
        f"clean={len(clean_eval_pack['features'])}, "
        f"aleatoric_like={len(aleatoric_eval_pack['features'])}, "
        f"epistemic_like={len(epistemic_eval_pack['features'])}"
    )

    if mode == "embeddings":
        model = train_feature_model(model, train_dataset, training_config, device)
    elif mode == "images":
        model = train_image_model(model, train_dataset, training_config, device)
    else:
        raise ValueError(f"Unsupported training mode: {mode}")

    model = model.to(device)
    model.eval()

    # Save training data statistics to CSV
    print("\n" + "="*80)
    print("Saving training data statistics...")
    print("="*80)
    
    # Convert config to dict for serialization
    from dataclasses import asdict
    config_dict = asdict(config)
    # Convert Path objects to strings for JSON serialization
    if config_dict.get('paths'):
        for key, value in config_dict['paths'].items():
            if isinstance(value, Path):
                config_dict['paths'][key] = str(value)
    # Convert Pydantic model to dict
    if config_dict.get('model'):
        config_dict['model'] = dict(config.model)
    
    save_training_data_csv(
        output_path=results_dir / "training_data.csv",
        train_dataset=train_dataset,
        config=config_dict,
    )

    eval_group_labels = eval_data["eval_group_labels"]
    eval_clean_labels = eval_data["eval_clean_labels"]
    eval_is_noisy = eval_data["eval_is_noisy"]
    eval_noisy_labels = eval_data["eval_noisy_labels"]
    eval_dataset_index = eval_data["eval_dataset_index"]

    save_zwischen_result(
        results_dir,
        "00_eval_setup",
        {
            "eval_group_labels": eval_group_labels.cpu(),
            "eval_clean_labels": eval_clean_labels.cpu(),
            "eval_is_noisy": eval_is_noisy.cpu(),
            "eval_noisy_labels": eval_noisy_labels.cpu(),
            "eval_dataset_index": eval_dataset_index.cpu(),
            "n_eval": int(eval_inputs.shape[0]),
            "mc_passes": mc_passes,
        },
    )

    eval_outputs = compute_eval_signals(
        model=model,
        train_dataset=train_dataset,
        eval_inputs=eval_inputs,
        device=device,
        train_batch_size=train_batch_size,
        mc_passes=mc_passes,
        top_k=top_k,
        run_cache_dir=run_cache_dir,
        results_dir=results_dir,
    )
    det_logits = eval_outputs["det_logits"]
    mean_pred_det = eval_outputs["mean_pred_det"]
    uq = eval_outputs["uq"]
    signal_table = eval_outputs["signal_table"]
    if not isinstance(uq, dict):
        raise TypeError("compute_eval_signals() returned invalid `uq` payload")
    if not isinstance(signal_table, dict):
        raise TypeError("compute_eval_signals() returned invalid `signal_table` payload")
    print(f"✅ Zwischenergebnisse: {results_dir / 'zwischen'}/")

    # REMOVED SIGNALS (poor performers; still computed inside attribution_signals):
    # - attribution_concentration: Random performance (0.54 alea, 0.31 epis)
    # - label_disagreement: Random performance (0.50, 0.50)
    # - compound_uncertainty: Random performance (0.50, 0.50)
    # - noisy_support_ratio: Misclassified, redundant with inverse_mass
    # - inverse_max_logit: Redundant with inverse_mass
    # - cross_class_support: Poor performer

    eval_summary = summarize_eval_signals(
        signal_table=signal_table,
        eval_group_labels=eval_group_labels,
        eval_clean_labels=eval_clean_labels,
        eval_is_noisy=eval_is_noisy,
        eval_noisy_labels=eval_noisy_labels,
        eval_dataset_index=eval_dataset_index,
        results_dir=results_dir,
        device=device,
        seed=seed,
    )
    auroc_rows = eval_summary["auroc_rows"]
    clf_rows = eval_summary["clf_rows"]

    eval_protocol = {
        "architecture_invariant": True,
        "rationale": (
            "Eval indices are sampled from CIFAR-10N pools before training; "
            "all architectures at the same sweep point use the same seed, "
            "eval_per_group, and under_supported_classes (same design as "
            "uq_disentanglement: fixed test set, varying train UQ method)."
        ),
        "eval_per_group": eval_per_group,
        "groups": list(GROUP_NAMES.values()),
        "under_supported_classes": list(split_spec.under_supported_classes),
        "seed": seed,
    }
    signal_formulas = build_signal_formula_manifest(
        top_k=top_k,
        mc_passes=mc_passes,
        eval_protocol=eval_protocol,
    )

    summary = {
        "config": {
            "config_file": str(config_path),
            "seed": seed,
            "device": str(device),
            "data": vars(data_config),
            "model": model_config.dict(),
            "training": vars(training_config),
            "evaluation": vars(eval_config),
        },
        "under_supported_classes": split_spec.under_supported_classes,
        "train_size": len(train_dataset),
        "eval_sizes": {
            "clean": len(clean_eval_pack["clean_labels"]),
            "aleatoric_like": len(aleatoric_eval_pack["clean_labels"]),
            "epistemic_like": len(epistemic_eval_pack["clean_labels"]),
        },
        "eval_protocol": eval_protocol,
        "signal_formulas": signal_formulas,
        "one_vs_rest_auroc": [
            {
                "signal": name,
                "aleatoric_like_auroc": alea_auc,
                "epistemic_like_auroc": epis_auc,
            }
            for name, alea_auc, epis_auc in auroc_rows
        ],
        "macro_f1": [
            {
                "signal_set": name,
                "macro_f1": score,
            }
            for name, score in clf_rows
        ],
    }

    with (results_dir / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    from uqlab.run_artifacts import save_signal_formula_manifest

    save_signal_formula_manifest(results_dir, signal_formulas)

    # Save model checkpoint for watsonx.ai export
    # Remove any forward hooks before saving (DualXDA adds hooks that can't be pickled)
    model.eval()
    # Remove hooks from all modules
    for module in model.modules():
        module._forward_hooks.clear()
        module._forward_pre_hooks.clear()
        module._backward_hooks.clear()
    
    checkpoint = {
        'model': model,  # Full model object (hooks removed)
        'model_state_dict': model.state_dict(),  # Also save state_dict for flexibility
        'epoch': epochs,
        'loss': 0.0,  # Final loss not tracked in this script
        'config': {
            'hidden_dim': hidden_dim,
            'dropout': dropout,
            'num_classes': 10,
            'dinov2_model': dinov2_model,
        }
    }
    try:
        torch.save(checkpoint, results_dir / "checkpoint.pt")
        print(f"✅ Saved model checkpoint to {results_dir / 'checkpoint.pt'}")
    except Exception as exc:
        print(f"⚠️ Checkpoint save failed (training metrics still saved): {exc}")

    # Save complete results for watsonx.ai export
    results_data = {
        # Model outputs
        'predictions': uq["mean_prediction"].argmax(dim=1),
        'confidences': uq["mean_prediction"].max(dim=1).values,
        'mean_prediction_deterministic': mean_pred_det,
        
        # Training data
        'train_embeddings': getattr(train_dataset, 'features', None),
        'train_images': eval_inputs.new_empty((0,)) if not hasattr(train_dataset, 'features') else None,
        'train_labels': train_dataset.clean_labels,
        'train_noisy_labels': train_dataset.targets,
        'train_is_noisy': train_dataset.is_noisy,
        'train_indices': train_dataset.original_indices,
        
        # Evaluation data
        'eval_embeddings': eval_inputs if mode == "embeddings" else None,
        'eval_images': eval_inputs if mode == "images" else None,
        'eval_clean_labels': eval_clean_labels,
        'eval_noisy_labels': torch.cat([
            clean_eval_pack["noisy_labels"],
            aleatoric_eval_pack["noisy_labels"],
            epistemic_eval_pack["noisy_labels"],
        ], dim=0),
        'eval_is_noisy': eval_is_noisy,
        'eval_group_labels': eval_group_labels,
        'eval_indices': torch.cat([
            clean_eval_pack["original_indices"],
            aleatoric_eval_pack["original_indices"],
            epistemic_eval_pack["original_indices"],
        ], dim=0),
        
        # Uncertainty signals
        'signal_table': signal_table,
        
        # AUROC results
        'auroc_rows': auroc_rows,
    }
    try:
        torch.save(results_data, results_dir / "results.pt")
        print(f"✅ Saved results data to {results_dir / 'results.pt'}")
    except Exception as exc:
        print(f"⚠️ results.pt save failed (summary.json is available): {exc}")

    # Create a namespace object for backward compatibility with build_results_markdown
    config_ns = argparse.Namespace(
        noise_type=noise_type,
        under_supported_classes=under_supported_classes_str,
        under_train_per_class=under_train_per_class,
        regular_train_per_class=regular_train_per_class,
        eval_per_group=eval_per_group,
        dinov2_model=dinov2_model,
        hidden_dim=hidden_dim,
        dropout=dropout,
        epochs=epochs,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        train_batch_size=train_batch_size,
        feature_batch_size=feature_batch_size,
        mc_passes=mc_passes,
        top_k=top_k,
        seed=seed,
        device=device_str,
    )
    
    markdown = build_results_markdown(
        args=config_ns,
        split_spec=split_spec,
        train_size=len(train_dataset),
        eval_sizes=summary["eval_sizes"],
        auroc_rows=auroc_rows,
        clf_rows=clf_rows,
    )
    (results_dir / "summary.md").write_text(markdown)

    try:
        from uqlab.run_artifacts import metrics_row_from_run, print_run_metrics_summary

        print("\n" + "=" * 70)
        print("SIGNAL MEANS & AUROC (all uncertainties)")
        print("=" * 70)
        print_run_metrics_summary(metrics_row_from_run(results_dir))
    except ImportError:
        pass

    # Print summary - separate attribution-based from logit-based
    attribution_signals = ["inverse_coherence", "dominance"]
    logit_signals = ["inverse_mass", "inverse_logit_magnitude"]
    predictive_signals = ["msp_uncertainty", "predictive_entropy", "mutual_info"]
    
    print("\n" + "="*70)
    print("ATTRIBUTION-BASED SIGNALS (DualXDA)")
    print("="*70)
    attr_rows = [(n, a, e) for n, a, e in auroc_rows if n in attribution_signals]
    for name, alea_auc, epis_auc in sorted(attr_rows, key=lambda row: max(row[1], row[2]), reverse=True):
        print(f"  {name:<30} aleatoric={alea_auc:.4f}, epistemic={epis_auc:.4f}")
    
    print("\n" + "="*70)
    print("LOGIT-BASED SIGNALS (via Representer Theorem)")
    print("="*70)
    logit_rows = [(n, a, e) for n, a, e in auroc_rows if n in logit_signals]
    for name, alea_auc, epis_auc in sorted(logit_rows, key=lambda row: max(row[1], row[2]), reverse=True):
        print(f"  {name:<30} aleatoric={alea_auc:.4f}, epistemic={epis_auc:.4f}")
    
    print("\n" + "="*70)
    print("PREDICTIVE UNCERTAINTY BASELINE")
    print("="*70)
    pred_rows = [(n, a, e) for n, a, e in auroc_rows if n in predictive_signals]
    for name, alea_auc, epis_auc in pred_rows:
        print(f"  {name:<30} aleatoric={alea_auc:.4f}, epistemic={epis_auc:.4f}")

    print("\n3-way macro-F1:")
    for name, score in clf_rows:
        print(f"  {name}: {score:.4f}")

    # Rewrite summary.json last so the API always finds it after a successful run.
    with (results_dir / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSaved per-sample signals to: {results_dir / 'per_sample_signals.csv'}")
    print(f"Saved summary to: {results_dir / 'summary.json'} and {results_dir / 'summary.md'}")


if __name__ == "__main__":
    main()

# Made with Bob
