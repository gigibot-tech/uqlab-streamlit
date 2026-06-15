"""Complete training pipeline with checkpoint saving and decision boundary visualization.

This script demonstrates a full training workflow that:
- Trains models on CIFAR-10 or synthetic data
- Saves checkpoints at regular intervals
- Visualizes decision boundaries at key checkpoints
- Integrates with ExperimentTracker for comprehensive logging
- Manages checkpoint cleanup to save disk space

Usage:
    # Train on synthetic 2D data (fast, good for testing)
    python train_with_checkpoints.py --dataset synthetic --epochs 50
    
    # Train on CIFAR-10 with visualization
    python train_with_checkpoints.py --dataset cifar10 --epochs 100 --viz-freq 20
    
    # Train with custom settings
    python train_with_checkpoints.py --dataset synthetic --model mlp \
        --epochs 100 --batch-size 64 --lr 0.001 --checkpoint-freq 10
"""

import argparse
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt

# Import our modules
from unified_tracker import ExperimentTracker
from decision_boundary_viz import (
    plot_decision_boundary,
    visualize_checkpoint,
    reduce_dimensions
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Model Definitions
# ============================================================================

class SimpleMLP(nn.Module):
    """Simple Multi-Layer Perceptron for classification.
    
    Architecture:
        - Input layer
        - 2 hidden layers with ReLU activation
        - Output layer with softmax
    """
    
    def __init__(self, input_dim: int, hidden_dim: int = 128, num_classes: int = 10):
        """Initialize MLP.
        
        Args:
            input_dim: Number of input features
            hidden_dim: Number of hidden units
            num_classes: Number of output classes
        """
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
    
    def forward(self, x):
        """Forward pass."""
        x = x.view(x.size(0), -1)  # Flatten
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x


class SimpleCNN(nn.Module):
    """Simple Convolutional Neural Network for image classification.
    
    Architecture:
        - 2 convolutional layers with max pooling
        - 2 fully connected layers
        - Suitable for CIFAR-10 (32x32 images)
    """
    
    def __init__(self, num_classes: int = 10, input_channels: int = 3):
        """Initialize CNN.
        
        Args:
            num_classes: Number of output classes
            input_channels: Number of input channels (3 for RGB)
        """
        super().__init__()
        self.conv1 = nn.Conv2d(input_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.25)
    
    def forward(self, x):
        """Forward pass."""
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)  # Flatten
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


# ============================================================================
# Data Loading Functions
# ============================================================================

def load_synthetic_data(
    n_samples: int = 1000,
    n_features: int = 2,
    n_classes: int = 3,
    noise: float = 0.1,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic classification data.
    
    Creates well-separated clusters for each class with controllable noise.
    
    Args:
        n_samples: Total number of samples
        n_features: Number of features (2 for easy visualization)
        n_classes: Number of classes
        noise: Standard deviation of Gaussian noise
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test)
    """
    np.random.seed(random_state)
    
    samples_per_class = n_samples // n_classes
    X_list = []
    y_list = []
    
    # Generate clusters for each class
    for class_idx in range(n_classes):
        # Create cluster center
        angle = 2 * np.pi * class_idx / n_classes
        center = np.array([3 * np.cos(angle), 3 * np.sin(angle)])
        
        # Generate samples around center
        X_class = np.random.randn(samples_per_class, n_features) * noise + center
        y_class = np.full(samples_per_class, class_idx)
        
        X_list.append(X_class)
        y_list.append(y_class)
    
    # Combine all classes
    X = np.vstack(X_list).astype(np.float32)
    y = np.hstack(y_list).astype(np.int64)
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    # Split into train/test
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    logger.info(f"Generated synthetic data: {X_train.shape[0]} train, {X_test.shape[0]} test samples")
    logger.info(f"Features: {n_features}, Classes: {n_classes}")
    
    return X_train, y_train, X_test, y_test


def load_cifar10_data(
    data_dir: str = "./data",
    subset_size: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load CIFAR-10 dataset.
    
    Args:
        data_dir: Directory to store/load data
        subset_size: Optional size to limit dataset (for faster training)
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test)
    """
    try:
        from torchvision import datasets, transforms
    except ImportError:
        raise ImportError("torchvision required for CIFAR-10. Install with: pip install torchvision")
    
    # Define transforms
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    
    # Load datasets
    train_dataset = datasets.CIFAR10(
        root=data_dir, train=True, download=True, transform=transform
    )
    test_dataset = datasets.CIFAR10(
        root=data_dir, train=False, download=True, transform=transform
    )
    
    # Convert to numpy arrays
    X_train = train_dataset.data.astype(np.float32) / 255.0
    y_train = np.array(train_dataset.targets, dtype=np.int64)
    X_test = test_dataset.data.astype(np.float32) / 255.0
    y_test = np.array(test_dataset.targets, dtype=np.int64)
    
    # Transpose to (N, C, H, W) format
    X_train = np.transpose(X_train, (0, 3, 1, 2))
    X_test = np.transpose(X_test, (0, 3, 1, 2))
    
    # Subset if requested
    if subset_size:
        X_train = X_train[:subset_size]
        y_train = y_train[:subset_size]
        X_test = X_test[:subset_size // 5]
        y_test = y_test[:subset_size // 5]
    
    logger.info(f"Loaded CIFAR-10: {X_train.shape[0]} train, {X_test.shape[0]} test samples")
    
    return X_train, y_train, X_test, y_test


# ============================================================================
# Checkpoint Management
# ============================================================================

class CheckpointManager:
    """Manages model checkpoints with automatic cleanup.
    
    Features:
        - Saves checkpoints with metadata
        - Keeps only N best checkpoints based on metric
        - Keeps only N most recent checkpoints
        - Organizes checkpoints in structured directory
    """
    
    def __init__(
        self,
        checkpoint_dir: str = "checkpoints",
        keep_best: int = 3,
        keep_recent: int = 5,
        metric_name: str = "val_accuracy"
    ):
        """Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory to save checkpoints
            keep_best: Number of best checkpoints to keep
            keep_recent: Number of recent checkpoints to keep
            metric_name: Metric to use for "best" selection
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.keep_best = keep_best
        self.keep_recent = keep_recent
        self.metric_name = metric_name
        self.checkpoints: List[Dict] = []
    
    def save_checkpoint(
        self,
        model: nn.Module,
        optimizer: optim.Optimizer,
        epoch: int,
        metrics: Dict[str, float],
        is_best: bool = False
    ) -> Path:
        """Save a checkpoint.
        
        Args:
            model: Model to save
            optimizer: Optimizer state
            epoch: Current epoch
            metrics: Dictionary of metrics
            is_best: Whether this is the best checkpoint so far
            
        Returns:
            Path to saved checkpoint
        """
        checkpoint_name = f"checkpoint_epoch_{epoch:04d}.pt"
        if is_best:
            checkpoint_name = f"best_{checkpoint_name}"
        
        checkpoint_path = self.checkpoint_dir / checkpoint_name
        
        # Save checkpoint
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'metrics': metrics,
        }, checkpoint_path)
        
        # Track checkpoint
        self.checkpoints.append({
            'path': checkpoint_path,
            'epoch': epoch,
            'metrics': metrics,
            'is_best': is_best
        })
        
        logger.info(f"Saved checkpoint: {checkpoint_path.name}")
        
        # Cleanup old checkpoints
        self._cleanup_checkpoints()
        
        return checkpoint_path
    
    def _cleanup_checkpoints(self):
        """Remove old checkpoints based on keep_best and keep_recent."""
        if len(self.checkpoints) <= max(self.keep_best, self.keep_recent):
            return
        
        # Sort by metric (descending) for best checkpoints
        sorted_by_metric = sorted(
            self.checkpoints,
            key=lambda x: x['metrics'].get(self.metric_name, 0),
            reverse=True
        )
        
        # Sort by epoch (descending) for recent checkpoints
        sorted_by_epoch = sorted(
            self.checkpoints,
            key=lambda x: x['epoch'],
            reverse=True
        )
        
        # Determine which to keep
        keep_paths = set()
        
        # Keep best N
        for ckpt in sorted_by_metric[:self.keep_best]:
            keep_paths.add(ckpt['path'])
        
        # Keep recent N
        for ckpt in sorted_by_epoch[:self.keep_recent]:
            keep_paths.add(ckpt['path'])
        
        # Keep explicitly marked as best
        for ckpt in self.checkpoints:
            if ckpt['is_best']:
                keep_paths.add(ckpt['path'])
        
        # Remove checkpoints not in keep list
        new_checkpoints = []
        for ckpt in self.checkpoints:
            if ckpt['path'] in keep_paths:
                new_checkpoints.append(ckpt)
            else:
                if ckpt['path'].exists():
                    ckpt['path'].unlink()
                    logger.debug(f"Removed old checkpoint: {ckpt['path'].name}")
        
        self.checkpoints = new_checkpoints
    
    def get_best_checkpoint(self) -> Optional[Path]:
        """Get path to best checkpoint."""
        if not self.checkpoints:
            return None
        
        best = max(
            self.checkpoints,
            key=lambda x: x['metrics'].get(self.metric_name, 0)
        )
        return best['path']
    
    def get_latest_checkpoint(self) -> Optional[Path]:
        """Get path to most recent checkpoint."""
        if not self.checkpoints:
            return None
        
        latest = max(self.checkpoints, key=lambda x: x['epoch'])
        return latest['path']


# ============================================================================
# Training Pipeline
# ============================================================================

class TrainingPipeline:
    """Complete training pipeline with checkpointing and visualization.
    
    Features:
        - Flexible model and dataset selection
        - Automatic checkpoint saving
        - Decision boundary visualization
        - Experiment tracking integration
        - Progress monitoring
    """
    
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        test_loader: DataLoader,
        criterion: nn.Module,
        optimizer: optim.Optimizer,
        device: str = "cpu",
        checkpoint_dir: str = "checkpoints",
        viz_dir: str = "visualizations",
        experiment_name: str = "training_experiment"
    ):
        """Initialize training pipeline.
        
        Args:
            model: PyTorch model to train
            train_loader: Training data loader
            test_loader: Test data loader
            criterion: Loss function
            optimizer: Optimizer
            device: Device to train on ('cpu' or 'cuda')
            checkpoint_dir: Directory for checkpoints
            viz_dir: Directory for visualizations
            experiment_name: Name for experiment tracking
        """
        self.model = model.to(device)
        self.train_loader = train_loader
        self.test_loader = test_loader
        self.criterion = criterion
        self.optimizer = optimizer
        self.device = device
        
        # Setup directories
        self.checkpoint_dir = Path(checkpoint_dir)
        self.viz_dir = Path(viz_dir)
        self.viz_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize managers
        self.checkpoint_manager = CheckpointManager(
            checkpoint_dir=checkpoint_dir,
            keep_best=3,
            keep_recent=5,
            metric_name="test_accuracy"
        )
        
        # Initialize experiment tracker
        self.tracker = ExperimentTracker(
            experiment_name=experiment_name,
            mlflow_uri=None  # Use JSON mode
        )
        
        # Training state
        self.current_epoch = 0
        self.best_accuracy = 0.0
        self.history = {
            'train_loss': [],
            'train_accuracy': [],
            'test_loss': [],
            'test_accuracy': []
        }
    
    def train_epoch(self) -> Tuple[float, float]:
        """Train for one epoch.
        
        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(self.train_loader):
            data, target = data.to(self.device), target.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Track metrics
            total_loss += loss.item()
            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()
        
        avg_loss = total_loss / len(self.train_loader)
        accuracy = 100.0 * correct / total
        
        return avg_loss, accuracy
    
    def evaluate(self) -> Tuple[float, float]:
        """Evaluate on test set.
        
        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in self.test_loader:
                data, target = data.to(self.device), target.to(self.device)
                
                output = self.model(data)
                loss = self.criterion(output, target)
                
                total_loss += loss.item()
                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()
        
        avg_loss = total_loss / len(self.test_loader)
        accuracy = 100.0 * correct / total
        
        return avg_loss, accuracy
    
    def visualize_decision_boundary(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        epoch: int,
        reduce_dims: bool = True
    ):
        """Create and save decision boundary visualization.
        
        Args:
            X_train: Training data
            y_train: Training labels
            X_test: Test data
            y_test: Test labels
            epoch: Current epoch number
            reduce_dims: Whether to apply dimensionality reduction
        """
        try:
            viz_path = self.viz_dir / f"boundary_epoch_{epoch:04d}.png"
            
            fig = plot_decision_boundary(
                self.model,
                X_train,
                y_train,
                X_test=X_test,
                y_test=y_test,
                reduce_dims=reduce_dims,
                reduction_method='tsne',
                title=f"Decision Boundary - Epoch {epoch}",
                save_path=viz_path,
                figsize=(14, 6)
            )
            
            plt.close(fig)
            
            # Log as artifact
            self.tracker.log_artifact(str(viz_path))
            logger.info(f"Saved visualization: {viz_path.name}")
            
        except Exception as e:
            logger.warning(f"Failed to create visualization: {e}")
    
    def train(
        self,
        num_epochs: int,
        checkpoint_freq: int = 10,
        viz_freq: int = 20,
        X_train_viz: Optional[np.ndarray] = None,
        y_train_viz: Optional[np.ndarray] = None,
        X_test_viz: Optional[np.ndarray] = None,
        y_test_viz: Optional[np.ndarray] = None,
        reduce_dims_viz: bool = True
    ):
        """Run complete training loop.
        
        Args:
            num_epochs: Number of epochs to train
            checkpoint_freq: Save checkpoint every N epochs
            viz_freq: Create visualization every N epochs
            X_train_viz: Training data for visualization (optional)
            y_train_viz: Training labels for visualization (optional)
            X_test_viz: Test data for visualization (optional)
            y_test_viz: Test labels for visualization (optional)
            reduce_dims_viz: Whether to reduce dimensions for visualization
        """
        logger.info("=" * 70)
        logger.info("Starting Training Pipeline")
        logger.info("=" * 70)
        
        # Start experiment tracking
        self.tracker.start_run(run_name=f"training_{num_epochs}_epochs")
        
        # Log hyperparameters
        self.tracker.log_params({
            'num_epochs': num_epochs,
            'batch_size': self.train_loader.batch_size,
            'learning_rate': self.optimizer.param_groups[0]['lr'],
            'optimizer': self.optimizer.__class__.__name__,
            'model': self.model.__class__.__name__,
            'device': self.device,
            'checkpoint_freq': checkpoint_freq,
            'viz_freq': viz_freq
        })
        
        try:
            for epoch in range(1, num_epochs + 1):
                self.current_epoch = epoch
                
                # Train
                train_loss, train_acc = self.train_epoch()
                
                # Evaluate
                test_loss, test_acc = self.evaluate()
                
                # Update history
                self.history['train_loss'].append(train_loss)
                self.history['train_accuracy'].append(train_acc)
                self.history['test_loss'].append(test_loss)
                self.history['test_accuracy'].append(test_acc)
                
                # Log metrics
                self.tracker.log_metrics({
                    'train_loss': train_loss,
                    'train_accuracy': train_acc,
                    'test_loss': test_loss,
                    'test_accuracy': test_acc
                }, step=epoch)
                
                # Print progress
                logger.info(
                    f"Epoch {epoch}/{num_epochs} | "
                    f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.2f}% | "
                    f"Test Loss: {test_loss:.4f}, Acc: {test_acc:.2f}%"
                )
                
                # Save checkpoint
                if epoch % checkpoint_freq == 0 or epoch == num_epochs:
                    is_best = test_acc > self.best_accuracy
                    if is_best:
                        self.best_accuracy = test_acc
                    
                    checkpoint_path = self.checkpoint_manager.save_checkpoint(
                        self.model,
                        self.optimizer,
                        epoch,
                        {
                            'train_loss': train_loss,
                            'train_accuracy': train_acc,
                            'test_loss': test_loss,
                            'test_accuracy': test_acc
                        },
                        is_best=is_best
                    )
                    
                    self.tracker.log_artifact(str(checkpoint_path))
                
                # Create visualization
                if (epoch % viz_freq == 0 or epoch == num_epochs) and X_train_viz is not None:
                    self.visualize_decision_boundary(
                        X_train_viz,
                        y_train_viz,
                        X_test_viz,
                        y_test_viz,
                        epoch,
                        reduce_dims=reduce_dims_viz
                    )
            
            # Training complete
            logger.info("=" * 70)
            logger.info("Training Complete!")
            logger.info(f"Best Test Accuracy: {self.best_accuracy:.2f}%")
            logger.info(f"Checkpoints saved in: {self.checkpoint_dir}")
            logger.info(f"Visualizations saved in: {self.viz_dir}")
            logger.info("=" * 70)
            
            # Save final training curves
            self._plot_training_curves()
            
        except KeyboardInterrupt:
            logger.info("\nTraining interrupted by user")
        
        finally:
            # End experiment tracking
            self.tracker.end_run()
    
    def _plot_training_curves(self):
        """Plot and save training curves."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        epochs = range(1, len(self.history['train_loss']) + 1)
        
        # Loss plot
        axes[0].plot(epochs, self.history['train_loss'], label='Train Loss', marker='o')
        axes[0].plot(epochs, self.history['test_loss'], label='Test Loss', marker='s')
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Loss')
        axes[0].set_title('Training and Test Loss')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Accuracy plot
        axes[1].plot(epochs, self.history['train_accuracy'], label='Train Accuracy', marker='o')
        axes[1].plot(epochs, self.history['test_accuracy'], label='Test Accuracy', marker='s')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Accuracy (%)')
        axes[1].set_title('Training and Test Accuracy')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        curves_path = self.viz_dir / "training_curves.png"
        fig.savefig(curves_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        self.tracker.log_artifact(str(curves_path))
        logger.info(f"Saved training curves: {curves_path.name}")


# ============================================================================
# Main Execution
# ============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train models with checkpoint saving and visualization",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Dataset options
    parser.add_argument(
        '--dataset',
        type=str,
        choices=['synthetic', 'cifar10'],
        default='synthetic',
        help='Dataset to use for training'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='./data',
        help='Directory for dataset storage'
    )
    parser.add_argument(
        '--n-samples',
        type=int,
        default=1000,
        help='Number of samples for synthetic data'
    )
    parser.add_argument(
        '--n-features',
        type=int,
        default=2,
        help='Number of features for synthetic data'
    )
    parser.add_argument(
        '--n-classes',
        type=int,
        default=3,
        help='Number of classes'
    )
    
    # Model options
    parser.add_argument(
        '--model',
        type=str,
        choices=['mlp', 'cnn'],
        default='mlp',
        help='Model architecture to use'
    )
    parser.add_argument(
        '--hidden-dim',
        type=int,
        default=128,
        help='Hidden dimension for MLP'
    )
    
    # Training options
    parser.add_argument(
        '--epochs',
        type=int,
        default=50,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for training'
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=0.001,
        help='Learning rate'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cuda' if torch.cuda.is_available() else 'cpu',
        help='Device to train on'
    )
    
    # Checkpoint and visualization options
    parser.add_argument(
        '--checkpoint-freq',
        type=int,
        default=10,
        help='Save checkpoint every N epochs'
    )
    parser.add_argument(
        '--viz-freq',
        type=int,
        default=20,
        help='Create visualization every N epochs'
    )
    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='checkpoints',
        help='Directory for checkpoints'
    )
    parser.add_argument(
        '--viz-dir',
        type=str,
        default='visualizations',
        help='Directory for visualizations'
    )
    parser.add_argument(
        '--experiment-name',
        type=str,
        default='training_experiment',
        help='Name for experiment tracking'
    )
    
    # Other options
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Disable decision boundary visualization'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_args()
    
    # Set random seeds
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    
    logger.info("Configuration:")
    for arg, value in vars(args).items():
        logger.info(f"  {arg}: {value}")
    
    # Load data
    logger.info(f"\nLoading {args.dataset} dataset...")
    if args.dataset == 'synthetic':
        X_train, y_train, X_test, y_test = load_synthetic_data(
            n_samples=args.n_samples,
            n_features=args.n_features,
            n_classes=args.n_classes,
            random_state=args.seed
        )
        input_dim = args.n_features
        num_classes = args.n_classes
        
    elif args.dataset == 'cifar10':
        X_train, y_train, X_test, y_test = load_cifar10_data(
            data_dir=args.data_dir,
            subset_size=5000  # Use subset for faster training
        )
        input_dim = 32 * 32 * 3  # Flattened CIFAR-10 image
        num_classes = 10
    
    # Create data loaders
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.LongTensor(y_train)
    )
    test_dataset = TensorDataset(
        torch.FloatTensor(X_test),
        torch.LongTensor(y_test)
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False
    )
    
    # Create model
    logger.info(f"\nCreating {args.model.upper()} model...")
    if args.model == 'mlp':
        model = SimpleMLP(
            input_dim=input_dim,
            hidden_dim=args.hidden_dim,
            num_classes=num_classes
        )
    elif args.model == 'cnn':
        if args.dataset != 'cifar10':
            logger.warning("CNN is designed for CIFAR-10, using MLP instead")
            model = SimpleMLP(input_dim=input_dim, hidden_dim=args.hidden_dim, num_classes=num_classes)
        else:
            model = SimpleCNN(num_classes=num_classes)
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Create optimizer and criterion
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()
    
    # Create training pipeline
    pipeline = TrainingPipeline(
        model=model,
        train_loader=train_loader,
        test_loader=test_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=args.device,
        checkpoint_dir=args.checkpoint_dir,
        viz_dir=args.viz_dir,
        experiment_name=args.experiment_name
    )
    
    # Prepare visualization data (use subset for speed)
    if not args.no_viz and args.dataset == 'synthetic':
        viz_size = min(500, len(X_train))
        X_train_viz = X_train[:viz_size]
        y_train_viz = y_train[:viz_size]
        X_test_viz = X_test[:viz_size // 4]
        y_test_viz = y_test[:viz_size // 4]
        reduce_dims_viz = args.n_features > 2
    elif not args.no_viz and args.dataset == 'cifar10':
        # For CIFAR-10, use smaller subset and always reduce dimensions
        viz_size = 300
        X_train_viz = X_train[:viz_size]
        y_train_viz = y_train[:viz_size]
        X_test_viz = X_test[:viz_size // 4]
        y_test_viz = y_test[:viz_size // 4]
        reduce_dims_viz = True
    else:
        X_train_viz = None
        y_train_viz = None
        X_test_viz = None
        y_test_viz = None
        reduce_dims_viz = False
    
    # Train model
    pipeline.train(
        num_epochs=args.epochs,
        checkpoint_freq=args.checkpoint_freq,
        viz_freq=args.viz_freq,
        X_train_viz=X_train_viz,
        y_train_viz=y_train_viz,
        X_test_viz=X_test_viz,
        y_test_viz=y_test_viz,
        reduce_dims_viz=reduce_dims_viz
    )
    
    # Print summary
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"Dataset: {args.dataset}")
    print(f"Model: {args.model.upper()}")
    print(f"Epochs: {args.epochs}")
    print(f"Best Test Accuracy: {pipeline.best_accuracy:.2f}%")
    print(f"\nOutputs:")
    print(f"  Checkpoints: {args.checkpoint_dir}/")
    print(f"  Visualizations: {args.viz_dir}/")
    print(f"  Experiment logs: experiments/{args.experiment_name}/")
    print("=" * 70)


if __name__ == "__main__":
    main()


# Made with Bob