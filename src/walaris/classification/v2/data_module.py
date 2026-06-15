"""
PyTorch Lightning DataModule for uncertainty classification.

Handles data loading, preprocessing, and splitting in a reusable way.
Integrates with Lightning's training infrastructure for automatic
data pipeline management.
"""

from typing import Optional

import torch
from torch.utils.data import DataLoader, Dataset

try:
    import pytorch_lightning as pl
    LIGHTNING_AVAILABLE = True
except ImportError:
    LIGHTNING_AVAILABLE = False
    # Create dummy base class for graceful degradation
    class pl:
        class LightningDataModule:
            pass


class UQDataModule(pl.LightningDataModule):
    """
    Lightning DataModule for uncertainty classification experiments.
    
    Handles:
    - Train/validation/test data loading
    - Batch size management
    - Worker configuration
    - Data preprocessing
    
    Args:
        train_dataset: Training dataset (FeatureDataset)
        val_dataset: Validation dataset (optional)
        test_dataset: Test dataset (optional)
        batch_size: Batch size for training
        num_workers: Number of data loading workers
        pin_memory: Whether to pin memory for faster GPU transfer
    
    Example:
        >>> data_module = UQDataModule(
        ...     train_dataset=train_dataset,
        ...     batch_size=256,
        ...     num_workers=4
        ... )
        >>> trainer = pl.Trainer(max_epochs=12)
        >>> trainer.fit(model, data_module)
    """
    
    def __init__(
        self,
        train_dataset: Dataset,
        val_dataset: Optional[Dataset] = None,
        test_dataset: Optional[Dataset] = None,
        batch_size: int = 256,
        num_workers: int = 0,
        pin_memory: bool = True,
    ):
        super().__init__()
        
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.test_dataset = test_dataset
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.pin_memory = pin_memory
    
    def train_dataloader(self) -> DataLoader:
        """Create training dataloader."""
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=self.num_workers > 0,
        )
    
    def val_dataloader(self) -> Optional[DataLoader]:
        """Create validation dataloader."""
        if self.val_dataset is None:
            return None
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=self.num_workers > 0,
        )
    
    def test_dataloader(self) -> Optional[DataLoader]:
        """Create test dataloader."""
        if self.test_dataset is None:
            return None
        return DataLoader(
            self.test_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            pin_memory=self.pin_memory,
            persistent_workers=self.num_workers > 0,
        )


# Made with Bob