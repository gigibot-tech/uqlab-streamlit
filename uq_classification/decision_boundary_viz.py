"""Decision boundary visualization for model checkpoints.

This module provides tools to visualize decision boundaries of trained models,
supporting both 2D data and high-dimensional data with dimensionality reduction.
Compatible with PyTorch models and the ExperimentTracker system.
"""

import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

# Optional imports with graceful fallbacks
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    warnings.warn("PyTorch not available. Checkpoint loading will be limited.")

try:
    from sklearn.manifold import TSNE
    TSNE_AVAILABLE = True
except ImportError:
    TSNE_AVAILABLE = False

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reduce_dimensions(
    X: np.ndarray,
    method: str = "tsne",
    n_components: int = 2,
    random_state: int = 42,
    **kwargs
) -> np.ndarray:
    """Reduce high-dimensional data to 2D for visualization.
    
    Args:
        X: Input data of shape (n_samples, n_features)
        method: Dimensionality reduction method ('tsne' or 'umap')
        n_components: Number of dimensions to reduce to (default: 2)
        random_state: Random seed for reproducibility
        **kwargs: Additional arguments passed to the reduction method
        
    Returns:
        Reduced data of shape (n_samples, n_components)
        
    Raises:
        ValueError: If method is not supported or required library is missing
        
    Examples:
        >>> X = np.random.randn(100, 50)
        >>> X_2d = reduce_dimensions(X, method='tsne')
        >>> X_2d.shape
        (100, 2)
    """
    if X.shape[1] == n_components:
        logger.info(f"Data already has {n_components} dimensions, skipping reduction")
        return X
    
    method = method.lower()
    
    if method == "tsne":
        if not TSNE_AVAILABLE:
            raise ValueError("t-SNE requires scikit-learn. Install with: pip install scikit-learn")
        
        logger.info(f"Applying t-SNE reduction from {X.shape[1]} to {n_components} dimensions")
        tsne = TSNE(
            n_components=n_components,
            random_state=random_state,
            **kwargs
        )
        return tsne.fit_transform(X)
    
    elif method == "umap":
        if not UMAP_AVAILABLE:
            raise ValueError("UMAP requires umap-learn. Install with: pip install umap-learn")
        
        logger.info(f"Applying UMAP reduction from {X.shape[1]} to {n_components} dimensions")
        reducer = umap.UMAP(
            n_components=n_components,
            random_state=random_state,
            **kwargs
        )
        return reducer.fit_transform(X)
    
    else:
        raise ValueError(f"Unsupported method: {method}. Use 'tsne' or 'umap'")


