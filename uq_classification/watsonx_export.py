"""
Export trained models and results for watsonx.ai deployment.

This module provides functions to package UQ classification results into
standardized formats for IBM watsonx.ai scoring and watsonx.governance tracking.

Exports both training and evaluation embeddings for full model lifecycle management.

Functions:
    export_model_checkpoint: Save PyTorch model weights
    export_model_config: Save model architecture as JSON
    export_embeddings: Save train/eval embeddings as PT files
    export_per_sample_signals: Save uncertainty signals as CSV
    export_evaluation_metadata: Save predictions and labels as CSV
    export_auroc_results: Save binary AUROC metrics as CSV
    export_experiment_config: Save full configuration as YAML
    create_watsonx_package: Bundle all files into downloadable ZIP
"""

from __future__ import annotations

import csv
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
import yaml


def export_model_checkpoint(
    model: torch.nn.Module,
    optimizer: Optional[torch.optim.Optimizer],
    epoch: int,
    loss: float,
    output_path: Path,
) -> Path:
    """
    Export PyTorch model checkpoint for watsonx.ai deployment.
    
    Args:
        model: Trained PyTorch model
        optimizer: Optimizer state (optional)
        epoch: Final training epoch
        loss: Final training loss
        output_path: Path to save checkpoint
        
    Returns:
        Path to saved checkpoint file
    """
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'epoch': epoch,
        'loss': loss,
    }
    
    if optimizer is not None:
        checkpoint['optimizer_state_dict'] = optimizer.state_dict()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint, output_path)
    
    return output_path


