"""
Experiment tracking with graceful degradation.

Supports MLflow, TensorBoard, and CSV logging with automatic fallback.
Provides a unified interface regardless of which tracking backend is available.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import torch

# Check for optional tracking dependencies
try:
    import pytorch_lightning as pl
    from pytorch_lightning.loggers import MLFlowLogger
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    MLFlowLogger = None

try:
    from pytorch_lightning.loggers import TensorBoardLogger
    TENSORBOARD_AVAILABLE = True
except ImportError:
    TENSORBOARD_AVAILABLE = False
    TensorBoardLogger = None

try:
    from pytorch_lightning.loggers import CSVLogger
    CSV_LOGGER_AVAILABLE = True
except ImportError:
    CSV_LOGGER_AVAILABLE = False
    CSVLogger = None


def create_logger(
    experiment_name: str,
    run_name: str,
    save_dir: Union[str, Path],
    tracking_uri: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Create the best available logger with graceful degradation.
    
    Priority:
    1. MLflow (if available and tracking_uri provided)
    2. TensorBoard (if available)
    3. CSV (fallback)
    
    Args:
        experiment_name: Name of the experiment
        run_name: Name of this specific run
        save_dir: Directory to save logs
        tracking_uri: MLflow tracking URI (optional)
        tags: Additional tags for the run
        
    Returns:
        Logger instance (MLFlowLogger, TensorBoardLogger, or CSVLogger)
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Try MLflow first (best option for research)
    if MLFLOW_AVAILABLE and tracking_uri:
        try:
            logger = MLFlowLogger(
                experiment_name=experiment_name,
                run_name=run_name,
                tracking_uri=tracking_uri,
                tags=tags or {},
            )
            print(f"✅ Using MLflow logger (tracking_uri: {tracking_uri})")
            return logger
        except Exception as e:
            print(f"⚠️  MLflow logger failed: {e}")
            print("   Falling back to next available logger...")
    
    # Try TensorBoard (good visualization)
    if TENSORBOARD_AVAILABLE:
        try:
            logger = TensorBoardLogger(
                save_dir=str(save_dir),
                name=experiment_name,
                version=run_name,
            )
            print(f"✅ Using TensorBoard logger (save_dir: {save_dir})")
            print(f"   View with: tensorboard --logdir {save_dir}")
            return logger
        except Exception as e:
            print(f"⚠️  TensorBoard logger failed: {e}")
            print("   Falling back to CSV logger...")
    
    # Fallback to CSV (always works)
    if CSV_LOGGER_AVAILABLE:
        logger = CSVLogger(
            save_dir=str(save_dir),
            name=experiment_name,
            version=run_name,
        )
        print(f"✅ Using CSV logger (save_dir: {save_dir})")
        return logger
    
    # If even CSV logger is not available, return None
    print("⚠️  No logger available. Metrics will not be logged.")
    return None


def print_tracking_status() -> None:
    """Print status of available tracking backends."""
    print("\n" + "="*70)
    print("📊 Experiment Tracking Status")
    print("="*70)
    
    if MLFLOW_AVAILABLE:
        print("✅ MLflow: Available")
        print("   • Best for research: experiment comparison, model registry")
        print("   • View UI: mlflow ui --backend-store-uri <tracking_uri>")
    else:
        print("⚠️  MLflow: Not installed")
        print("   • Install: pip install mlflow")
    
    print()
    
    if TENSORBOARD_AVAILABLE:
        print("✅ TensorBoard: Available")
        print("   • Good for: real-time training visualization")
        print("   • View UI: tensorboard --logdir <log_dir>")
    else:
        print("⚠️  TensorBoard: Not installed")
        print("   • Install: pip install tensorboard")
    
    print()
    
    if CSV_LOGGER_AVAILABLE:
        print("✅ CSV Logger: Available (fallback)")
        print("   • Simple file-based logging")
    else:
        print("⚠️  CSV Logger: Not available")
    
    print("="*70 + "\n")


def print_mlflow_instructions() -> None:
    """Print detailed MLflow setup instructions."""
    print("\n" + "="*70)
    print("🚀 MLflow Setup Instructions")
    print("="*70)
    print("\n1. Install MLflow:")
    print("   pip install mlflow")
    print("\n2. Start MLflow tracking server (optional):")
    print("   mlflow server --host 0.0.0.0 --port 5000")
    print("\n3. Set tracking URI in your config:")
    print("   tracking:")
    print("     mlflow_tracking_uri: 'http://localhost:5000'")
    print("\n4. Or use file-based tracking:")
    print("   tracking:")
    print("     mlflow_tracking_uri: 'file:./mlruns'")
    print("\n5. View experiments:")
    print("   mlflow ui --backend-store-uri <tracking_uri>")
    print("\nBenefits:")
    print("  • Compare multiple experiments side-by-side")
    print("  • Track hyperparameters and metrics automatically")
    print("  • Model versioning and registry")
    print("  • Artifact storage (models, plots, data)")
    print("="*70 + "\n")


class SimpleMetricLogger:
    """
    Simple fallback logger when Lightning is not available.
    
    Logs metrics to a JSON file for basic tracking.
    """
    
    def __init__(self, save_dir: Union[str, Path], experiment_name: str):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.experiment_name = experiment_name
        self.metrics: Dict[str, list] = {}
        self.log_file = self.save_dir / f"{experiment_name}_metrics.json"
    
    def log_metric(self, name: str, value: float, step: Optional[int] = None) -> None:
        """Log a single metric value."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({
            'value': float(value),
            'step': step if step is not None else len(self.metrics[name])
        })
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """Log multiple metrics at once."""
        for name, value in metrics.items():
            self.log_metric(name, value, step)
    
    def save(self) -> None:
        """Save metrics to JSON file."""
        import json
        with open(self.log_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        print(f"Metrics saved to: {self.log_file}")


# Made with Bob