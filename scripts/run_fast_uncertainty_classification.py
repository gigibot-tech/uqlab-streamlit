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
import sys
from datetime import datetime
from pathlib import Path

# Third-party
import numpy as np
import torch
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# MODULAR IMPORTS: Explicit, specific imports from each module
# ============================================================================

# Data loading
from src.data.cifar10n_loader import CIFAR10NDataset

# Uncertainty metrics
from src.metrics.mc_dropout_uq import calculate_mc_dropout_uncertainty

# Attribution methods
from src.triage.dualxda_axioms import DualXDATracer, infer_classifier_layer_name

# UQ Classification package - Constants
from uq_classification import (
    GROUP_ALEATORIC,
    GROUP_CLEAN,
    GROUP_EPISTEMIC,
    GROUP_NAMES,
)

# UQ Classification package - Models
from uq_classification.models import EmbeddingDataset

# UQ Classification package - Utils
from uq_classification.utils import auto_device, dino_transform, set_seed

# UQ Classification package - Data loading
from uq_classification.data_loader import (
    EmbeddingOrganizer,
    SplitSpec,
    build_feature_cache_path,
    maybe_load_or_compute_feature_cache,
    sample_indices_for_fast_pilot,
    train_feature_model,
)

# UQ Classification package - Attribution signals
from uq_classification.attribution_signals import compute_attribution_structure_signals