def create_meshgrid(
    X: np.ndarray,
    resolution: int = 100,
    padding: float = 0.5
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create a meshgrid for decision boundary visualization.
    
    Args:
        X: Input data of shape (n_samples, 2) - must be 2D
        resolution: Number of points per dimension in the grid
        padding: Padding around data bounds as fraction of range
        
    Returns:
        Tuple of (xx, yy, grid_points) where:
            - xx, yy: Meshgrid coordinate arrays
            - grid_points: Flattened grid points of shape (resolution^2, 2)
            
    Raises:
        ValueError: If X is not 2-dimensional
        
    Examples:
        >>> X = np.random.randn(100, 2)
        >>> xx, yy, grid = create_meshgrid(X, resolution=50)
        >>> xx.shape
        (50, 50)
    """
    if X.shape[1] != 2:
        raise ValueError(f"Input must be 2D, got shape {X.shape}")
    
    # Calculate bounds with padding
    x_min, x_max = X[:, 0].min(), X[:, 0].max()
    y_min, y_max = X[:, 1].min(), X[:, 1].max()
    
    x_range = x_max - x_min
    y_range = y_max - y_min
    
    x_min -= padding * x_range
    x_max += padding * x_range
    y_min -= padding * y_range
    y_max += padding * y_range
    
    # Create meshgrid
    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, resolution),
        np.linspace(y_min, y_max, resolution)
    )
    
    # Flatten for model prediction
    grid_points = np.c_[xx.ravel(), yy.ravel()]
    
    logger.debug(f"Created meshgrid: {resolution}x{resolution} points, "
                f"bounds: x=[{x_min:.2f}, {x_max:.2f}], y=[{y_min:.2f}, {y_max:.2f}]")
    
    return xx, yy, grid_points


def load_checkpoint(
    checkpoint_path: Union[str, Path],
    model: Optional[Any] = None,
    device: str = "cpu"
) -> Any:
    """Load a model from a checkpoint file.
    
    Supports PyTorch .pt/.pth files. If a model is provided, loads state_dict
    into it. Otherwise, attempts to load the entire model.
    
    Args:
        checkpoint_path: Path to checkpoint file
        model: Optional model instance to load weights into
        device: Device to load model on ('cpu' or 'cuda')
        
    Returns:
        Loaded model
        
    Raises:
        FileNotFoundError: If checkpoint file doesn't exist
        ValueError: If PyTorch is not available
        RuntimeError: If checkpoint loading fails
        
    Examples:
        >>> model = load_checkpoint('model_epoch_10.pt')
        >>> # Or with existing model
        >>> model = MyModel()
        >>> model = load_checkpoint('weights.pt', model=model)
    """
    checkpoint_path = Path(checkpoint_path)
    
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    if not TORCH_AVAILABLE:
        raise ValueError("PyTorch is required for checkpoint loading. "
                        "Install with: pip install torch")
    
    logger.info(f"Loading checkpoint from: {checkpoint_path}")
    
    try:
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
        
        if model is not None:
            # Load state dict into provided model
            if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                model.load_state_dict(checkpoint['state_dict'])
            elif isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            elif isinstance(checkpoint, dict):
                # Assume the dict itself is the state dict
                model.load_state_dict(checkpoint)
            else:
                raise RuntimeError("Checkpoint format not recognized")
            
            model.to(device)
            model.eval()
            logger.info("Loaded state dict into provided model")
            return model
        else:
            # Try to load entire model
            if isinstance(checkpoint, nn.Module):
                checkpoint.to(device)
                checkpoint.eval()
                logger.info("Loaded complete model from checkpoint")
                return checkpoint
            elif isinstance(checkpoint, dict) and 'model' in checkpoint:
                checkpoint['model'].to(device)
                checkpoint['model'].eval()
                logger.info("Loaded model from checkpoint dict")
                return checkpoint['model']
            else:
                raise RuntimeError(
                    "Could not load model. Checkpoint doesn't contain a model. "
                    "Please provide a model instance to load weights into."
                )
    
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        raise RuntimeError(f"Checkpoint loading failed: {e}") from e


def plot_decision_boundary(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    X_test: Optional[np.ndarray] = None,
    y_test: Optional[np.ndarray] = None,
    reduce_dims: bool = True,
    reduction_method: str = "tsne",
    resolution: int = 200,
    figsize: Tuple[int, int] = (12, 5),
    cmap: str = "RdYlBu",
    alpha: float = 0.3,
    title: Optional[str] = None,
    save_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> plt.Figure:
    """Plot decision boundaries for a trained model.
    
    Handles both 2D data directly and high-dimensional data with automatic
    dimensionality reduction. Creates visualizations with decision boundaries,
    training points, and optional test points.
    
    Args:
        model: Trained model with predict or forward method
        X: Training data of shape (n_samples, n_features)
        y: Training labels of shape (n_samples,)
        X_test: Optional test data of shape (n_test_samples, n_features)
        y_test: Optional test labels of shape (n_test_samples,)
        reduce_dims: Whether to apply dimensionality reduction for high-dim data
        reduction_method: Method for reduction ('tsne' or 'umap')
        resolution: Grid resolution for decision boundary
        figsize: Figure size as (width, height)
        cmap: Colormap for decision boundary
        alpha: Transparency for decision boundary
        title: Optional plot title
        save_path: Optional path to save figure
        **kwargs: Additional arguments for dimensionality reduction
        
    Returns:
        Matplotlib figure object
        
    Raises:
        ValueError: If data dimensions are invalid
        
    Examples:
        >>> model = train_model(X_train, y_train)
        >>> fig = plot_decision_boundary(model, X_train, y_train, X_test, y_test)
        >>> plt.show()
    """
    # Validate inputs
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"X and y must have same number of samples: {X.shape[0]} vs {y.shape[0]}")
    
    if X_test is not None and y_test is not None:
        if X_test.shape[0] != y_test.shape[0]:
            raise ValueError(f"X_test and y_test must have same number of samples")
    
    # Handle dimensionality reduction
    if X.shape[1] > 2 and reduce_dims:
        logger.info(f"Reducing dimensions from {X.shape[1]} to 2 using {reduction_method}")
        X_2d = reduce_dimensions(X, method=reduction_method, **kwargs)
        
        if X_test is not None:
            # Combine for consistent reduction
            X_combined = np.vstack([X, X_test])
            X_combined_2d = reduce_dimensions(X_combined, method=reduction_method, **kwargs)
            X_test_2d = X_combined_2d[len(X):]
        else:
            X_test_2d = None
    elif X.shape[1] == 2:
        X_2d = X
        X_test_2d = X_test
    else:
        raise ValueError(f"Data must be 2D or reduce_dims must be True. Got shape: {X.shape}")
    
    # Create meshgrid
    xx, yy, grid_points = create_meshgrid(X_2d, resolution=resolution)
    
    # Get predictions on grid
    logger.info("Computing decision boundary predictions...")
    try:
        if TORCH_AVAILABLE and isinstance(model, nn.Module):
            # PyTorch model
            model.eval()
            with torch.no_grad():
                grid_tensor = torch.FloatTensor(grid_points)
                if next(model.parameters()).is_cuda:
                    grid_tensor = grid_tensor.cuda()
                
                predictions = model(grid_tensor)
                
                # Handle different output formats
                if isinstance(predictions, torch.Tensor):
                    if predictions.dim() > 1 and predictions.shape[1] > 1:
                        # Multi-class: take argmax
                        Z = predictions.argmax(dim=1).cpu().numpy()
                    else:
                        # Binary: threshold at 0.5
                        Z = (predictions.squeeze() > 0.5).cpu().numpy().astype(int)
                else:
                    Z = predictions
        else:
            # Scikit-learn style model
            if hasattr(model, 'predict'):
                Z = model.predict(grid_points)
            elif hasattr(model, 'forward'):
                Z = model.forward(grid_points)
            else:
                raise ValueError("Model must have 'predict' or 'forward' method")
        
        Z = Z.reshape(xx.shape)
    
    except Exception as e:
        logger.error(f"Failed to compute predictions: {e}")
        raise RuntimeError(f"Prediction failed: {e}") from e
    
    # Create figure
    n_plots = 2 if X_test is not None else 1
    fig, axes = plt.subplots(1, n_plots, figsize=figsize)
    if n_plots == 1:
        axes = [axes]
    
    # Get unique classes for colors
    unique_classes = np.unique(y)
    n_classes = len(unique_classes)
    
    # Create colormaps
    if n_classes == 2:
        colors = ['#FF6B6B', '#4ECDC4']
    else:
        colors = plt.cm.get_cmap('tab10')(np.linspace(0, 1, n_classes))
    
    # Plot training data
    ax = axes[0]
    ax.contourf(xx, yy, Z, alpha=alpha, cmap=cmap, levels=n_classes - 1)
    
    for idx, class_label in enumerate(unique_classes):
        mask = y == class_label
        ax.scatter(
            X_2d[mask, 0], X_2d[mask, 1],
            c=[colors[idx]], label=f'Train Class {class_label}',
            edgecolors='black', linewidth=0.5, s=50
        )
    
    ax.set_xlabel('Feature 1' if X.shape[1] == 2 else 'Component 1')
    ax.set_ylabel('Feature 2' if X.shape[1] == 2 else 'Component 2')
    ax.set_title(title or 'Decision Boundary - Training Data')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot test data if provided
    if X_test is not None and y_test is not None:
        ax = axes[1]
        ax.contourf(xx, yy, Z, alpha=alpha, cmap=cmap, levels=n_classes - 1)
        
        for idx, class_label in enumerate(unique_classes):
            mask = y_test == class_label
            if mask.any():
                ax.scatter(
                    X_test_2d[mask, 0], X_test_2d[mask, 1],
                    c=[colors[idx]], label=f'Test Class {class_label}',
                    edgecolors='black', linewidth=0.5, s=50, marker='s'
                )
        
        ax.set_xlabel('Feature 1' if X.shape[1] == 2 else 'Component 1')
        ax.set_ylabel('Feature 2' if X.shape[1] == 2 else 'Component 2')
        ax.set_title('Decision Boundary - Test Data')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved figure to: {save_path}")
    
    return fig


def visualize_checkpoint(
    checkpoint_path: Union[str, Path],
    X: np.ndarray,
    y: np.ndarray,
    model: Optional[Any] = None,
    X_test: Optional[np.ndarray] = None,
    y_test: Optional[np.ndarray] = None,
    save_dir: Optional[Union[str, Path]] = None,
    **plot_kwargs
) -> Tuple[plt.Figure, Optional[Path]]:
    """Visualize decision boundary from a checkpoint file.
    
    Loads a model from checkpoint and generates decision boundary visualization.
    
    Args:
        checkpoint_path: Path to model checkpoint
        X: Training data
        y: Training labels
        model: Optional model instance to load weights into
        X_test: Optional test data
        y_test: Optional test labels
        save_dir: Optional directory to save visualization
        **plot_kwargs: Additional arguments passed to plot_decision_boundary
        
    Returns:
        Tuple of (figure, save_path) where save_path is None if not saved
        
    Examples:
        >>> fig, path = visualize_checkpoint(
        ...     'checkpoints/model_epoch_10.pt',
        ...     X_train, y_train,
        ...     save_dir='visualizations'
        ... )
    """
    checkpoint_path = Path(checkpoint_path)
    
    # Load model
    loaded_model = load_checkpoint(checkpoint_path, model=model)
    
    # Generate title from checkpoint name
    if 'title' not in plot_kwargs:
        plot_kwargs['title'] = f"Decision Boundary - {checkpoint_path.stem}"
    
    # Determine save path
    save_path = None
    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"{checkpoint_path.stem}_boundary.png"
        plot_kwargs['save_path'] = save_path
    
    # Create visualization
    fig = plot_decision_boundary(
        loaded_model, X, y,
        X_test=X_test, y_test=y_test,
        **plot_kwargs
    )
    
    return fig, save_path


def visualize_checkpoints_batch(
    checkpoint_paths: Union[List[Union[str, Path]], str, Path],
    X: np.ndarray,
    y: np.ndarray,
    model: Optional[Any] = None,
    X_test: Optional[np.ndarray] = None,
    y_test: Optional[np.ndarray] = None,
    save_dir: Union[str, Path] = "visualizations",
    pattern: str = "*.pt",
    **plot_kwargs
) -> List[Path]:
    """Generate decision boundary visualizations for multiple checkpoints.
    
    Args:
        checkpoint_paths: List of checkpoint paths or directory containing checkpoints
        X: Training data
        y: Training labels
        model: Optional model instance to load weights into
        X_test: Optional test data
        y_test: Optional test labels
        save_dir: Directory to save visualizations
        pattern: File pattern for finding checkpoints (if checkpoint_paths is a directory)
        **plot_kwargs: Additional arguments passed to plot_decision_boundary
        
    Returns:
        List of paths to generated visualization images
        
    Examples:
        >>> # From list of checkpoints
        >>> paths = visualize_checkpoints_batch(
        ...     ['model_e1.pt', 'model_e2.pt'],
        ...     X_train, y_train
        ... )
        >>> 
        >>> # From directory
        >>> paths = visualize_checkpoints_batch(
        ...     'checkpoints/',
        ...     X_train, y_train,
        ...     pattern='*.pth'
        ... )
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle directory input
    if isinstance(checkpoint_paths, (str, Path)):
        checkpoint_dir = Path(checkpoint_paths)
        if checkpoint_dir.is_dir():
            checkpoint_paths = sorted(checkpoint_dir.glob(pattern))
            logger.info(f"Found {len(checkpoint_paths)} checkpoints in {checkpoint_dir}")
        else:
            checkpoint_paths = [checkpoint_dir]
    
    if not checkpoint_paths:
        logger.warning("No checkpoints found")
        return []
    
    generated_paths = []
    
    for i, checkpoint_path in enumerate(checkpoint_paths):
        checkpoint_path = Path(checkpoint_path)
        logger.info(f"Processing checkpoint {i+1}/{len(checkpoint_paths)}: {checkpoint_path.name}")
        
        try:
            fig, save_path = visualize_checkpoint(
                checkpoint_path, X, y,
                model=model,
                X_test=X_test, y_test=y_test,
                save_dir=save_dir,
                **plot_kwargs
            )
            
            if save_path:
                generated_paths.append(save_path)
            
            # Close figure to free memory
            plt.close(fig)
            
        except Exception as e:
            logger.error(f"Failed to process {checkpoint_path.name}: {e}")
            continue
    
    logger.info(f"Generated {len(generated_paths)} visualizations in {save_dir}")
    return generated_paths


# Made with Bob