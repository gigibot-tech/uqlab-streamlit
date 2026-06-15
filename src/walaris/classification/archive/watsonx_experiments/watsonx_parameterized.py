"""
Parameterized watsonx.ai inference for dynamic experiment configurations.

This module enables a SINGLE watsonx.ai deployment to handle multiple experiment
configurations by passing parameters at inference time, rather than requiring
separate deployments for each configuration.

Key Concept:
- Deploy ONE model with training data
- Pass experiment parameters (noise rate, sample size, etc.) at inference time
- Server-side logic selects appropriate training subset for DualXDA attribution
- No need for multiple deployments!
"""

from __future__ import annotations

import torch
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    """
    Configuration for a specific experiment variant.
    
    Attributes:
        noise_rate: Label noise rate (0.0 to 1.0)
        under_supported_classes: List of under-supported class indices
        under_train_per_class: Samples per under-supported class
        regular_train_per_class: Samples per regular class
        eval_per_group: Evaluation samples per group
    """
    noise_rate: float
    under_supported_classes: List[int]
    under_train_per_class: int
    regular_train_per_class: int
    eval_per_group: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API payload."""
        return {
            "noise_rate": self.noise_rate,
            "under_supported_classes": self.under_supported_classes,
            "under_train_per_class": self.under_train_per_class,
            "regular_train_per_class": self.regular_train_per_class,
            "eval_per_group": self.eval_per_group,
        }


class ParameterizedScoringClient:
    """
    Client for parameterized watsonx.ai inference.
    
    Sends experiment configuration along with embeddings, allowing a single
    deployment to handle multiple experiment variants.
    
    Usage:
        client = ParameterizedScoringClient(
            api_key="your-key",
            scoring_url="https://...",
            space_id="space-id"
        )
        
        # Experiment 1: 10% noise, 2 under-supported classes
        config1 = ExperimentConfig(
            noise_rate=0.1,
            under_supported_classes=[0, 1],
            under_train_per_class=50,
            regular_train_per_class=300,
            eval_per_group=100
        )
        
        # Experiment 2: 40% noise, 3 under-supported classes
        config2 = ExperimentConfig(
            noise_rate=0.4,
            under_supported_classes=[0, 1, 2],
            under_train_per_class=30,
            regular_train_per_class=250,
            eval_per_group=150
        )
        
        # Same deployment, different configs!
        results1 = client.score_with_config(embeddings, config1)
        results2 = client.score_with_config(embeddings, config2)
    """
    
    def __init__(
        self,
        api_key: str,
        scoring_url: str,
        space_id: Optional[str] = None,
        timeout: int = 60,
    ):
        """Initialize parameterized scoring client."""
        from walaris.classification.watsonx_scoring import WatsonxScoringClient
        
        self.base_client = WatsonxScoringClient(
            api_key=api_key,
            scoring_url=scoring_url,
            space_id=space_id,
            timeout=timeout
        )
    
    def score_with_config(
        self,
        embeddings: torch.Tensor,
        config: ExperimentConfig,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        """
        Score embeddings with specific experiment configuration.
        
        Args:
            embeddings: Input embeddings [N, 768]
            config: Experiment configuration
            batch_size: Batch size per request
            
        Returns:
            Dictionary with predictions and uncertainty signals
        """
        # Create payload with embeddings AND config
        payload = self._create_parameterized_payload(embeddings, config)
        
        # Send to watsonx.ai
        response = self.base_client.session.post(
            self.base_client.scoring_url,
            headers=self.base_client.headers,
            json=payload,
            timeout=self.base_client.timeout,
        )
        response.raise_for_status()
        
        return response.json()
    
    def _create_parameterized_payload(
        self,
        embeddings: torch.Tensor,
        config: ExperimentConfig,
    ) -> Dict[str, Any]:
        """
        Create payload with embeddings and experiment parameters.
        
        The custom scorer on watsonx.ai will use these parameters to:
        1. Select appropriate training subset for DualXDA
        2. Apply noise filtering based on noise_rate
        3. Compute attribution signals with correct training context
        """
        # Ensure 2D shape
        if embeddings.dim() == 1:
            embeddings = embeddings.unsqueeze(0)
        
        # Convert to list
        values = embeddings.cpu().numpy().tolist()
        
        payload = {
            "input_data": [
                {
                    "fields": ["embedding"],
                    "values": values,
                }
            ],
            # Add experiment configuration as metadata
            "experiment_config": config.to_dict(),
        }
        
        return payload


class ParameterizedUncertaintyScorer:
    """
    Server-side scorer that handles parameterized inference.
    
    This class would be deployed to watsonx.ai as the custom scoring function.
    It receives experiment configuration and dynamically selects the appropriate
    training subset for DualXDA attribution.
    
    Key Innovation:
    - Single deployment handles ALL experiment variants
    - Training data is pre-loaded with ALL samples
    - Parameters determine which subset to use for attribution
    - No need for multiple deployments!
    """
    
    def __init__(
        self,
        model: torch.nn.Module,
        full_train_embeddings: torch.Tensor,
        full_train_labels: torch.Tensor,
        full_train_is_noisy: torch.Tensor,
        mc_passes: int = 20,
    ):
        """
        Initialize parameterized scorer with FULL training data.
        
        Args:
            model: Trained classifier
            full_train_embeddings: ALL training embeddings [N_total, 768]
            full_train_labels: ALL training labels [N_total]
            full_train_is_noisy: Noise flags for ALL samples [N_total]
            mc_passes: Number of MC dropout passes
        """
        self.model = model
        self.full_train_embeddings = full_train_embeddings
        self.full_train_labels = full_train_labels
        self.full_train_is_noisy = full_train_is_noisy
        self.mc_passes = mc_passes
        
        # Pre-compute indices for each class
        self.class_indices = {}
        for class_id in range(10):  # CIFAR-10
            mask = (full_train_labels == class_id)
            self.class_indices[class_id] = torch.nonzero(mask, as_tuple=False).squeeze()
    
    def score(
        self,
        embeddings: torch.Tensor,
        experiment_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Score with dynamic experiment configuration.
        
        Args:
            embeddings: Input embeddings [N, 768]
            experiment_config: Dictionary with experiment parameters
            
        Returns:
            Dictionary with predictions and uncertainty signals
        """
        # Parse config
        config = ExperimentConfig(**experiment_config)
        
        # Select training subset based on config
        train_subset_indices = self._select_training_subset(config)
        train_embeddings = self.full_train_embeddings[train_subset_indices]
        train_labels = self.full_train_labels[train_subset_indices]
        train_is_noisy = self.full_train_is_noisy[train_subset_indices]
        
        # Initialize DualXDA with selected subset
        from src.triage.dualxda_axioms import DualXDATracer
        
        tracer = DualXDATracer(
            model=self.model,
            train_dataset=self._create_dataset(train_embeddings, train_labels, train_is_noisy),
            layer_name="classifier",
            cache_dir=None,  # In-memory only
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        
        # Compute predictions with MC Dropout
        all_logits = []
        self.model.eval()
        self.model.enable_dropout()
        
        with torch.no_grad():
            for _ in range(self.mc_passes):
                logits = self.model(embeddings)
                all_logits.append(logits)
        
        all_logits = torch.stack(all_logits, dim=0)
        mean_logits = all_logits.mean(dim=0)
        mean_probs = torch.softmax(mean_logits, dim=1)
        
        # Compute predictive uncertainty signals
        uncertainties = self._compute_predictive_signals(all_logits, mean_probs)
        
        # Compute attribution signals with DualXDA
        attribution_signals = self._compute_attribution_signals(
            tracer=tracer,
            embeddings=embeddings,
            predictions=mean_probs,
            train_labels=train_labels,
            train_is_noisy=train_is_noisy
        )
        
        # Combine all signals
        uncertainties.update(attribution_signals)
        
        # Get predictions
        confidences, predicted_classes = torch.max(mean_probs, dim=1)
        
        return {
            "predictions": predicted_classes.cpu().numpy().tolist(),
            "confidences": confidences.cpu().numpy().tolist(),
            "uncertainty": {
                key: val.cpu().numpy().tolist()
                for key, val in uncertainties.items()
            },
            "experiment_config": config.to_dict(),
        }
    
    def _select_training_subset(self, config: ExperimentConfig) -> torch.Tensor:
        """
        Select training subset based on experiment configuration.
        
        This is the KEY function that enables parameterized inference!
        """
        selected_indices = []
        
        # Under-supported classes
        for class_id in config.under_supported_classes:
            class_idx = self.class_indices[class_id]
            # Take first N samples (or random sample)
            n_samples = min(config.under_train_per_class, len(class_idx))
            selected_indices.append(class_idx[:n_samples])
        
        # Regular classes
        regular_classes = [i for i in range(10) if i not in config.under_supported_classes]
        for class_id in regular_classes:
            class_idx = self.class_indices[class_id]
            n_samples = min(config.regular_train_per_class, len(class_idx))
            selected_indices.append(class_idx[:n_samples])
        
        # Combine all indices
        all_indices = torch.cat(selected_indices)
        
        # Apply noise filtering if needed
        if config.noise_rate < 1.0:
            # Keep only samples matching target noise rate
            # (This is a simplified version - real implementation would be more sophisticated)
            pass
        
        return all_indices
    
    def _compute_predictive_signals(
        self,
        all_logits: torch.Tensor,
        mean_probs: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """Compute predictive uncertainty signals."""
        eps = 1e-10
        
        # Predictive entropy
        predictive_entropy = -(mean_probs * torch.log(mean_probs + eps)).sum(dim=1)
        
        # Mutual information
        all_probs = torch.softmax(all_logits, dim=2)
        expected_entropy = -(all_probs * torch.log(all_probs + eps)).sum(dim=2).mean(dim=0)
        mutual_info = predictive_entropy - expected_entropy
        
        # MSP uncertainty
        msp_uncertainty = 1.0 - mean_probs.max(dim=1)[0]
        
        # Inverse logit magnitude
        logit_magnitude = torch.norm(all_logits.mean(dim=0), dim=1)
        inverse_logit_magnitude = 1.0 / (logit_magnitude + eps)
        
        return {
            "predictive_entropy": predictive_entropy,
            "mutual_info": mutual_info,
            "msp_uncertainty": msp_uncertainty,
            "inverse_logit_magnitude": inverse_logit_magnitude,
        }
    
    def _compute_attribution_signals(
        self,
        tracer,
        embeddings: torch.Tensor,
        predictions: torch.Tensor,
        train_labels: torch.Tensor,
        train_is_noisy: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """Compute DualXDA attribution signals."""
        from walaris.classification.attribution_signals import (
            compute_attribution_structure_signals,
            map_attribution_structure_to_uncertainty,
        )
        
        # Create temporary dataset
        class TempDataset:
            def __init__(self, labels, is_noisy):
                self.targets = labels
                self.is_noisy = is_noisy
        
        dataset = TempDataset(train_labels, train_is_noisy)
        
        signals = compute_attribution_structure_signals(
            tracer=tracer,
            model=self.model,
            eval_inputs=embeddings,  # DINOv2 embeddings
            mean_predictions=predictions,
            train_dataset=dataset,
            device=embeddings.device,
            batch_size=32,
            top_k=10,
            num_classes=10
        )
        
        return map_attribution_structure_to_uncertainty(signals)
    
    def _create_dataset(self, embeddings, labels, is_noisy):
        """Create temporary dataset object."""
        class TempDataset:
            def __init__(self, targets, is_noisy_flags):
                self.targets = targets
                self.is_noisy = is_noisy_flags
        
        return TempDataset(labels, is_noisy)


# ============================================================================
# DEPLOYMENT STRATEGY COMPARISON
# ============================================================================
"""
OPTION 1: Multiple Deployments (NOT RECOMMENDED)
-------------------------------------------------
- Deploy separate model for each experiment configuration
- Each deployment has specific training subset
- Pros: Simple, isolated
- Cons: 
  * Need 10+ deployments for different configs
  * Expensive (each deployment costs money)
  * Hard to manage
  * Slow to iterate

Example:
- deployment_1: 10% noise, 2 under-supported classes
- deployment_2: 10% noise, 3 under-supported classes
- deployment_3: 40% noise, 2 under-supported classes
- ... (many more)


OPTION 2: Parameterized Single Deployment (RECOMMENDED)
--------------------------------------------------------
- Deploy ONE model with FULL training data
- Pass experiment config at inference time
- Server-side logic selects appropriate subset
- Pros:
  * Single deployment for ALL experiments
  * Cost-effective
  * Easy to manage
  * Fast iteration
  * Can test new configs without redeployment
- Cons:
  * Slightly more complex scorer logic
  * Larger deployment package (includes all training data)

Example:
- deployment: ONE deployment
- config_1: {noise_rate: 0.1, under_supported: [0,1], ...}
- config_2: {noise_rate: 0.4, under_supported: [0,1,2], ...}
- ... (unlimited configs, same deployment!)


RECOMMENDATION: Use Option 2 (Parameterized Single Deployment)
"""

# Made with Bob