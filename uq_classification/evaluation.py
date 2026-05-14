"""
Evaluation metrics and result formatting for uncertainty classification.

Provides:
- Binary AUROC computation
- Confusion matrix and macro-F1 score
- 3-way signal classifier training
- Results formatting (Markdown, CSV)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn


def binary_auroc(scores: torch.Tensor, positives: torch.Tensor) -> float:
    """
    Calculate binary AUROC (Area Under ROC Curve).
    
    Computes the probability that a randomly chosen positive sample
    has a higher score than a randomly chosen negative sample.
    
    Args:
        scores: Uncertainty scores [N]
        positives: Boolean mask for positive class [N]
        
    Returns:
        AUROC value in [0, 1], or NaN if one class is empty
    """
    scores = scores.flatten().float()
    positives = positives.flatten().bool()
    pos_scores = scores[positives]
    neg_scores = scores[~positives]
    if pos_scores.numel() == 0 or neg_scores.numel() == 0:
        return float("nan")
    pairwise = (pos_scores[:, None] > neg_scores[None, :]).float()
    ties = (pos_scores[:, None] == neg_scores[None, :]).float() * 0.5
    return float((pairwise + ties).mean().item())


def confusion_matrix(num_classes: int, y_true: torch.Tensor, y_pred: torch.Tensor) -> torch.Tensor:
    """
    Compute confusion matrix.
    
    Args:
        num_classes: Number of classes
        y_true: True labels [N]
        y_pred: Predicted labels [N]
        
    Returns:
        Confusion matrix [num_classes, num_classes]
    """
    cm = torch.zeros((num_classes, num_classes), dtype=torch.long)
    for t, p in zip(y_true.long(), y_pred.long()):
        cm[int(t), int(p)] += 1
    return cm


def macro_f1(y_true: torch.Tensor, y_pred: torch.Tensor, num_classes: int) -> float:
    """
    Calculate macro-averaged F1 score.
    
    Computes F1 for each class independently, then averages.
    Gives equal weight to all classes regardless of support.
    
    Args:
        y_true: True labels [N]
        y_pred: Predicted labels [N]
        num_classes: Number of classes
        
    Returns:
        Macro-averaged F1 score
    """
    cm = confusion_matrix(num_classes, y_true, y_pred).float()
    f1s = []
    for c in range(num_classes):
        tp = cm[c, c]
        fp = cm[:, c].sum() - tp
        fn = cm[c, :].sum() - tp
        denom = (2 * tp + fp + fn).item()
        if denom == 0:
            f1s.append(0.0)
        else:
            f1s.append(float((2 * tp / (2 * tp + fp + fn)).item()))
    return float(sum(f1s) / len(f1s))


def standardize(train_x: torch.Tensor, test_x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Standardize features using training set statistics.
    
    Args:
        train_x: Training features [N_train, D]
        test_x: Test features [N_test, D]
        
    Returns:
        Tuple of (standardized_train, standardized_test)
    """
    mean = train_x.mean(dim=0, keepdim=True)
    std = train_x.std(dim=0, keepdim=True).clamp_min(1e-6)
    return (train_x - mean) / std, (test_x - mean) / std


def train_signal_classifier(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    *,
    device: torch.device,
    epochs: int = 300,
    learning_rate: float = 0.05,
) -> torch.Tensor:
    """
    Train a simple linear classifier on uncertainty signals.
    
    Used to evaluate how well different signal combinations can
    distinguish between clean, aleatoric, and epistemic samples.
    
    Args:
        x_train: Training features [N_train, D]
        y_train: Training labels [N_train]
        x_test: Test features [N_test, D]
        device: Device to train on
        epochs: Number of training epochs
        learning_rate: Learning rate
        
    Returns:
        Predicted labels for test set [N_test]
    """
    x_train, x_test = standardize(x_train, x_test)
    model = nn.Linear(int(x_train.shape[1]), int(y_train.max().item()) + 1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    x_train = x_train.to(device)
    y_train = y_train.to(device)
    x_test = x_test.to(device)

    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(x_train)
        loss = criterion(logits, y_train)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        preds = model(x_test).argmax(dim=1).cpu()
    return preds


def split_group_balanced_targets(
    y: torch.Tensor, 
    seed: int, 
    train_fraction: float = 0.5
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Split data into train/test with balanced class distribution.
    
    Ensures each class has the same train/test split ratio.
    
    Args:
        y: Labels [N]
        seed: Random seed
        train_fraction: Fraction of data for training
        
    Returns:
        Tuple of (train_indices, test_indices)
    """
    rng = np.random.default_rng(seed)
    train_idx: List[int] = []
    test_idx: List[int] = []
    for cls in sorted(set(int(v) for v in y.tolist())):
        cls_idx = np.where(y.numpy() == cls)[0]
        rng.shuffle(cls_idx)
        cut = max(1, int(len(cls_idx) * train_fraction))
        train_idx.extend(cls_idx[:cut].tolist())
        test_idx.extend(cls_idx[cut:].tolist())
    return torch.as_tensor(train_idx, dtype=torch.long), torch.as_tensor(test_idx, dtype=torch.long)


def evaluate_three_way_classification(
    signal_table: Dict[str, torch.Tensor],
    eval_group_labels: torch.Tensor,
    device: torch.device,
    seed: int,
    train_fraction: float = 0.5,
) -> List[Tuple[str, float]]:
    """
    Evaluate three-way classification (clean/aleatoric/epistemic) using different signal combinations.
    
    Trains simple linear classifiers on different signal subsets and evaluates
    their ability to distinguish between uncertainty types.
    
    Args:
        signal_table: Dictionary of uncertainty signals
        eval_group_labels: Ground truth group labels [N]
        device: Device to train on
        seed: Random seed for train/test split
        train_fraction: Fraction of data for training
        
    Returns:
        List of (signal_set_name, macro_f1_score) tuples
    """
    # Build signal matrices for different combinations
    signal_matrix_predictive = torch.stack(
        [
            signal_table["msp_uncertainty"],
            signal_table["predictive_entropy"],
            signal_table["mutual_info"],
        ],
        dim=1,
    )
    
    # Build attribution signal matrix from available signals only
    attribution_signals = []
    
    # Core attribution signals (should always be present)
    if "inverse_coherence" in signal_table:
        attribution_signals.append(signal_table["inverse_coherence"])
    if "dominance" in signal_table:
        attribution_signals.append(signal_table["dominance"])
    
    # Logit-based signals (via Representer Theorem)
    if "inverse_mass" in signal_table:
        attribution_signals.append(signal_table["inverse_mass"])
    if "inverse_logit_magnitude" in signal_table:
        attribution_signals.append(signal_table["inverse_logit_magnitude"])
    
    # Stack if we have any attribution signals
    if attribution_signals:
        signal_matrix_attribution = torch.stack(attribution_signals, dim=1)
    else:
        # Fallback: use zeros if no attribution signals
        signal_matrix_attribution = torch.zeros((len(eval_group_labels), 1))
    
    signal_matrix_combined = torch.cat([signal_matrix_predictive, signal_matrix_attribution], dim=1)
    
    # Optional: Add compound signal if available
    if "compound_uncertainty" in signal_table:
        signal_matrix_enhanced = torch.cat(
            [signal_matrix_combined, signal_table["compound_uncertainty"].unsqueeze(1)],
            dim=1,
        )
        signal_sets = [
            ("predictive_only", signal_matrix_predictive),
            ("attribution_only", signal_matrix_attribution),
            ("combined", signal_matrix_combined),
            ("enhanced_with_hybrid", signal_matrix_enhanced),
        ]
    else:
        signal_sets = [
            ("predictive_only", signal_matrix_predictive),
            ("attribution_only", signal_matrix_attribution),
            ("combined", signal_matrix_combined),
        ]
    
    # Split data into train/test with balanced classes
    clf_train_idx, clf_test_idx = split_group_balanced_targets(
        eval_group_labels,
        seed=seed + 1,
        train_fraction=train_fraction
    )
    
    # Train and evaluate classifiers
    results = []
    for name, signal_matrix in signal_sets:
        preds = train_signal_classifier(
            signal_matrix[clf_train_idx],
            eval_group_labels[clf_train_idx],
            signal_matrix[clf_test_idx],
            device=device,
        )
        score = macro_f1(eval_group_labels[clf_test_idx], preds, num_classes=3)
        results.append((name, score))
    
    return results


def build_results_markdown(
    *,
    args: argparse.Namespace,
    split_spec,
    train_size: int,
    eval_sizes: Dict[str, int],
    auroc_rows: List[Tuple[str, float, float]],
    clf_rows: List[Tuple[str, float]],
) -> str:
    """
    Build a Markdown summary of experiment results.
    
    Args:
        args: Command-line arguments
        split_spec: Data split specification
        train_size: Number of training samples
        eval_sizes: Dictionary of evaluation set sizes
        auroc_rows: List of (signal_name, aleatoric_auroc, epistemic_auroc)
        clf_rows: List of (signal_set_name, macro_f1)
        
    Returns:
        Markdown-formatted results string
    """
    lines = [
        "# Fast Uncertainty Classification Results",
        "",
        "## Setup",
        f"- Noise type: `{args.noise_type}`",
        f"- Under-supported classes: `{split_spec.under_supported_classes}`",
        f"- Train size: `{train_size}`",
        f"- Eval clean: `{eval_sizes['clean']}`",
        f"- Eval aleatoric-like: `{eval_sizes['aleatoric_like']}`",
        f"- Eval epistemic-like: `{eval_sizes['epistemic_like']}`",
        f"- DINOv2 backbone: `{args.dinov2_model}`",
        "",
        "## One-vs-Rest AUROC",
        "",
        "| Signal | Aleatoric-like AUROC | Epistemic-like AUROC |",
        "| --- | ---: | ---: |",
    ]
    for name, alea_auc, epis_auc in auroc_rows:
        lines.append(f"| {name} | {alea_auc:.4f} | {epis_auc:.4f} |")

    lines.extend(
        [
            "",
            "## 3-Way Signal Classifier",
            "",
            "| Signal set | Macro-F1 |",
            "| --- | ---: |",
        ]
    )
    for name, score in clf_rows:
        lines.append(f"| {name} | {score:.4f} |")

    return "\n".join(lines) + "\n"


def save_per_sample_csv(
    output_path: Path,
    eval_group_labels: torch.Tensor,
    eval_clean_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    signal_table: Dict[str, torch.Tensor],
    group_names: Dict[int, str],
) -> None:
    """
    Save per-sample signals to CSV file.
    
    Args:
        output_path: Path to output CSV file
        eval_group_labels: Group labels (clean/aleatoric/epistemic) [N]
        eval_clean_labels: Ground truth class labels [N]
        eval_is_noisy: Boolean mask for noisy samples [N]
        signal_table: Dictionary of signal tensors
        group_names: Mapping from group ID to name
    """
    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        header = ["group", "clean_label", "is_noisy"] + list(signal_table.keys())
        writer.writerow(header)
        
        # Data rows
        for i in range(int(eval_group_labels.shape[0])):
            row = [
                group_names[int(eval_group_labels[i].item())],
                int(eval_clean_labels[i].item()),
                bool(eval_is_noisy[i].item()),
            ]
            for signal_name in signal_table.keys():
                row.append(float(signal_table[signal_name][i].item()))
            writer.writerow(row)

# Made with Bob