def export_model_config(
    model_type: str,
    input_dim: int,
    hidden_dim: int,
    num_classes: int,
    dropout: float,
    dinov2_backbone: str,
    training_config: Dict[str, Any],
    output_path: Path,
) -> Path:
    """
    Export model architecture configuration as JSON.
    
    Args:
        model_type: Model class name (e.g., "EmbeddingDropoutMLP")
        input_dim: Input feature dimension (768 for DINOv2)
        hidden_dim: Hidden layer dimension
        num_classes: Number of output classes
        dropout: Dropout probability
        dinov2_backbone: DINOv2 model variant
        training_config: Training hyperparameters
        output_path: Path to save JSON file
        
    Returns:
        Path to saved config file
    """
    config = {
        "model_type": model_type,
        "input_dim": input_dim,
        "hidden_dim": hidden_dim,
        "num_classes": num_classes,
        "dropout": dropout,
        "dinov2_backbone": dinov2_backbone,
        "training_config": training_config,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return output_path


def export_train_embeddings(
    embeddings: torch.Tensor,
    labels: torch.Tensor,
    noisy_labels: torch.Tensor,
    is_noisy: torch.Tensor,
    indices: torch.Tensor,
    output_path: Path,
) -> Path:
    """
    Export training embeddings as PyTorch file.
    
    These embeddings were used to train the model and can be used for:
    - Model retraining/fine-tuning in watsonx.ai
    - Transfer learning to new tasks
    - Analyzing training data distribution
    
    Args:
        embeddings: DINOv2 feature embeddings [N_train, 768]
        labels: Training labels (may be noisy) [N_train]
        noisy_labels: Original noisy labels [N_train]
        is_noisy: Boolean mask for noisy samples [N_train]
        indices: Original dataset indices [N_train]
        output_path: Path to save PT file
        
    Returns:
        Path to saved embeddings file
    """
    data = {
        'embeddings': embeddings.cpu(),
        'labels': labels.cpu(),
        'noisy_labels': noisy_labels.cpu(),
        'is_noisy': is_noisy.cpu(),
        'indices': indices.cpu(),
        'description': 'Training embeddings used to train the model',
        'shape': list(embeddings.shape),
        'dtype': str(embeddings.dtype),
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(data, output_path)
    
    return output_path


def export_eval_embeddings(
    embeddings: torch.Tensor,
    clean_labels: torch.Tensor,
    noisy_labels: torch.Tensor,
    is_noisy: torch.Tensor,
    group_labels: torch.Tensor,
    indices: torch.Tensor,
    output_path: Path,
) -> Path:
    """
    Export evaluation embeddings as PyTorch file.
    
    These embeddings were used for model evaluation and can be used for:
    - Reproducing evaluation results in watsonx.ai
    - Testing model performance
    - Comparing different model versions
    
    Args:
        embeddings: DINOv2 feature embeddings [N_eval, 768]
        clean_labels: Ground truth class labels [N_eval]
        noisy_labels: Noisy labels (if applicable) [N_eval]
        is_noisy: Boolean mask for noisy samples [N_eval]
        group_labels: Group labels (0=clean, 1=aleatoric, 2=epistemic) [N_eval]
        indices: Original dataset indices [N_eval]
        output_path: Path to save PT file
        
    Returns:
        Path to saved embeddings file
    """
    data = {
        'embeddings': embeddings.cpu(),
        'clean_labels': clean_labels.cpu(),
        'noisy_labels': noisy_labels.cpu(),
        'is_noisy': is_noisy.cpu(),
        'group_labels': group_labels.cpu(),
        'indices': indices.cpu(),
        'description': 'Evaluation embeddings used to test the model',
        'shape': list(embeddings.shape),
        'dtype': str(embeddings.dtype),
        'group_mapping': {0: 'clean', 1: 'aleatoric', 2: 'epistemic'},
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(data, output_path)
    
    return output_path


def export_per_sample_signals(
    eval_group_labels: torch.Tensor,
    eval_clean_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    signal_table: Dict[str, torch.Tensor],
    output_path: Path,
) -> Path:
    """
    Export per-sample uncertainty signals as CSV.
    
    Args:
        eval_group_labels: Group labels (0=clean, 1=aleatoric, 2=epistemic) [N]
        eval_clean_labels: Ground truth class labels [N]
        eval_is_noisy: Boolean mask for noisy samples [N]
        signal_table: Dictionary of uncertainty signal tensors
        output_path: Path to save CSV file
        
    Returns:
        Path to saved CSV file
    """
    group_names = {0: "clean", 1: "aleatoric", 2: "epistemic"}
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ["group", "clean_label", "is_noisy"] + list(signal_table.keys())
        writer.writerow(header)
        
        # Data rows
        n_samples = int(eval_group_labels.shape[0])
        for i in range(n_samples):
            row = [
                group_names[int(eval_group_labels[i].item())],
                int(eval_clean_labels[i].item()),
                bool(eval_is_noisy[i].item()),
            ]
            for signal_name in signal_table.keys():
                row.append(float(signal_table[signal_name][i].item()))
            writer.writerow(row)
    
    return output_path


def export_evaluation_metadata(
    eval_group_labels: torch.Tensor,
    eval_clean_labels: torch.Tensor,
    eval_noisy_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    eval_original_indices: torch.Tensor,
    predictions: torch.Tensor,
    confidences: torch.Tensor,
    output_path: Path,
) -> Path:
    """
    Export evaluation metadata with predictions as CSV.
    
    Args:
        eval_group_labels: Group labels (0=clean, 1=aleatoric, 2=epistemic) [N]
        eval_clean_labels: Ground truth class labels [N]
        eval_noisy_labels: Noisy labels used during training [N]
        eval_is_noisy: Boolean mask for noisy samples [N]
        eval_original_indices: Original dataset indices [N]
        predictions: Predicted class labels [N]
        confidences: Prediction confidence scores [N]
        output_path: Path to save CSV file
        
    Returns:
        Path to saved CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = [
            "sample_id",
            "original_index",
            "group_label",
            "clean_label",
            "noisy_label",
            "is_noisy",
            "predicted_class",
            "confidence",
        ]
        writer.writerow(header)
        
        # Data rows
        n_samples = int(eval_group_labels.shape[0])
        for i in range(n_samples):
            row = [
                i,
                int(eval_original_indices[i].item()),
                int(eval_group_labels[i].item()),
                int(eval_clean_labels[i].item()),
                int(eval_noisy_labels[i].item()),
                bool(eval_is_noisy[i].item()),
                int(predictions[i].item()),
                float(confidences[i].item()),
            ]
            writer.writerow(row)
    
    return output_path


def export_auroc_results(
    auroc_rows: List[Tuple[str, float, float]],
    output_path: Path,
) -> Path:
    """
    Export binary AUROC results as CSV.
    
    Args:
        auroc_rows: List of (signal_name, aleatoric_auroc, epistemic_auroc)
        output_path: Path to save CSV file
        
    Returns:
        Path to saved CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(["signal_name", "aleatoric_auroc", "epistemic_auroc"])
        
        # Data rows
        for signal_name, alea_auc, epis_auc in auroc_rows:
            writer.writerow([signal_name, f"{alea_auc:.4f}", f"{epis_auc:.4f}"])
    
    return output_path


def export_experiment_config(
    config: Dict[str, Any],
    output_path: Path,
) -> Path:
    """
    Export full experiment configuration as YAML.
    
    Args:
        config: Complete experiment configuration dictionary
        output_path: Path to save YAML file
        
    Returns:
        Path to saved config file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    return output_path


def create_readme(
    output_path: Path,
    timestamp: str,
    model_info: Dict[str, Any],
    train_size: int,
    eval_size: int,
) -> Path:
    """
    Create README.txt with deployment instructions.
    
    Args:
        output_path: Path to save README file
        timestamp: Generation timestamp
        model_info: Model metadata dictionary
        train_size: Number of training samples
        eval_size: Number of evaluation samples
        
    Returns:
        Path to saved README file
    """
    readme_content = f"""watsonx.ai Integration Package
==============================

This package contains all files needed to deploy the UQ classification model
to watsonx.ai and track metrics in watsonx.governance.

Files:
------
1. model_checkpoint.pt          - Trained PyTorch model weights
2. model_config.json            - Model architecture specification
3. train_embeddings.pt          - Training DINOv2 features ({train_size} samples)
4. eval_embeddings.pt           - Evaluation DINOv2 features ({eval_size} samples)
5. per_sample_signals.csv       - 7 uncertainty signals per eval sample
6. evaluation_metadata.csv      - Ground truth labels and predictions
7. auroc_results.csv            - Binary classification metrics
8. experiment_config.yaml       - Full experiment configuration

Model Information:
-----------------
- Type: {model_info.get('model_type', 'EmbeddingDropoutMLP')}
- Input: {model_info.get('input_dim', 768)}-dimensional embeddings
- Output: {model_info.get('num_classes', 10)} class probabilities
- Backbone: {model_info.get('dinov2_backbone', 'dinov2_vitb14')}
- Training Epochs: {model_info.get('epochs', 'N/A')}
- Final Loss: {model_info.get('final_loss', 'N/A'):.4f}

Dataset Sizes:
-------------
- Training samples: {train_size}
- Evaluation samples: {eval_size}
- Total embeddings: {train_size + eval_size}

Deployment Steps:
-----------------
1. Upload model_checkpoint.pt to watsonx.ai model repository
2. Create scoring endpoint using model_config.json
3. Test with eval_embeddings.pt (batch scoring)
4. Upload per_sample_signals.csv to watsonx.governance
5. Configure monitoring using auroc_results.csv thresholds

Model Input:
-----------
- Format: 768-dimensional float vector (DINOv2 embedding)
- Shape: [batch_size, 768]
- Normalization: None required (pre-normalized)
- Source: Extract from images using DINOv2 ViT-B/14 backbone

Model Output:
------------
- Format: 10-dimensional probability vector
- Shape: [batch_size, 10]
- Interpretation: Softmax probabilities for CIFAR-10 classes
  [airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck]

Uncertainty Signals:
-------------------
Epistemic (Model Uncertainty):
  - mutual_info: Information gain from model parameters
  - inverse_coherence: Inconsistency in attribution patterns
  - dominance: Concentration of attributions

Aleatoric (Data Uncertainty):
  - msp_uncertainty: 1 - max(softmax)
  - predictive_entropy: Shannon entropy of predictions

Hybrid Signals:
  - inverse_mass: Inverse of total attribution magnitude
  - inverse_logit_magnitude: Inverse of logit vector norm

Retraining with watsonx.ai:
---------------------------
1. Load train_embeddings.pt
2. Use embeddings as input features (no image preprocessing needed)
3. Train new MLP head or fine-tune existing model
4. Compare performance using eval_embeddings.pt

Production Inference:
--------------------
For new images:
1. Extract DINOv2 embeddings using dinov2_vitb14 backbone
2. Send 768-dim vectors to watsonx.ai scoring endpoint
3. Receive predictions + uncertainty scores
4. Log to watsonx.governance for monitoring

Generated: {timestamp}
Version: 1.0
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(readme_content)
    
    return output_path


def create_watsonx_package(
    export_dir: Path,
    output_zip: Path,
) -> Path:
    """
    Bundle all export files into a ZIP package.
    
    Args:
        export_dir: Directory containing all export files
        output_zip: Path to output ZIP file
        
    Returns:
        Path to created ZIP file
    """
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in export_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(export_dir.parent)
                zipf.write(file_path, arcname)
    
    return output_zip


def export_all_for_watsonx(
    model: torch.nn.Module,
    optimizer: Optional[torch.optim.Optimizer],
    epoch: int,
    loss: float,
    train_embeddings: torch.Tensor,
    train_labels: torch.Tensor,
    train_noisy_labels: torch.Tensor,
    train_is_noisy: torch.Tensor,
    train_indices: torch.Tensor,
    eval_embeddings: torch.Tensor,
    eval_clean_labels: torch.Tensor,
    eval_noisy_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    eval_group_labels: torch.Tensor,
    eval_indices: torch.Tensor,
    signal_table: Dict[str, torch.Tensor],
    predictions: torch.Tensor,
    confidences: torch.Tensor,
    auroc_rows: List[Tuple[str, float, float]],
    config: Dict[str, Any],
    output_base_dir: Path,
) -> Tuple[Path, Path]:
    """
    Export complete watsonx.ai package with all required files.
    
    Includes both training and evaluation embeddings for full model lifecycle.
    
    Args:
        model: Trained PyTorch model
        optimizer: Optimizer state (optional)
        epoch: Final training epoch
        loss: Final training loss
        train_embeddings: Training embeddings [N_train, 768]
        train_labels: Training labels [N_train]
        train_noisy_labels: Noisy training labels [N_train]
        train_is_noisy: Training noise mask [N_train]
        train_indices: Training dataset indices [N_train]
        eval_embeddings: Evaluation embeddings [N_eval, 768]
        eval_clean_labels: Evaluation ground truth labels [N_eval]
        eval_noisy_labels: Evaluation noisy labels [N_eval]
        eval_is_noisy: Evaluation noise mask [N_eval]
        eval_group_labels: Evaluation group labels [N_eval]
        eval_indices: Evaluation dataset indices [N_eval]
        signal_table: Uncertainty signals dictionary
        predictions: Predicted classes [N_eval]
        confidences: Prediction confidences [N_eval]
        auroc_rows: AUROC results
        config: Full experiment configuration
        output_base_dir: Base directory for exports
        
    Returns:
        Tuple of (export_directory_path, zip_file_path)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = output_base_dir / f"watsonx_export_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Export model checkpoint
    export_model_checkpoint(
        model=model,
        optimizer=optimizer,
        epoch=epoch,
        loss=loss,
        output_path=export_dir / "model_checkpoint.pt",
    )
    
    # Export model config
    model_info = {
        "model_type": "EmbeddingDropoutMLP",
        "input_dim": 768,
        "hidden_dim": config.get("model", {}).get("hidden_dim", 256),
        "num_classes": 10,
        "dropout": config.get("model", {}).get("dropout", 0.2),
        "dinov2_backbone": config.get("model", {}).get("dinov2_model", "dinov2_vitb14"),
        "epochs": epoch,
        "final_loss": float(loss),
    }
    
    export_model_config(
        model_type=model_info["model_type"],
        input_dim=model_info["input_dim"],
        hidden_dim=model_info["hidden_dim"],
        num_classes=model_info["num_classes"],
        dropout=model_info["dropout"],
        dinov2_backbone=model_info["dinov2_backbone"],
        training_config=config.get("training", {}),
        output_path=export_dir / "model_config.json",
    )
    
    # Export training embeddings
    export_train_embeddings(
        embeddings=train_embeddings,
        labels=train_labels,
        noisy_labels=train_noisy_labels,
        is_noisy=train_is_noisy,
        indices=train_indices,
        output_path=export_dir / "train_embeddings.pt",
    )
    
    # Export evaluation embeddings
    export_eval_embeddings(
        embeddings=eval_embeddings,
        clean_labels=eval_clean_labels,
        noisy_labels=eval_noisy_labels,
        is_noisy=eval_is_noisy,
        group_labels=eval_group_labels,
        indices=eval_indices,
        output_path=export_dir / "eval_embeddings.pt",
    )
    
    # Export per-sample signals
    export_per_sample_signals(
        eval_group_labels=eval_group_labels,
        eval_clean_labels=eval_clean_labels,
        eval_is_noisy=eval_is_noisy,
        signal_table=signal_table,
        output_path=export_dir / "per_sample_signals.csv",
    )
    
    # Export evaluation metadata
    export_evaluation_metadata(
        eval_group_labels=eval_group_labels,
        eval_clean_labels=eval_clean_labels,
        eval_noisy_labels=eval_noisy_labels,
        eval_is_noisy=eval_is_noisy,
        eval_original_indices=eval_indices,
        predictions=predictions,
        confidences=confidences,
        output_path=export_dir / "evaluation_metadata.csv",
    )
    
    # Export AUROC results
    export_auroc_results(
        auroc_rows=auroc_rows,
        output_path=export_dir / "auroc_results.csv",
    )
    
    # Export experiment config
    export_experiment_config(
        config=config,
        output_path=export_dir / "experiment_config.yaml",
    )
    
    # Create README
    create_readme(
        output_path=export_dir / "README.txt",
        timestamp=timestamp,
        model_info=model_info,
        train_size=int(train_embeddings.shape[0]),
        eval_size=int(eval_embeddings.shape[0]),
    )
    
    # Create ZIP package
    zip_path = output_base_dir / f"watsonx_export_{timestamp}.zip"
    create_watsonx_package(export_dir, zip_path)
    
    return export_dir, zip_path


# Made with Bob