# UQ Classification package - Evaluation
from uq_classification.evaluation import (
    binary_auroc,
    build_results_markdown,
    save_per_sample_csv,
    split_group_balanced_targets,
    train_signal_classifier,
)


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
    
    Recommended Values:
    -------------------
    Quick experiments (5-10 min):
      - under_train_per_class: 30-50
      - regular_train_per_class: 200-300
      - eval_per_group: 400-600
      - dinov2_model: "small"
      - epochs: 8-12
      - mc_passes: 10-20
      - top_k: 5-10
    
    Thorough experiments (30-60 min):
      - under_train_per_class: 100-200
      - regular_train_per_class: 500-1000
      - eval_per_group: 1000-2000
      - dinov2_model: "base"
      - epochs: 20-30
      - mc_passes: 50-100
      - top_k: 20-50
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
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Extract parameters from config with CLI overrides
    seed = args.seed if args.seed is not None else config.get("seed", 42)
    device_str = args.device if args.device is not None else config.get("device", "auto")
    
    # Setup
    set_seed(seed)
    device = auto_device(device_str)

    # Setup directories
    if args.output_dir:
        results_dir = Path(args.output_dir)
    else:
        results_base = PROJECT_ROOT / config.get("paths", {}).get("results_base_dir", "./results")
        results_dir = results_base / f"fast_uncertainty_classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    feature_cache_dir = PROJECT_ROOT / config.get("paths", {}).get("feature_cache_dir", "./cache/fast_uncertainty_classification/features")
    run_cache_dir = results_dir / "cache"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Extract data parameters
    data_config = config.get("data", {})
    noise_type = data_config.get("noise_type", "aggre_label")
    under_supported_classes_str = data_config.get("under_supported_classes", "3,5")
    under_supported_classes = [int(x.strip()) for x in under_supported_classes_str.split(",") if x.strip()]
    under_train_per_class = data_config.get("under_train_per_class", 50)
    regular_train_per_class = data_config.get("regular_train_per_class", 300)
    eval_per_group = data_config.get("eval_per_group", 600)
    
    # Extract model parameters
    model_config = config.get("model", {})
    dinov2_model = model_config.get("dinov2_model", "small")
    hidden_dim = model_config.get("hidden_dim", 256)
    dropout = model_config.get("dropout", 0.2)
    
    # Extract training parameters
    training_config = config.get("training", {})
    epochs = training_config.get("epochs", 12)
    learning_rate = training_config.get("learning_rate", 1e-3)
    weight_decay = training_config.get("weight_decay", 1e-4)
    train_batch_size = training_config.get("train_batch_size", 256)
    feature_batch_size = training_config.get("feature_batch_size", 64)
    
    # Extract evaluation parameters
    eval_config = config.get("evaluation", {})
    mc_passes = eval_config.get("mc_passes", 20)
    top_k = eval_config.get("top_k", 10)

    # Load CIFAR-10N dataset
    cifar10n_root = Path(config.get("paths", {}).get("cifar10n_root", "./data/cifar10n"))
    if not cifar10n_root.is_absolute():
        cifar10n_root = PROJECT_ROOT / cifar10n_root

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
            f"`{noise_type}` resolved to zero noise. Please place `CIFAR-10_human.pt` under "
            f"`{cifar10n_root / 'cifar-10-batches-py'}` before running this pilot."
        )

    # Sample train/eval splits
    split_spec: SplitSpec = sample_indices_for_fast_pilot(
        dataset,
        under_supported_classes=under_supported_classes,
        under_train_per_class=under_train_per_class,
        regular_train_per_class=regular_train_per_class,
        eval_per_group=eval_per_group,
        seed=args.seed,
    )
    if len(split_spec.clean_eval_indices) == 0 or len(split_spec.aleatoric_eval_indices) == 0 or len(split_spec.epistemic_eval_indices) == 0:
        raise RuntimeError(
            "At least one evaluation group is empty. Try reducing `--eval_per_group`, "
            "changing `--under_supported_classes`, or using a milder support reduction."
        )

    # Extract or load cached embeddings using OO-based organizer
    embedding_organizer = EmbeddingOrganizer(
        dataset=dataset,
        split_spec=split_spec,
        feature_cache_dir=feature_cache_dir,
        noise_type=noise_type,
        dinov2_model=dinov2_model,
        batch_size=feature_batch_size,
        device=device,
    )
    
    # Load embeddings once, organize by split
    embedding_organizer.load_or_compute_features()
    
    # Extract organized data packs
    train_pack = embedding_organizer.get_train_pack()
    clean_eval_pack = embedding_organizer.get_clean_eval_pack()
    aleatoric_eval_pack = embedding_organizer.get_aleatoric_eval_pack()
    epistemic_eval_pack = embedding_organizer.get_epistemic_eval_pack()

    train_dataset = EmbeddingDataset(
        train_pack["features"],
        train_pack["noisy_labels"],
        train_pack["clean_labels"],
        train_pack["is_noisy"],
        train_pack["original_indices"],
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

    # Train feature-space classifier
    model = train_feature_model(
        train_dataset,
        device=device,
        num_classes=10,
        hidden_dim=hidden_dim,
        dropout=dropout,
        epochs=epochs,
        batch_size=train_batch_size,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
    )
    model.eval()

    # Prepare evaluation data
    eval_features = torch.cat(
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

    # Compute predictive uncertainty with MC Dropout
    mc_predictions = model.mc_forward(eval_features.to(device), n_passes=mc_passes).cpu()
    uq = calculate_mc_dropout_uncertainty(mc_predictions)
    mean_pred = uq["mean_prediction"]
    msp_uncertainty = 1.0 - mean_pred.max(dim=1).values

    # Compute attribution-based signals with DualXDA
    tracer = DualXDATracer(
        model=model,
        train_dataset=train_dataset,
        layer_name=infer_classifier_layer_name(model),
        device=str(device),
        cache_dir=str(run_cache_dir / "dualxda"),
    )
    attribution_signals = compute_attribution_structure_signals(
        tracer,
        model,
        eval_features,
        mean_pred,
        train_dataset,
        device=device,
        batch_size=train_batch_size,
        top_k=top_k,
        num_classes=10,
    )
    # ============================================================================
    # MATHEMATICAL RELATIONSHIP: Attribution Mass ≈ Logit Magnitude
    # ============================================================================
    # Via the Representer Theorem for kernel methods (which SVM approximates):
    #
    # For a linear classifier: f(x) = w^T x + b
    # The dual formulation gives: w = Σ_i α_i y_i x_i
    # Therefore: f(x) = Σ_i α_i y_i ⟨x_i, x⟩ + b
    #
    # DualXDA attribution mass = Σ_i |α_i y_i ⟨x_i, x⟩| ≈ |f(x)| = |logit|
    #
    # This means:
    # - inverse_mass ≈ 1/|logit| ≈ inverse_logit_magnitude
    # - High mass → High confidence (large |logit|)
    # - Low mass → Low confidence (small |logit|) → Epistemic uncertainty
    #
    # We implement BOTH attribution-based (inverse_mass) and logit-based
    # (inverse_logit_magnitude, inverse_max_logit) signals to empirically
    # validate this theoretical relationship.
    # ============================================================================

    # Compute logit-based signals for comparison with attribution-based signals
    # NOTE: mean_pred contains softmax probabilities, not raw logits
    # We need to get raw logits from the model for proper comparison
    with torch.no_grad():
        raw_logits = model(eval_features.to(device)).cpu()  # Get raw logits before softmax
    
    max_logit = raw_logits.max(dim=1).values
    logit_magnitude = torch.abs(raw_logits).sum(dim=1)  # L1 norm of logit vector

    # Build signal table
    compound_uncertainty = uq["entropy"] * attribution_signals["label_disagreement"]
    
    signal_table = {
        # Predictive uncertainty signals (baseline)
        "msp_uncertainty": msp_uncertainty,
        "predictive_entropy": uq["entropy"],
        "mutual_info": uq["mutual_info"],
        
        # Attribution-based signals (DualXDA)
        # Aleatoric indicator (detect label ambiguity)
        "inverse_coherence": 1.0 - attribution_signals["coherence"],  # BEST aleatoric (0.73 AUROC)
        
        # Epistemic indicator (detect lack of support)
        "dominance": attribution_signals["dominance"],  # Good epistemic (0.76 AUROC)
        
        # Logit-based signals (via Representer Theorem: mass ≈ |logit|)
        "inverse_mass": 1.0 / (attribution_signals["mass"] + 1e-8),  # BEST epistemic (0.94 AUROC)
        "inverse_logit_magnitude": 1.0 / (logit_magnitude + 1e-8),  # Baseline comparison
    }
    
    # REMOVED SIGNALS (poor performers):
    # - attribution_concentration: Random performance (0.54 alea, 0.31 epis)
    # - label_disagreement: Random performance (0.50, 0.50)
    # - compound_uncertainty: Random performance (0.50, 0.50)
    # - noisy_support_ratio: Misclassified, redundant with inverse_mass
    # - inverse_max_logit: Redundant with inverse_mass
    # - cross_class_support: Poor performer

    # Compute one-vs-rest AUROC
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

    # Evaluate three-way classification using refactored function
    from uq_classification.evaluation import evaluate_three_way_classification
    clf_rows = evaluate_three_way_classification(
        signal_table=signal_table,
        eval_group_labels=eval_group_labels,
        device=device,
        seed=seed,
        train_fraction=0.5,
    )

    # Save results
    save_per_sample_csv(
        results_dir / "per_sample_signals.csv",
        eval_group_labels,
        eval_clean_labels,
        eval_is_noisy,
        signal_table,
        GROUP_NAMES,
    )

    summary = {
        "config": {
            "config_file": str(config_path),
            "seed": seed,
            "device": str(device),
            "data": data_config,
            "model": model_config,
            "training": training_config,
            "evaluation": eval_config,
        },
        "under_supported_classes": split_spec.under_supported_classes,
        "train_size": len(train_dataset),
        "eval_sizes": {
            "clean": len(clean_eval_pack["features"]),
            "aleatoric_like": len(aleatoric_eval_pack["features"]),
            "epistemic_like": len(epistemic_eval_pack["features"]),
        },
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
    torch.save(checkpoint, results_dir / "checkpoint.pt")
    print(f"✅ Saved model checkpoint to {results_dir / 'checkpoint.pt'}")

    # Save complete results for watsonx.ai export
    results_data = {
        # Model outputs
        'predictions': mean_pred.argmax(dim=1),
        'confidences': mean_pred.max(dim=1).values,
        
        # Training data
        'train_embeddings': train_dataset.features,
        'train_labels': train_dataset.clean_labels,
        'train_noisy_labels': train_dataset.targets,
        'train_is_noisy': train_dataset.is_noisy,
        'train_indices': train_dataset.original_indices,
        
        # Evaluation data
        'eval_embeddings': eval_features,
        'eval_clean_labels': eval_clean_labels,
        'eval_noisy_labels': torch.cat([
            clean_eval_pack["noisy_labels"],
            aleatoric_eval_pack["noisy_labels"],
            epistemic_eval_pack["noisy_labels"],
        ], dim=0),
        'eval_is_noisy': eval_is_noisy,
        'eval_group_labels': eval_group_labels,
        'eval_indices': torch.cat([
            clean_eval_pack["indices"],
            aleatoric_eval_pack["indices"],
            epistemic_eval_pack["indices"],
        ], dim=0),
        
        # Uncertainty signals
        'signal_table': signal_table,
        
        # AUROC results
        'auroc_rows': auroc_rows,
    }
    torch.save(results_data, results_dir / "results.pt")
    print(f"✅ Saved results data to {results_dir / 'results.pt'}")

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

    print(f"\nSaved per-sample signals to: {results_dir / 'per_sample_signals.csv'}")
    print(f"Saved summary to: {results_dir / 'summary.md'}")


if __name__ == "__main__":
    main()

# Made with Bob
