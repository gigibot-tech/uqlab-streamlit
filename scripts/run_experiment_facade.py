#!/usr/bin/env python3
"""
Facade-based experiment runner - Clean replacement for monolithic script.

This script uses the ExperimentFacade pattern to orchestrate uncertainty
quantification experiments with a clean, maintainable architecture.

Usage:
    python scripts/run_experiment_facade.py --epochs 10 --mc-passes 20
    
For full options:
    python scripts/run_experiment_facade.py --help
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
for path in [PROJECT_ROOT, SRC_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Import facade
from uqlab.facade import ExperimentFacade


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run uncertainty quantification experiment using facade pattern",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Dataset configuration
    dataset_group = parser.add_argument_group("Dataset Configuration")
    dataset_group.add_argument(
        "--dataset", 
        default="cifar10n",
        help="Dataset name"
    )
    dataset_group.add_argument(
        "--noise-type", 
        default="worse_label",
        choices=["worse_label", "aggre_label", "random_label1", "random_label2", "random_label3"],
        help="Type of label noise in CIFAR-10N"
    )
    dataset_group.add_argument(
        "--under-supported", 
        default="random:2",
        help="Under-supported classes (e.g., 'random:2' or '0,1,2')"
    )
    dataset_group.add_argument(
        "--under-train-per-class", 
        type=int, 
        default=50,
        help="Training samples per under-supported class"
    )
    dataset_group.add_argument(
        "--regular-train-per-class", 
        type=int, 
        default=300,
        help="Training samples per regular class"
    )
    
    # Model configuration
    model_group = parser.add_argument_group("Model Configuration")
    model_group.add_argument(
        "--model-type", 
        default="dinov2",
        choices=["dinov2", "resnet"],
        help="Model architecture type"
    )
    model_group.add_argument(
        "--dinov2-model", 
        default="small",
        choices=["small", "base", "large", "giant"],
        help="DINOv2 model size"
    )
    model_group.add_argument(
        "--hidden-dim", 
        type=int, 
        default=256,
        help="Hidden dimension size for MLP"
    )
    model_group.add_argument(
        "--dropout", 
        type=float, 
        default=0.2,
        help="Dropout rate for MC Dropout"
    )
    model_group.add_argument(
        "--use-untrained-resnet",
        action="store_true",
        help="Use untrained ResNet (for baseline comparison)"
    )
    
    # Training configuration
    training_group = parser.add_argument_group("Training Configuration")
    training_group.add_argument(
        "--epochs", 
        type=int, 
        default=12,
        help="Number of training epochs"
    )
    training_group.add_argument(
        "--learning-rate", 
        type=float, 
        default=0.001,
        help="Learning rate"
    )
    training_group.add_argument(
        "--weight-decay", 
        type=float, 
        default=0.0001,
        help="Weight decay for optimizer"
    )
    training_group.add_argument(
        "--batch-size", 
        type=int, 
        default=256,
        help="Training batch size"
    )
    training_group.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    # Evaluation configuration
    eval_group = parser.add_argument_group("Evaluation Configuration")
    eval_group.add_argument(
        "--mc-passes", 
        type=int, 
        default=20,
        help="Number of MC Dropout forward passes"
    )
    eval_group.add_argument(
        "--eval-per-group", 
        type=int, 
        default=100,
        help="Evaluation samples per group"
    )
    eval_group.add_argument(
        "--signals",
        nargs="+",
        default=None,
        help="Specific signals to compute (default: all)"
    )
    
    # Output configuration
    output_group = parser.add_argument_group("Output Configuration")
    output_group.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("results"),
        help="Output directory for results"
    )
    output_group.add_argument(
        "--experiment-name", 
        default=None,
        help="Experiment name (default: auto-generated)"
    )
    output_group.add_argument(
        "--save-checkpoints",
        action="store_true",
        help="Save model checkpoints during training"
    )
    
    # Logging configuration
    log_group = parser.add_argument_group("Logging Configuration")
    log_group.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    log_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )
    
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> dict:
    """
    Build experiment configuration from command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Configuration dictionary for ExperimentFacade
    """
    # Generate experiment name if not provided
    experiment_name = args.experiment_name
    if experiment_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"exp_{timestamp}"
    
    config = {
        # Experiment metadata
        "experiment_name": experiment_name,
        "seed": args.seed,
        
        # Dataset configuration
        "dataset_name": args.dataset,
        "noise_type": args.noise_type,
        "under_supported": args.under_supported,
        "under_train_per_class": args.under_train_per_class,
        "regular_train_per_class": args.regular_train_per_class,
        
        # Model configuration
        "model_type": args.model_type,
        "dinov2_model": args.dinov2_model,
        "hidden_dim": args.hidden_dim,
        "dropout": args.dropout,
        "use_untrained_resnet": args.use_untrained_resnet,
        "num_classes": 10,  # CIFAR-10
        
        # Training configuration
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "train_batch_size": args.batch_size,
        "save_checkpoints": args.save_checkpoints,
        
        # Evaluation configuration
        "mc_passes": args.mc_passes,
        "eval_per_group": args.eval_per_group,
        "signals": args.signals,  # None means all signals
        
        # Output configuration
        "output_dir": str(args.output_dir),
    }
    
    return config


def setup_logging(log_level: str, quiet: bool) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        quiet: If True, suppress progress output
        
    Returns:
        Configured logger instance
    """
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    
    if quiet:
        logger.setLevel(logging.WARNING)
    
    return logger


def main() -> int:
    """
    Main entry point for facade-based experiment runner.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level, args.quiet)
    
    # Build configuration
    config = build_config(args)
    
    # Log experiment start
    logger.info("=" * 80)
    logger.info(f"Starting Experiment: {config['experiment_name']}")
    logger.info("=" * 80)
    logger.info(f"Configuration:\n{json.dumps(config, indent=2)}")
    logger.info("=" * 80)
    
    try:
        # Create facade
        facade = ExperimentFacade(config, logger=logger)
        
        # Run experiment
        logger.info("Initializing experiment...")
        results = facade.run_experiment()
        
        # Log completion
        logger.info("=" * 80)
        logger.info("✅ Experiment Complete!")
        logger.info("=" * 80)
        logger.info(f"Results saved to: {results.get('output_dir', config['output_dir'])}")
        
        # Display key metrics if available
        if "final_metrics" in results:
            logger.info("\n📊 Final Metrics:")
            for key, value in results["final_metrics"].items():
                logger.info(f"  {key}: {value}")
        
        logger.info("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Experiment interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ Experiment Failed!")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob