"""
watsonx.ai scoring client for UQ classification models.

This module provides functions to interact with watsonx.ai scoring endpoints
for batch inference and real-time predictions using trained UQ models.

Functions:
    create_scoring_payload: Format embeddings for watsonx.ai API
    score_batch: Send batch of embeddings for scoring
    parse_scoring_response: Extract predictions and uncertainties
    score_with_uncertainty: Get predictions + MC Dropout uncertainty
    monitor_to_governance: Log predictions to watsonx.governance
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

# Set up logging following IBM best practices
logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not available. Install with: pip install requests")


class WatsonxScoringClient:
    """
    Client for watsonx.ai scoring endpoints.
    
    Handles authentication, request formatting, and response parsing
    for UQ classification model inference.
    
    Usage:
        client = WatsonxScoringClient(
            api_key="your-api-key",
            scoring_url="https://your-endpoint.watsonx.ai/v1/deployments/model-id/predictions"
        )
        
        predictions, uncertainties = client.score_with_uncertainty(
            embeddings=eval_embeddings,
            mc_passes=20
        )
    """
    
    def __init__(
        self,
        api_key: str,
        scoring_url: str,
        space_id: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize watsonx.ai scoring client.
        
        Args:
            api_key: IBM Cloud API key or watsonx.ai token
            scoring_url: Full URL to scoring endpoint
            space_id: Optional deployment space ID
            timeout: Request timeout in seconds
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required. Install with: pip install requests")
        
        self.api_key = api_key
        self.scoring_url = scoring_url
        self.space_id = space_id
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set up authentication headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        if space_id:
            self.headers["ML-Instance-ID"] = space_id
    
    def create_scoring_payload(
        self,
        embeddings: torch.Tensor,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create watsonx.ai scoring payload from embeddings.
        
        Args:
            embeddings: Input embeddings [N, 768] or [768]
            fields: Optional field names (default: ["embedding"])
            
        Returns:
            Formatted payload dictionary
        """
        # Ensure 2D shape
        if embeddings.dim() == 1:
            embeddings = embeddings.unsqueeze(0)
        
        # Convert to list of lists
        values = embeddings.cpu().numpy().tolist()
        
        if fields is None:
            fields = ["embedding"]
        
        payload = {
            "input_data": [
                {
                    "fields": fields,
                    "values": values,
                }
            ]
        }
        
        return payload
    
    def score_batch(
        self,
        embeddings: torch.Tensor,
        batch_size: int = 32,
    ) -> Dict[str, Any]:
        """
        Score a batch of embeddings using watsonx.ai endpoint.
        
        Args:
            embeddings: Input embeddings [N, 768]
            batch_size: Maximum batch size per request
            
        Returns:
            Combined scoring response dictionary
        """
        n_samples = embeddings.shape[0]
        all_predictions = []
        
        # Process in batches
        for i in range(0, n_samples, batch_size):
            batch = embeddings[i:i + batch_size]
            payload = self.create_scoring_payload(batch)
            
            try:
                response = self.session.post(
                    self.scoring_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                
                result = response.json()
                all_predictions.append(result)
                logger.debug(f"Successfully scored batch {i//batch_size + 1}/{(n_samples + batch_size - 1)//batch_size}")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Error scoring batch {i//batch_size + 1}: {e}"
                if hasattr(e, 'response') and e.response is not None:
                    error_msg += f" | Status: {e.response.status_code} | Response: {e.response.text[:200]}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        
        # Combine results
        combined = {
            "predictions": [],
            "fields": all_predictions[0].get("predictions", [{}])[0].get("fields", []),
        }
        
        for pred in all_predictions:
            if "predictions" in pred and len(pred["predictions"]) > 0:
                combined["predictions"].extend(pred["predictions"][0].get("values", []))
        
        return combined
    
    def parse_scoring_response(
        self,
        response: Dict[str, Any],
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Parse watsonx.ai scoring response into predictions and confidences.
        
        Args:
            response: Raw scoring response from watsonx.ai
            
        Returns:
            Tuple of (predicted_classes, confidences)
        """
        predictions = response.get("predictions", [])
        
        if not predictions:
            raise ValueError("No predictions in response")
        
        # Extract probability vectors
        probs_list = []
        for pred in predictions:
            if isinstance(pred, list) and len(pred) > 0:
                probs_list.append(pred)
            elif isinstance(pred, dict) and "values" in pred:
                probs_list.extend(pred["values"])
        
        # Convert to tensor
        probs = torch.tensor(probs_list, dtype=torch.float32)
        
        # Get predicted classes and confidences
        confidences, predicted_classes = torch.max(probs, dim=1)
        
        return predicted_classes, confidences
    
    def score_with_uncertainty(
        self,
        embeddings: torch.Tensor,
        mc_passes: int = 20,
        batch_size: int = 32,
    ) -> Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Score embeddings with Monte Carlo Dropout uncertainty estimation.
        
        Requires model to have MC Dropout enabled on watsonx.ai endpoint.
        
        Args:
            embeddings: Input embeddings [N, 768]
            mc_passes: Number of stochastic forward passes
            batch_size: Batch size per request
            
        Returns:
            Tuple of (predictions, confidences, uncertainty_dict)
            
        Uncertainty dict contains:
            - predictive_entropy: H(p)
            - mutual_info: I(y;θ|x)
            - msp_uncertainty: 1 - max(p)
        """
        # Collect predictions from multiple passes
        all_probs = []
        
        for pass_idx in range(mc_passes):
            response = self.score_batch(embeddings, batch_size=batch_size)
            _, _ = self.parse_scoring_response(response)
            
            # Extract probabilities
            predictions = response.get("predictions", [])
            probs_list = []
            for pred in predictions:
                if isinstance(pred, list) and len(pred) > 0:
                    probs_list.append(pred)
                elif isinstance(pred, dict) and "values" in pred:
                    probs_list.extend(pred["values"])
            
            probs = torch.tensor(probs_list, dtype=torch.float32)
            all_probs.append(probs)
        
        # Stack predictions [mc_passes, N, num_classes]
        all_probs = torch.stack(all_probs, dim=0)
        
        # Compute mean predictions
        mean_probs = all_probs.mean(dim=0)
        confidences, predicted_classes = torch.max(mean_probs, dim=1)
        
        # Compute uncertainty metrics
        uncertainties = {}
        
        # Predictive entropy: H(p)
        eps = 1e-10
        predictive_entropy = -(mean_probs * torch.log(mean_probs + eps)).sum(dim=1)
        uncertainties["predictive_entropy"] = predictive_entropy
        
        # Mutual information: I(y;θ|x) = H(p) - E[H(p|θ)]
        expected_entropy = -(all_probs * torch.log(all_probs + eps)).sum(dim=2).mean(dim=0)
        mutual_info = predictive_entropy - expected_entropy
        uncertainties["mutual_info"] = mutual_info
        
        # MSP uncertainty: 1 - max(p)
        msp_uncertainty = 1.0 - confidences
        uncertainties["msp_uncertainty"] = msp_uncertainty
        
        return predicted_classes, confidences, uncertainties


class WatsonxGovernanceLogger:
    """
    Logger for watsonx.governance metrics tracking.
    
    Sends model predictions, uncertainties, and performance metrics
    to watsonx.governance for monitoring and compliance.
    
    Usage:
        logger = WatsonxGovernanceLogger(
            api_key="your-api-key",
            governance_url="https://api.dataplatform.cloud.ibm.com/v2/governance",
            model_id="uq-classifier-v1"
        )
        
        logger.log_predictions(
            predictions=predictions,
            ground_truth=labels,
            uncertainties=uncertainty_dict,
            metadata={"deployment": "prod"}
        )
    """
    
    def __init__(
        self,
        api_key: str,
        governance_url: str,
        model_id: str,
        deployment_id: Optional[str] = None,
    ):
        """
        Initialize watsonx.governance logger.
        
        Args:
            api_key: IBM Cloud API key
            governance_url: watsonx.governance API endpoint
            model_id: Unique model identifier
            deployment_id: Optional deployment identifier
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required. Install with: pip install requests")
        
        self.api_key = api_key
        self.governance_url = governance_url
        self.model_id = model_id
        self.deployment_id = deployment_id or f"{model_id}_default"
        self.session = requests.Session()
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
    
    def log_predictions(
        self,
        predictions: torch.Tensor,
        ground_truth: Optional[torch.Tensor] = None,
        uncertainties: Optional[Dict[str, torch.Tensor]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log predictions to watsonx.governance.
        
        Args:
            predictions: Predicted class labels [N]
            ground_truth: Optional ground truth labels [N]
            uncertainties: Optional uncertainty signals dict
            metadata: Optional metadata (deployment info, timestamps, etc.)
            
        Returns:
            Response from governance API
        """
        timestamp = time.time()
        
        # Build payload
        payload = {
            "model_id": self.model_id,
            "deployment_id": self.deployment_id,
            "timestamp": timestamp,
            "predictions": predictions.cpu().numpy().tolist(),
        }
        
        if ground_truth is not None:
            payload["ground_truth"] = ground_truth.cpu().numpy().tolist()
            
            # Compute accuracy
            accuracy = (predictions == ground_truth).float().mean().item()
            payload["metrics"] = {"accuracy": accuracy}
        
        if uncertainties is not None:
            payload["uncertainties"] = {
                key: val.cpu().numpy().tolist()
                for key, val in uncertainties.items()
            }
        
        if metadata is not None:
            payload["metadata"] = metadata
        
        # Send to governance API
        try:
            response = self.session.post(
                f"{self.governance_url}/predictions",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Successfully logged {len(predictions)} predictions to governance")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error logging to governance: {e}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" | Status: {e.response.status_code}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def log_metrics(
        self,
        metrics: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log aggregate metrics to watsonx.governance.
        
        Args:
            metrics: Dictionary of metric names and values
            metadata: Optional metadata
            
        Returns:
            Response from governance API
        """
        timestamp = time.time()
        
        payload = {
            "model_id": self.model_id,
            "deployment_id": self.deployment_id,
            "timestamp": timestamp,
            "metrics": metrics,
        }
        
        if metadata is not None:
            payload["metadata"] = metadata
        
        try:
            response = self.session.post(
                f"{self.governance_url}/metrics",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Successfully logged metrics to governance: {list(metrics.keys())}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error logging metrics: {e}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" | Status: {e.response.status_code}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


def create_mock_scoring_client(
    model: torch.nn.Module,
    device: torch.device,
) -> "MockScoringClient":
    """
    Create a mock scoring client for local testing.
    
    Simulates watsonx.ai API without requiring actual deployment.
    
    Args:
        model: Local PyTorch model
        device: Device to run inference on
        
    Returns:
        Mock client with same interface as WatsonxScoringClient
    """
    
    class MockScoringClient:
        """Mock client for local testing."""
        
        def __init__(self, model, device):
            self.model = model
            self.device = device
            self.model.eval()
        
        def score_batch(self, embeddings, batch_size=32):
            """Mock batch scoring."""
            with torch.no_grad():
                embeddings = embeddings.to(self.device)
                logits = self.model(embeddings)
                probs = torch.softmax(logits, dim=1)
            
            return {
                "predictions": probs.cpu().numpy().tolist(),
                "fields": ["probabilities"],
            }
        
        def score_with_uncertainty(self, embeddings, mc_passes=20, batch_size=32):
            """Mock MC Dropout scoring."""
            self.model.eval()
            self.model.enable_dropout()
            
            all_probs = []
            with torch.no_grad():
                embeddings = embeddings.to(self.device)
                for _ in range(mc_passes):
                    logits = self.model(embeddings)
                    probs = torch.softmax(logits, dim=1)
                    all_probs.append(probs)
            
            all_probs = torch.stack(all_probs, dim=0)
            mean_probs = all_probs.mean(dim=0)
            confidences, predicted_classes = torch.max(mean_probs, dim=1)
            
            # Compute uncertainties
            eps = 1e-10
            predictive_entropy = -(mean_probs * torch.log(mean_probs + eps)).sum(dim=1)
            expected_entropy = -(all_probs * torch.log(all_probs + eps)).sum(dim=2).mean(dim=0)
            mutual_info = predictive_entropy - expected_entropy
            msp_uncertainty = 1.0 - confidences
            
            uncertainties = {
                "predictive_entropy": predictive_entropy,
                "mutual_info": mutual_info,
                "msp_uncertainty": msp_uncertainty,
            }
            
            return predicted_classes, confidences, uncertainties
    
    return MockScoringClient(model, device)


# Made with Bob