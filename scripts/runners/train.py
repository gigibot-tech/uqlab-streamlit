"""
Training Script - CLI interface for training uncertainty models.

Usage:
    python scripts/train.py --config configs/experiment.yaml
    python scripts/train.py --model dinov2_mlp --epochs 12 --lr 1e-3
"""

import argparse
import sys
from pathlib import Path

import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import sys
sys.path.insert(0, str(project_root / "1_data"))
sys.path.insert(0, str(project_root / "2_models"))
sys.path.insert(0, str(project_root / "3_training"))

from shared import (
    DataConfig,
    GlobalConfig,
    ModelArchitecture,
    NoiseType,
    get_logger,
    load_yaml,
    save_json,
    set_seed,
    setup_logging,
)

# Import from numbered directories
import importlib.util

# Load 1_data module
data_spec = importlib.util.spec_from_file_location("data_module", project_root / "1_data" / "__init__.py")
data_module = importlib.util.module_from_spec(data_spec)
data_spec.loader.exec_module(data_module)
get_cifar10n_loaders = data_module.get_cifar10n_loaders

# Load 2_models module
models_spec = importlib.util.spec_from_file_location("models_module", project_root / "2_models" / "__init__.py")
models_module = importlib.util.module_from_spec(models_spec)
models_spec.loader.exec_module(models_module)
create_model = models_module.create_model

# Load 3_training module
training_spec = importlib.util.spec_from_file_location("training_module", project_root / "3_training" / "__init__.py")
training_module = importlib.util.module_from_spec(training_spec)
training_spec.loader.exec_module(training_module)
CheckpointCallback = training_module.CheckpointCallback
EarlyStoppingCallback = training_module.EarlyStoppingCallback
LoggingCallback = training_module.LoggingCallback
ProgressCallback = training_module.ProgressCallback
TrainingConfig = training_module.TrainingConfig
UncertaintyTrainer = training_module.UncertaintyTrainer


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train uncertainty quantification model")
    
    # Config file
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration YAML file",
    )
    
    # Model arguments
    parser.add_argument(
        "--model",
        type=str,
        default="dinov2_mlp",
        choices=[arch.value for arch in ModelArchitecture],
        help="Model architecture",
    )
    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=256,
        help="Hidden dimension size",
    )
    parser.add_argument(
        "--dropout",
        type=float,
        default=0.2,
        help="Dropout rate",
    )
    
    # Data arguments
    parser.add_argument(
        "--noise-type",
        type=str,
        default="worst",
        choices=[nt.value for nt in NoiseType],
        help="CIFAR-10N noise type",
    )
    parser.add_argument(
        "--data-root",
        type=str,
        default="./data/cifar10n",
        help="Path to CIFAR-10N data",
    )
    
    # Training arguments
    parser.add_argument(
        "--epochs",
        type=int,
        default=12,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--lr",
        "--learning-rate",
        type=float,
        default=1e-3,
        dest="learning_rate",
        help="Learning rate",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=256,
        help="Training batch size",
    )
    parser.add_argument(
        "--weight-decay",
        type=float,
        default=1e-4,
        help="Weight decay",
    )
    parser.add_argument(
        "--optimizer",
        type=str,
        default="adamw",
        choices=["adam", "adamw", "sgd", "rmsprop"],
        help="Optimizer type",
    )
    parser.add_argument(
        "--scheduler",
        type=str,
        default="cosine",
        choices=["cosine", "step", "exponential", "plateau", "none"],
        help="Learning rate scheduler",
    )
    
    # System arguments
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to use for training",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=4,
        help="Number of data loading workers",
    )
    
    # Output arguments
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./results/experiments",
        help="Output directory for results",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        help="Experiment name (auto-generated if not provided)",
    )
    
    # Flags
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip validation during training",
    )
    parser.add_argument(
        "--early-stopping",
        action="store_true",
        help="Enable early stopping",
    )
    parser.add_argument(
        "--amp",
        action="store_true",
        help="Use automatic mixed precision",
    )
    
    return parser.parse_args()


