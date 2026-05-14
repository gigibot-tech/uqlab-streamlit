"""
PyTorch Lightning module for uncertainty classification.

This module provides a LightningModule wrapper around FeatureDropoutMLP,
enabling automatic GPU support, distributed training, checkpointing, and
integration with various loggers (MLflow, TensorBoard, CSV).

Key benefits over manual training:
- Automatic device placement and multi-GPU support
- Built-in checkpointing and early stopping
- Seamless logger integration
- ~100 lines of boilerplate eliminated
- Better code organization and testability
"""

from typing import Any, Dict, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

try:
    import pytorch_lightning as pl
    try:
        from pytorch_lightning.utilities.types import STEP_OUTPUT
    except ImportError:
        STEP_OUTPUT = dict  # Fallback for older versions
    LIGHTNING_AVAILABLE = True
except ImportError:
    LIGHTNING_AVAILABLE = False
    STEP_OUTPUT = dict
    # Create dummy base class for graceful degradation
    class pl:
        class LightningModule:
            pass

from .models import FeatureDropoutMLP


class UQClassificationModule(pl.LightningModule):
    """
    Lightning module for uncertainty quantification classification.
    
    Wraps FeatureDropoutMLP with Lightning's training infrastructure.
    Automatically handles:
    - Device placement (CPU/GPU/multi-GPU)
    - Training/validation loops
    - Metric logging
    - Checkpointing
    - MC Dropout inference
    
    Args:
        input_dim: Dimension of input features
        num_classes: Number of output classes
        hidden_dim: Hidden layer dimension
        dropout: Dropout probability for MC Dropout
        learning_rate: Learning rate for optimizer
        weight_decay: L2 regularization strength
    
    Example:
        >>> module = UQClassificationModule(
        ...     input_dim=384,
        ...     num_classes=10,
        ...     hidden_dim=256,
        ...     dropout=0.2,
        ...     learning_rate=1e-3,
        ...     weight_decay=1e-4
        ... )
        >>> trainer = pl.Trainer(max_epochs=12, accelerator="auto")
        >>> trainer.fit(module, train_dataloader)
    """
    
    def __init__(
        self,
        input_dim: int,
        num_classes: int = 10,
        hidden_dim: int = 256,
        dropout: float = 0.2,
        learning_rate: float = 1e-3,
        weight_decay: float = 1e-4,
    ):
        super().__init__()
        
        # Save hyperparameters for checkpointing and logging
        self.save_hyperparameters()
        
        # Create model
        self.model = FeatureDropoutMLP(
            input_dim=input_dim,
            num_classes=num_classes,
            hidden_dim=hidden_dim,
            dropout=dropout,
        )
        
        # Loss function
        self.criterion = nn.CrossEntropyLoss()
        
        # Store hyperparameters for optimizer
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the model."""
        return self.model(x)
    
    def training_step(self, batch: tuple, batch_idx: int) -> dict:
        """
        Training step - called for each batch.
        
        Lightning automatically:
        - Moves batch to correct device
        - Calls backward()
        - Updates weights
        - Logs metrics
        """
        x, y = batch
        logits = self.forward(x)
        loss = self.criterion(logits, y)
        
        # Calculate accuracy
        preds = logits.argmax(dim=1)
        acc = (preds == y).float().mean()
        
        # Log metrics (automatically sent to all configured loggers)
        self.log('train_loss', loss, on_step=False, on_epoch=True, prog_bar=True)
        self.log('train_acc', acc, on_step=False, on_epoch=True, prog_bar=True)
        
        return loss
    
    def validation_step(self, batch: tuple, batch_idx: int) -> dict:
        """
        Validation step - called for each validation batch.
        
        Used for early stopping and model selection.
        """
        x, y = batch
        logits = self.forward(x)
        loss = self.criterion(logits, y)
        
        # Calculate accuracy
        preds = logits.argmax(dim=1)
        acc = (preds == y).float().mean()
        
        # Log metrics
        self.log('val_loss', loss, on_step=False, on_epoch=True, prog_bar=True)
        self.log('val_acc', acc, on_step=False, on_epoch=True, prog_bar=True)
        
        return loss
    
    def configure_optimizers(self) -> Dict[str, Any]:
        """
        Configure optimizer and learning rate scheduler.
        
        Lightning automatically calls this to set up training.
        """
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )
        
        # Optional: Add learning rate scheduler
        # scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        #     optimizer, mode='min', factor=0.5, patience=5
        # )
        # return {
        #     'optimizer': optimizer,
        #     'lr_scheduler': scheduler,
        #     'monitor': 'val_loss'
        # }
        
        return optimizer
    
    @torch.no_grad()
    def mc_forward(self, x: torch.Tensor, n_passes: int = 20) -> torch.Tensor:
        """
        Perform Monte Carlo Dropout forward passes.
        
        Args:
            x: Input features [batch_size, input_dim]
            n_passes: Number of stochastic forward passes
            
        Returns:
            predictions: Stacked softmax predictions [n_passes, batch_size, num_classes]
        """
        return self.model.mc_forward(x, n_passes=n_passes)
    
    def enable_dropout(self) -> None:
        """Enable dropout layers for MC Dropout inference."""
        self.model.enable_dropout()


def check_lightning_available() -> bool:
    """Check if PyTorch Lightning is available."""
    return LIGHTNING_AVAILABLE


def print_lightning_instructions() -> None:
    """Print installation instructions for PyTorch Lightning."""
    print("\n" + "="*70)
    print("⚠️  PyTorch Lightning not found")
    print("="*70)
    print("\nPyTorch Lightning provides:")
    print("  • Automatic GPU/multi-GPU support")
    print("  • Built-in checkpointing and early stopping")
    print("  • Seamless logger integration (MLflow, TensorBoard, etc.)")
    print("  • Cleaner, more maintainable code")
    print("\nInstall with:")
    print("  pip install pytorch-lightning")
    print("\nFalling back to manual training loop...")
    print("="*70 + "\n")


# Made with Bob