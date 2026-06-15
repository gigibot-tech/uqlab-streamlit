"""
Custom scoring function for watsonx.ai deployment with uncertainty quantification.

This module provides a modular scoring function that:
1. Works with any model architecture (not just DINOv2)
2. Returns predictions + uncertainty scores in a single API call
3. Computes uncertainty from final layer outputs (logits/embeddings)
4. Compatible with watsonx.ai custom deployment

Usage:
    Deploy this as a custom scoring function in watsonx.ai to get
    predictions + uncertainty in one API call instead of multiple.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class UncertaintyScorer:
    """
    Custom scorer that returns predictions + uncertainty scores.
    
    Modular design: Works with any model that has:
    - A forward() method returning logits
    - Optional: An embedding layer before final classifier
    - Optional: Attribution method (DualXDA or custom)
    
    Usage in watsonx.ai:
        # Without attribution
        scorer = UncertaintyScorer(model, mc_passes=20)
        
        # With DualXDA attribution
        from attribution_signals import DualXDAAttribution
        attribution_fn = DualXDAAttribution(train_embeddings, train_labels)
        scorer = UncertaintyScorer(model, mc_passes=20, attribution_fn=attribution_fn)
        
        results = scorer.score(inputs)
        # Returns: predictions, confidences, uncertainty_scores
    """
    
    def __init__(
        self,
        model: nn.Module,
        mc_passes: int = 20,
        uncertainty_signals: Optional[List[str]] = None,
        attribution_fn: Optional[Callable] = None,
    ):
        """
        Initialize uncertainty scorer.
        
        Args:
            model: PyTorch model (any architecture)
            mc_passes: Number of MC Dropout passes
            uncertainty_signals: Which signals to compute
                Default: ['msp', 'entropy', 'mutual_info', 'logit_magnitude']
            attribution_fn: Optional attribution function (e.g., DualXDA)
                Should take (embeddings, logits) and return attribution dict
        """
        self.model = model
        self.mc_passes = mc_passes
        self.attribution_fn = attribution_fn
        
        if uncertainty_signals is None:
            # Default: predictive signals only
            self.uncertainty_signals = [
                'msp_uncertainty',
                'predictive_entropy',
                'mutual_info',
                'inverse_logit_magnitude',
            ]
        else:
            self.uncertainty_signals = uncertainty_signals
    
    def enable_dropout(self):
        """Enable dropout for MC Dropout inference."""
        for module in self.model.modules():
            if isinstance(module, nn.Dropout):
                module.train()
    
    def forward_with_uncertainty(
        self,
        inputs: torch.Tensor,
        embeddings: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Forward pass with uncertainty quantification.
        
        Args:
            inputs: Input tensor [batch_size, ...] (any shape)
            embeddings: Optional pre-computed embeddings for attribution
                If None and attribution_fn provided, will extract from model
            
        Returns:
            Tuple of:
            - predictions: Predicted classes [batch_size]
            - confidences: Prediction confidences [batch_size]
            - uncertainties: Dictionary of uncertainty signals
        """
        self.model.eval()
        self.enable_dropout()
        
        # Collect MC Dropout predictions
        all_logits = []
        all_probs = []
        
        with torch.no_grad():
            for _ in range(self.mc_passes):
                logits = self.model(inputs)  # [batch_size, num_classes]
                probs = F.softmax(logits, dim=1)
                all_logits.append(logits)
                all_probs.append(probs)
        
        # Stack predictions
        all_logits = torch.stack(all_logits, dim=0)  # [mc_passes, batch_size, num_classes]
        all_probs = torch.stack(all_probs, dim=0)  # [mc_passes, batch_size, num_classes]
        
        # Mean predictions
        mean_probs = all_probs.mean(dim=0)  # [batch_size, num_classes]
        mean_logits = all_logits.mean(dim=0)  # [batch_size, num_classes]
        
        # Get predictions
        confidences, predictions = mean_probs.max(dim=1)
        
        # Compute uncertainty signals
        uncertainties = self._compute_uncertainties(
            all_probs=all_probs,
            mean_probs=mean_probs,
            mean_logits=mean_logits,
            embeddings=embeddings if embeddings is not None else inputs,
        )
        
        return predictions, confidences, uncertainties
    
    def _compute_uncertainties(
        self,
        all_probs: torch.Tensor,
        mean_probs: torch.Tensor,
        mean_logits: torch.Tensor,
        embeddings: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Compute requested uncertainty signals.
        
        Args:
            all_probs: MC Dropout probabilities [mc_passes, batch_size, num_classes]
            mean_probs: Mean probabilities [batch_size, num_classes]
            mean_logits: Mean logits [batch_size, num_classes]
            embeddings: Input embeddings for attribution [batch_size, embed_dim]
            
        Returns:
            Dictionary of uncertainty signals
        """
        uncertainties = {}
        eps = 1e-10
        
        # MSP uncertainty
        if 'msp_uncertainty' in self.uncertainty_signals:
            max_probs, _ = mean_probs.max(dim=1)
            uncertainties['msp_uncertainty'] = 1.0 - max_probs
        
        # Predictive entropy
        if 'predictive_entropy' in self.uncertainty_signals:
            entropy = -(mean_probs * torch.log(mean_probs + eps)).sum(dim=1)
            uncertainties['predictive_entropy'] = entropy
        
        # Mutual information (epistemic uncertainty)
        if 'mutual_info' in self.uncertainty_signals:
            # H(p) - E[H(p|θ)]
            predictive_entropy = -(mean_probs * torch.log(mean_probs + eps)).sum(dim=1)
            sample_entropies = -(all_probs * torch.log(all_probs + eps)).sum(dim=2)
            expected_entropy = sample_entropies.mean(dim=0)
            mutual_info = predictive_entropy - expected_entropy
            uncertainties['mutual_info'] = mutual_info
        
        # Logit magnitude (confidence in decision)
        if 'inverse_logit_magnitude' in self.uncertainty_signals:
            logit_norms = torch.norm(mean_logits, dim=1)
            uncertainties['inverse_logit_magnitude'] = 1.0 / (logit_norms + eps)
        
        # Attribution-based signals (if attribution function provided)
        if self.attribution_fn is not None:
            attribution_signals = self.attribution_fn(embeddings, mean_logits)
            uncertainties.update(attribution_signals)
        
        # Compound uncertainty (weighted average)
        if len(uncertainties) > 0:
            # Normalize each signal to [0, 1]
            normalized = {}
            for name, signal in uncertainties.items():
                min_val = signal.min()
                max_val = signal.max()
                if max_val > min_val:
                    normalized[name] = (signal - min_val) / (max_val - min_val)
                else:
                    normalized[name] = torch.zeros_like(signal)
            
            # Average
            compound = torch.stack(list(normalized.values())).mean(dim=0)
            uncertainties['compound_uncertainty'] = compound
        
        return uncertainties
    
    def score(
        self,
        inputs: torch.Tensor,
    ) -> Dict[str, Any]:
        """
        Score inputs and return predictions + uncertainties.
        
        This is the main entry point for watsonx.ai deployment.
        
        Args:
            inputs: Input tensor [batch_size, ...]
            
        Returns:
            Dictionary with:
            - predictions: List of predicted classes
            - confidences: List of confidence scores
            - uncertainties: Dictionary of uncertainty signals (each a list)
        """
        predictions, confidences, uncertainties = self.forward_with_uncertainty(inputs)
        
        # Convert to lists for JSON serialization
        result = {
            'predictions': predictions.cpu().numpy().tolist(),
            'confidences': confidences.cpu().numpy().tolist(),
            'uncertainties': {
                name: values.cpu().numpy().tolist()
                for name, values in uncertainties.items()
            },
        }
        
        return result


def create_watsonx_scoring_function(
    model_path: str,
    model_class: type,
    mc_passes: int = 20,
    uncertainty_signals: Optional[List[str]] = None,
) -> Callable:
    """
    Create a scoring function for watsonx.ai custom deployment.
    
    This function can be deployed to watsonx.ai to get predictions + uncertainty
    in a single API call.
    
    Args:
        model_path: Path to model checkpoint
        model_class: Model class (e.g., EmbeddingDropoutMLP)
        mc_passes: Number of MC Dropout passes
        uncertainty_signals: Which signals to compute
        
    Returns:
        Scoring function compatible with watsonx.ai
    """
    # Load model
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    model = model_class()
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # Create scorer
    scorer = UncertaintyScorer(
        model=model,
        mc_passes=mc_passes,
        uncertainty_signals=uncertainty_signals,
    )
    
    def score_function(input_data: List[List[float]]) -> Dict[str, Any]:
        """
        Scoring function for watsonx.ai.
        
        Args:
            input_data: List of input vectors (e.g., embeddings)
            
        Returns:
            Dictionary with predictions and uncertainties
        """
        # Convert to tensor
        inputs = torch.tensor(input_data, dtype=torch.float32)
        
        # Score
        results = scorer.score(inputs)
        
        return results
    
    return score_function


# Example deployment script for watsonx.ai
WATSONX_DEPLOYMENT_TEMPLATE = """
# watsonx.ai Custom Scoring Function
# Deploy this file to watsonx.ai for uncertainty-aware predictions

import torch
import torch.nn as nn
from typing import Dict, List, Any

# Import your model class
from models import EmbeddingDropoutMLP  # Replace with your model

# Load model
MODEL_PATH = "model_checkpoint.pt"
checkpoint = torch.load(MODEL_PATH, map_location='cpu', weights_only=False)

model = EmbeddingDropoutMLP(
    input_dim=768,
    num_classes=10,
    hidden_dim=256,
    dropout=0.2
)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Create scorer
from watsonx_custom_scorer import UncertaintyScorer

scorer = UncertaintyScorer(
    model=model,
    mc_passes=20,
    uncertainty_signals=['msp_uncertainty', 'predictive_entropy', 'mutual_info']
)

# ============================================================================
# EXAMPLE: DualXDA Attribution Integration
# ============================================================================
#
# This example shows how to integrate DualXDA attribution signals with the
# custom scorer for watsonx.ai deployment.
#
# Usage:
#   from src.triage.dualxda_axioms import DualXDATracer
#   from walaris.classification.attribution_signals import compute_attribution_structure_signals
#
#   # 1. Create DualXDA tracer
#   tracer = DualXDATracer(
#       model=model,
#       train_dataset=train_dataset,
#       layer_name="classifier",
#       cache_dir="./cache",
#       device=device
#   )
#
#   # 2. Create attribution function wrapper
#   def dualxda_attribution_fn(embeddings, logits):
#       #Wrapper for DualXDA attribution signals.
#       predictions = torch.softmax(logits, dim=1)
#
#       signals = compute_attribution_structure_signals(
#           tracer=tracer,
#           model=model,
#           eval_features=embeddings,
#           mean_predictions=predictions,
#           train_dataset=train_dataset,
#           device=device,
#           batch_size=32,
#           top_k=10,
#           num_classes=10
#       )
#
#       # Convert to uncertainty format (higher = more uncertain)
#       return {
#           'inverse_mass': 1.0 / (signals['mass'] + 1e-6),
#           'inverse_coherence': 1.0 / (signals['coherence'] + 1e-6),
#           'dominance': signals['dominance'],
#           'label_disagreement': signals['label_disagreement'],
#           'noisy_support_ratio': signals['noisy_support_ratio'],
#           'attribution_concentration': signals['attribution_concentration'],
#           'cross_class_support': signals['cross_class_support'],
#       }
#
#   # 3. Create scorer with DualXDA attribution
#   scorer = UncertaintyScorer(
#       model=model,
#       mc_passes=20,
#       attribution_fn=dualxda_attribution_fn  # Plug in DualXDA!
#   )
#
#   # 4. Deploy to watsonx.ai - scorer computes all signals in single API call
# ============================================================================

def score(input_data: List[List[float]]) -> Dict[str, Any]:
    '''
    Main scoring function called by watsonx.ai.
    
    Input format:
        [[emb1_dim1, emb1_dim2, ..., emb1_dim768],
         [emb2_dim1, emb2_dim2, ..., emb2_dim768],
         ...]
    
    Output format:
        {
            "predictions": [0, 1, 2, ...],
            "confidences": [0.95, 0.87, 0.76, ...],
            "uncertainties": {
                "msp_uncertainty": [0.05, 0.13, 0.24, ...],
                "predictive_entropy": [0.12, 0.34, 0.56, ...],
                "mutual_info": [0.03, 0.08, 0.15, ...]
            }
        }
    '''
    inputs = torch.tensor(input_data, dtype=torch.float32)
    return scorer.score(inputs)
"""


def save_deployment_script(output_path: str):
    """Save the watsonx.ai deployment script template."""
    with open(output_path, 'w') as f:
        f.write(WATSONX_DEPLOYMENT_TEMPLATE)
    print(f"✅ Saved deployment script to: {output_path}")


# Made with Bob