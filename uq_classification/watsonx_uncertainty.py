"""
Compute full uncertainty classification signals from watsonx.ai predictions.

This module takes predictions from watsonx.ai and computes all 7 uncertainty signals
(epistemic, aleatoric, hybrid) just like the local Streamlit pipeline.

Functions:
    compute_uncertainty_signals: Calculate all 7 UQ signals from predictions
    evaluate_watsonx_deployment: Full evaluation pipeline for deployed model
    compare_local_vs_watsonx: Validate deployment matches local results
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn.functional as F


def compute_predictive_signals(
    mc_predictions: torch.Tensor,
) -> Dict[str, torch.Tensor]:
    """
    Compute predictive uncertainty signals from MC Dropout predictions.
    
    Args:
        mc_predictions: Stacked predictions [mc_passes, N, num_classes]
        
    Returns:
        Dictionary with:
        - msp_uncertainty: 1 - max(mean_probs)
        - predictive_entropy: H(mean_probs)
        - mutual_info: I(y;θ|x) = H(mean) - E[H(samples)]
    """
    # Mean predictions across MC passes
    mean_probs = mc_predictions.mean(dim=0)  # [N, num_classes]
    
    # MSP uncertainty: 1 - max(p)
    max_probs, _ = mean_probs.max(dim=1)
    msp_uncertainty = 1.0 - max_probs
    
    # Predictive entropy: H(p) = -Σ p_i log(p_i)
    eps = 1e-10
    predictive_entropy = -(mean_probs * torch.log(mean_probs + eps)).sum(dim=1)
    
    # Mutual information: I(y;θ|x) = H(p) - E[H(p|θ)]
    # Expected entropy across MC samples
    sample_entropies = -(mc_predictions * torch.log(mc_predictions + eps)).sum(dim=2)
    expected_entropy = sample_entropies.mean(dim=0)
    mutual_info = predictive_entropy - expected_entropy
    
    return {
        "msp_uncertainty": msp_uncertainty,
        "predictive_entropy": predictive_entropy,
        "mutual_info": mutual_info,
    }


def compute_attribution_signals(
    logits: torch.Tensor,
    embeddings: torch.Tensor,
    train_embeddings: Optional[torch.Tensor] = None,
    train_labels: Optional[torch.Tensor] = None,
) -> Dict[str, torch.Tensor]:
    """
    Compute attribution-based uncertainty signals.
    
    **IMPORTANT:** Full attribution signals require training data access.
    Without training data, this provides APPROXIMATIONS based on logits only.
    
    For accurate attribution signals, you need:
    - train_embeddings: Training set embeddings [N_train, 768]
    - train_labels: Training set labels [N_train]
    
    Then use DualXDA's Representer Theorem to compute true attributions.
    
    Args:
        logits: Model logits [N, num_classes]
        embeddings: Input embeddings [N, 768]
        train_embeddings: Optional training embeddings for true attributions
        train_labels: Optional training labels for true attributions
        
    Returns:
        Dictionary with:
        - inverse_coherence: 1 / (1 + coherence) [APPROXIMATION without training data]
        - dominance: max_attr / mean_attr [APPROXIMATION without training data]
        - inverse_mass: 1 / total_attribution [APPROXIMATION without training data]
        - inverse_logit_magnitude: 1 / ||logits|| [EXACT]
    """
    if train_embeddings is not None and train_labels is not None:
        # TODO: Implement true DualXDA attribution computation
        # This requires:
        # 1. Load trained model weights
        # 2. Compute influence of each training sample on test predictions
        # 3. Use Representer Theorem for attribution scores
        raise NotImplementedError(
            "True attribution computation with training data not yet implemented. "
            "Use local Streamlit pipeline for accurate attribution signals."
        )
    
    # APPROXIMATIONS (without training data)
    # These are rough estimates based on logit patterns only
    
    # Logit-based signals (EXACT)
    logit_norms = torch.norm(logits, dim=1)  # [N]
    inverse_logit_magnitude = 1.0 / (logit_norms + 1e-6)
    
    # Embedding-based approximation (ROUGH)
    embedding_norms = torch.norm(embeddings, dim=1)  # [N]
    
    # Approximate attribution mass (ROUGH)
    attribution_mass = logit_norms * embedding_norms
    inverse_mass = 1.0 / (attribution_mass + 1e-6)
    
    # Approximate coherence (ROUGH)
    # Higher logit variance = lower coherence
    logit_std = logits.std(dim=1)
    logit_mean = logits.abs().mean(dim=1)
    coherence = 1.0 / (1.0 + logit_std / (logit_mean + 1e-6))
    inverse_coherence = 1.0 / (coherence + 1e-6)
    
    # Approximate dominance (ROUGH)
    max_logits, _ = logits.abs().max(dim=1)
    mean_logits = logits.abs().mean(dim=1)
    dominance = max_logits / (mean_logits + 1e-6)
    
    return {
        "inverse_coherence": inverse_coherence,  # APPROXIMATION
        "dominance": dominance,  # APPROXIMATION
        "inverse_mass": inverse_mass,  # APPROXIMATION
        "inverse_logit_magnitude": inverse_logit_magnitude,  # EXACT
    }


def compute_compound_uncertainty(
    predictive_signals: Dict[str, torch.Tensor],
    attribution_signals: Dict[str, torch.Tensor],
    weights: Optional[Dict[str, float]] = None,
) -> torch.Tensor:
    """
    Compute compound uncertainty score from all signals.
    
    Args:
        predictive_signals: Predictive uncertainty signals
        attribution_signals: Attribution-based signals
        weights: Optional weights for each signal (default: equal)
        
    Returns:
        Compound uncertainty score [N]
    """
    if weights is None:
        # Default: equal weights
        weights = {
            "msp_uncertainty": 1.0,
            "predictive_entropy": 1.0,
            "mutual_info": 1.0,
            "inverse_coherence": 1.0,
            "dominance": 1.0,
            "inverse_mass": 1.0,
            "inverse_logit_magnitude": 1.0,
        }
    
    # Normalize each signal to [0, 1]
    all_signals = {**predictive_signals, **attribution_signals}
    normalized = {}
    
    for name, signal in all_signals.items():
        min_val = signal.min()
        max_val = signal.max()
        if max_val > min_val:
            normalized[name] = (signal - min_val) / (max_val - min_val)
        else:
            normalized[name] = torch.zeros_like(signal)
    
    # Weighted sum
    compound = torch.zeros_like(list(normalized.values())[0])
    total_weight = 0.0
    
    for name, signal in normalized.items():
        weight = weights.get(name, 1.0)
        compound += weight * signal
        total_weight += weight
    
    compound /= total_weight
    
    return compound


def compute_uncertainty_signals(
    mc_predictions: torch.Tensor,
    embeddings: torch.Tensor,
    logits: Optional[torch.Tensor] = None,
) -> Dict[str, torch.Tensor]:
    """
    Compute all 7 uncertainty signals from watsonx.ai predictions.
    
    This replicates the full Streamlit evaluation pipeline.
    
    Args:
        mc_predictions: MC Dropout predictions [mc_passes, N, num_classes]
        embeddings: Input embeddings [N, 768]
        logits: Optional logits [N, num_classes] (if not provided, computed from mean probs)
        
    Returns:
        Dictionary with all 7 signals:
        - msp_uncertainty (aleatoric)
        - predictive_entropy (aleatoric)
        - mutual_info (epistemic)
        - inverse_coherence (epistemic)
        - dominance (epistemic)
        - inverse_mass (hybrid)
        - inverse_logit_magnitude (hybrid)
        - compound_uncertainty (combined)
    """
    # Compute predictive signals
    predictive_signals = compute_predictive_signals(mc_predictions)
    
    # Compute logits if not provided
    if logits is None:
        mean_probs = mc_predictions.mean(dim=0)
        logits = torch.log(mean_probs + 1e-10)
    
    # Compute attribution signals
    attribution_signals = compute_attribution_signals(logits, embeddings)
    
    # Compute compound uncertainty
    compound = compute_compound_uncertainty(predictive_signals, attribution_signals)
    
    # Combine all signals
    all_signals = {
        **predictive_signals,
        **attribution_signals,
        "compound_uncertainty": compound,
    }
    
    return all_signals


def evaluate_watsonx_deployment(
    client,
    embeddings: torch.Tensor,
    ground_truth: torch.Tensor,
    group_labels: torch.Tensor,
    mc_passes: int = 20,
    batch_size: int = 32,
) -> Dict[str, Any]:
    """
    Full evaluation pipeline for watsonx.ai deployed model.
    
    Replicates the complete Streamlit evaluation:
    1. Get MC Dropout predictions from watsonx.ai
    2. Compute all 7 uncertainty signals
    3. Calculate AUROC for epistemic/aleatoric detection
    4. Generate evaluation metrics
    
    Args:
        client: WatsonxScoringClient instance
        embeddings: Evaluation embeddings [N, 768]
        ground_truth: Ground truth labels [N]
        group_labels: Group labels (0=clean, 1=aleatoric, 2=epistemic) [N]
        mc_passes: Number of MC Dropout passes
        batch_size: Batch size for API calls
        
    Returns:
        Dictionary with:
        - predictions: Predicted classes [N]
        - confidences: Prediction confidences [N]
        - signals: All 7 uncertainty signals
        - auroc_results: AUROC scores for each signal
        - accuracy: Overall accuracy
        - group_accuracies: Accuracy per group
    """
    from .evaluation import binary_auroc
    
    # Get predictions with uncertainty from watsonx.ai
    predictions, confidences, base_uncertainties = client.score_with_uncertainty(
        embeddings=embeddings,
        mc_passes=mc_passes,
        batch_size=batch_size,
    )
    
    # Get full MC predictions for signal computation
    # (This requires multiple API calls)
    all_mc_preds = []
    for _ in range(mc_passes):
        response = client.score_batch(embeddings, batch_size=batch_size)
        # Parse response to get probabilities
        probs = parse_probabilities_from_response(response)
        all_mc_preds.append(probs)
    
    mc_predictions = torch.stack(all_mc_preds, dim=0)  # [mc_passes, N, num_classes]
    
    # Compute all uncertainty signals
    signals = compute_uncertainty_signals(
        mc_predictions=mc_predictions,
        embeddings=embeddings,
    )
    
    # Calculate AUROC scores
    # Aleatoric: detect noisy labels (group 1)
    # Epistemic: detect under-supported classes (group 2)
    aleatoric_mask = (group_labels == 1)
    epistemic_mask = (group_labels == 2)
    
    auroc_results = []
    for signal_name, signal_values in signals.items():
        alea_auroc = binary_auroc(signal_values, aleatoric_mask)
        epis_auroc = binary_auroc(signal_values, epistemic_mask)
        auroc_results.append((signal_name, alea_auroc, epis_auroc))
    
    # Calculate accuracy metrics
    accuracy = (predictions == ground_truth).float().mean().item()
    
    group_accuracies = {}
    for group_id in [0, 1, 2]:
        group_mask = (group_labels == group_id)
        if group_mask.sum() > 0:
            group_acc = (predictions[group_mask] == ground_truth[group_mask]).float().mean().item()
            group_names = {0: "clean", 1: "aleatoric", 2: "epistemic"}
            group_accuracies[group_names[group_id]] = group_acc
    
    return {
        "predictions": predictions,
        "confidences": confidences,
        "signals": signals,
        "auroc_results": auroc_results,
        "accuracy": accuracy,
        "group_accuracies": group_accuracies,
    }


def parse_probabilities_from_response(response: Dict) -> torch.Tensor:
    """
    Parse probability vectors from watsonx.ai response.
    
    Args:
        response: Raw API response
        
    Returns:
        Probability tensor [N, num_classes]
    """
    predictions = response.get("predictions", [])
    
    probs_list = []
    for pred in predictions:
        if isinstance(pred, list) and len(pred) > 0:
            probs_list.append(pred)
        elif isinstance(pred, dict) and "values" in pred:
            probs_list.extend(pred["values"])
    
    return torch.tensor(probs_list, dtype=torch.float32)


def compare_local_vs_watsonx(
    local_signals: Dict[str, torch.Tensor],
    watsonx_signals: Dict[str, torch.Tensor],
    tolerance: float = 0.01,
) -> Dict[str, bool]:
    """
    Compare local Streamlit results with watsonx.ai deployment.
    
    Validates that deployment produces same results as local evaluation.
    
    Args:
        local_signals: Signals from Streamlit evaluation
        watsonx_signals: Signals from watsonx.ai evaluation
        tolerance: Maximum allowed difference
        
    Returns:
        Dictionary of signal_name -> matches (bool)
    """
    comparison = {}
    
    for signal_name in local_signals.keys():
        if signal_name not in watsonx_signals:
            comparison[signal_name] = False
            continue
        
        local = local_signals[signal_name]
        watsonx = watsonx_signals[signal_name]
        
        # Check if values are close
        max_diff = (local - watsonx).abs().max().item()
        matches = max_diff < tolerance
        
        comparison[signal_name] = matches
        
        if not matches:
            print(f"⚠️  {signal_name}: max diff = {max_diff:.6f} (tolerance = {tolerance})")
    
    return comparison


# Made with Bob