def main():
    """Main training function."""
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(log_level="INFO", log_to_console=True)
    logger.info("Starting training script")
    
    # Set random seed
    set_seed(args.seed)
    logger.info(f"Set random seed to {args.seed}")
    
    # Load config from file if provided
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        config_dict = load_yaml(args.config)
        config = GlobalConfig.from_dict(config_dict)
    else:
        # Create config from arguments
        config = GlobalConfig()
        config.model.architecture = ModelArchitecture(args.model)
        config.model.hidden_dim = args.hidden_dim
        config.model.dropout = args.dropout
        config.data.noise_type = NoiseType(args.noise_type)
        config.training.epochs = args.epochs
        config.training.train_batch_size = args.batch_size
        config.training.optimizer.learning_rate = args.learning_rate
        config.training.optimizer.weight_decay = args.weight_decay
        config.training.optimizer.optimizer_type = args.optimizer
        config.training.scheduler.scheduler_type = args.scheduler
        config.training.use_amp = args.amp
        config.system.seed = args.seed
    
    # Create experiment directory
    if args.experiment_name:
        exp_name = args.experiment_name
    else:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_name = f"{args.model}_{timestamp}"
    
    output_dir = Path(args.output_dir) / exp_name
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Experiment directory: {output_dir}")
    
    # Save configuration
    config_path = output_dir / "config.json"
    save_json(config.to_dict(), config_path)
    logger.info(f"Saved configuration to {config_path}")
    
    # Create data loaders
    logger.info("Creating data loaders...")
    train_loader, val_loader, test_loader = get_cifar10n_loaders(
        root=Path(args.data_root),
        noise_type=config.data.noise_type,
        train_batch_size=config.training.train_batch_size,
        eval_batch_size=config.training.eval_batch_size,
        num_workers=args.num_workers,
    )
    logger.info(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    
    # Create model
    logger.info(f"Creating model: {config.model.architecture}")
    model = create_model(
        architecture=config.model.architecture,
        num_classes=config.data.num_classes,
        hidden_dim=config.model.hidden_dim,
        dropout=config.model.dropout,
    )
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    # Create callbacks
    callbacks = [
        LoggingCallback(
            log_dir=output_dir / "logs",
            log_every_n_steps=config.training.log_every_n_steps,
        ),
        CheckpointCallback(
            save_dir=output_dir / "checkpoints",
            save_every_n_epochs=config.training.checkpoint.save_every_n_epochs,
            save_best=config.training.checkpoint.save_best,
            monitor_metric=config.training.checkpoint.monitor_metric,
            monitor_mode=config.training.checkpoint.monitor_mode,
        ),
        ProgressCallback(show_batch_progress=True),
    ]
    
    if args.early_stopping or config.training.early_stopping.enabled:
        callbacks.append(
            EarlyStoppingCallback(
                monitor_metric=config.training.early_stopping.monitor_metric,
                monitor_mode=config.training.early_stopping.monitor_mode,
                patience=config.training.early_stopping.patience,
                min_delta=config.training.early_stopping.min_delta,
            )
        )
    
    # Create trainer
    logger.info("Creating trainer...")
    trainer = UncertaintyTrainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader if not args.no_validation else None,
        config=config.training,
        callbacks=callbacks,
        device=torch.device(args.device),
    )
    
    # Train
    logger.info("Starting training...")
    history = trainer.train()
    
    # Save training history
    history_path = output_dir / "training_history.json"
    save_json(history, history_path)
    logger.info(f"Saved training history to {history_path}")
    
    # Save final model
    final_model_path = output_dir / "final_model.pt"
    torch.save(model.state_dict(), final_model_path)
    logger.info(f"Saved final model to {final_model_path}")
    
    logger.info("Training completed successfully!")


if __name__ == "__main__":
    main()

# Made with Bob