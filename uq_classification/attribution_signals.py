"""
Attribution-based uncertainty signal computation.

Computes various signals from DualXDA attribution traces to distinguish
between aleatoric and epistemic uncertainty:

STANDARD DualXDA METRICS:
- Mass: Sum of absolute attribution magnitudes
- Coherence: Ratio of signed sum to absolute sum  
- Dominance: Maximum attribution relative to total mass

SEMANTIC SIGNALS (Aleatoric indicators):
- Label disagreement: Entropy of supporter labels
- Noisy support ratio: Fraction of supporters with noisy labels
- Cross-class support: Fraction of supporters from different classes

STRUCTURAL SIGNALS (Epistemic indicators):
- Attribution concentration: Gini coefficient of attribution magnitudes

MATHEMATICAL FOUNDATION - Representer Theorem:
-----------------------------------------------
For linear classifiers with dual formulation:
    f(x) = Σ_i α_i y_i ⟨x_i, x⟩ + b

DualXDA attribution mass = Σ_i |α_i y_i ⟨x_i, x⟩| ≈ |f(x)| = |logit|

This means:
- High mass ≈ High |logit| → High confidence
- Low mass ≈ Low |logit| → Low confidence → Epistemic uncertainty
- inverse_mass ≈ 1/|logit| ≈ inverse_msp (for max logit)

The attribution-based signals provide interpretable, sample-level explanations
while being mathematically equivalent to logit-based confidence measures.
"""

from __future__ import annotations

import math
from typing import Dict, List

import torch

from src.triage.dualxda_axioms import DualXDATracer


def normalized_entropy_from_labels(labels: torch.Tensor, num_classes: int) -> float:
    """
    Calculate normalized entropy of a label distribution.
    
    Normalized entropy is in [0, 1] where:
    - 0 = all labels are the same (no uncertainty)
    - 1 = uniform distribution (maximum uncertainty)
    
    Args:
        labels: Label tensor [N]
        num_classes: Total number of classes
        
    Returns:
        Normalized entropy value in [0, 1]
    """
    counts = torch.bincount(labels.long(), minlength=num_classes).float()
    probs = counts / counts.sum().clamp_min(1.0)
    mask = probs > 0
    entropy = -(probs[mask] * torch.log(probs[mask])).sum()
    return float((entropy / math.log(num_classes)).item()) if num_classes > 1 else 0.0


@torch.no_grad()
def compute_attribution_structure_signals(
    tracer: DualXDATracer,
    model,
    eval_features: torch.Tensor,
    mean_predictions: torch.Tensor,
    train_dataset,
    *,
    device: torch.device,
    batch_size: int,
    top_k: int,
    num_classes: int,
) -> Dict[str, torch.Tensor]:
    """
    Compute attribution-based uncertainty signals using DualXDA.
    
    For each evaluation sample, computes:
    
    Standard DualXDA metrics:
    - mass: Sum of absolute attribution magnitudes
    - coherence: Ratio of signed sum to absolute sum
    - dominance: Maximum attribution relative to total mass
    
    Label-based signals:
    - label_disagreement: Entropy of supporter labels (aleatoric indicator)
    - noisy_support_ratio: Fraction of supporters with noisy labels
    
    NEW signals for better uncertainty distinction:
    - attribution_concentration: Gini coefficient of attribution magnitudes
      (High = dominated by few samples → epistemic)
    - cross_class_support: Fraction of supporters from different classes
      (High = cross-class conflict → aleatoric)
    
    Args:
        tracer: DualXDA tracer instance
        model: Trained classifier model
        eval_features: Evaluation features [N, feature_dim]
        mean_predictions: Mean predictions [N, num_classes]
        train_dataset: Training dataset with labels and noise info
        device: Device to run on
        batch_size: Batch size for processing
        top_k: Number of top supporters to analyze
        num_classes: Number of classes used to normalize label entropy
        
    Returns:
        Dictionary of signal tensors, each of shape [N]
    """
    from src.triage.dualxda_axioms import infer_classifier_layer_name
    
    layer_name = infer_classifier_layer_name(model)
    print(f"Using DualXDA classifier layer: {layer_name}")

    train_labels = train_dataset.targets
    train_is_noisy = train_dataset.is_noisy

    out = {
        "mass": [],
        "coherence": [],
        "dominance": [],
        "label_disagreement": [],
        "noisy_support_ratio": [],
        "attribution_concentration": [],
        "cross_class_support": [],
    }

    for start in range(0, int(eval_features.shape[0]), batch_size):
        end = min(start + batch_size, int(eval_features.shape[0]))
        xb = eval_features[start:end].to(device)
        targets = mean_predictions[start:end].argmax(dim=1).to(device)
        
        # Get DualXDA attributions
        attr = tracer.traces(x=xb, targets=targets, drop_zero_columns=False)
        tri = tracer.triage(attr, targets=targets)

        out["mass"].append(tri["mass"].detach().cpu())
        out["coherence"].append(tri["coherence"].detach().cpu())
        out["dominance"].append(tri["dominance"].detach().cpu())

        batch_disagreement: List[float] = []
        batch_noisy_ratio: List[float] = []
        batch_attribution_concentration: List[float] = []
        batch_cross_class_support: List[float] = []

        for row in range(int(attr.shape[0])):
            row_attr = attr[row].detach().cpu()
            predicted_class = int(targets[row].item())
            pos_idx = torch.nonzero(row_attr > 0, as_tuple=False).view(-1)
            
            if pos_idx.numel() == 0:
                # No positive attributions - use default values
                batch_disagreement.append(0.0)
                batch_noisy_ratio.append(0.0)
                batch_attribution_concentration.append(0.0)
                batch_cross_class_support.append(0.0)
                continue

            pos_vals = row_attr[pos_idx]
            k = min(top_k, int(pos_idx.numel()))
            _, top_sub = torch.topk(pos_vals, k)
            top_idx = pos_idx[top_sub]
            top_vals = pos_vals[top_sub]

            supporter_labels = train_labels[top_idx]
            supporter_noisy = train_is_noisy[top_idx].float()
            
            # Existing signals
            batch_disagreement.append(normalized_entropy_from_labels(supporter_labels, num_classes))
            batch_noisy_ratio.append(float(supporter_noisy.mean().item()))
            
            # NEW: Attribution concentration - Gini coefficient of attribution magnitudes
            # High concentration = dominated by few samples (epistemic uncertainty)
            sorted_vals, _ = torch.sort(top_vals)
            n = len(sorted_vals)
            cumsum = torch.cumsum(sorted_vals, dim=0)
            gini = (2.0 * torch.arange(1, n + 1, dtype=torch.float32) * sorted_vals).sum()
            gini = gini / (n * cumsum[-1]) - (n + 1) / n
            batch_attribution_concentration.append(float(gini.item()))
            
            # NEW: Cross-class support - fraction of supporters from different classes than prediction
            # High cross-class support indicates training data conflict (aleatoric uncertainty)
            cross_class_mask = supporter_labels != predicted_class
            cross_class_fraction = float(cross_class_mask.float().mean().item())
            batch_cross_class_support.append(cross_class_fraction)

        out["label_disagreement"].append(torch.tensor(batch_disagreement, dtype=torch.float32))
        out["noisy_support_ratio"].append(torch.tensor(batch_noisy_ratio, dtype=torch.float32))
        out["attribution_concentration"].append(torch.tensor(batch_attribution_concentration, dtype=torch.float32))
        out["cross_class_support"].append(torch.tensor(batch_cross_class_support, dtype=torch.float32))

    return {k: torch.cat(v, dim=0) for k, v in out.items()}

# Made with Bob
