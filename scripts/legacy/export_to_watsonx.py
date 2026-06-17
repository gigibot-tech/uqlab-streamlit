#!/usr/bin/env python3
"""
Export trained model to watsonx.ai deployment package.

This script should be run AFTER training completes. It will:
1. Load the trained model checkpoint
2. Load training and evaluation data
3. Export everything needed for watsonx.ai deployment

Usage:
    python export_to_watsonx.py --checkpoint path/to/checkpoint.pt
    
Or run after training in your training script:
    from uqlab.evaluation.classification.watsonx_export import export_all_for_watsonx
    export_all_for_watsonx(...)
"""

import argparse
import logging
import torch
from pathlib import Path
from uqlab.evaluation.classification.watsonx_export import export_all_for_watsonx

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Export model to watsonx.ai')
    parser.add_argument(
        '--checkpoint',
        type=str,
        required=True,
        help='Path to model checkpoint (.pt file)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./watsonx_deployment',
        help='Output directory for deployment package'
    )
    parser.add_argument(
        '--experiment-dir',
        type=str,
        help='Experiment directory containing results (optional, will try to infer from checkpoint)'
    )
    
    args = parser.parse_args()
    
    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    logger.info(f"Loading checkpoint from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    
    # Try to infer experiment directory
    if args.experiment_dir:
        exp_dir = Path(args.experiment_dir)
    else:
        # Assume checkpoint is in results/experiment_name/checkpoints/
        exp_dir = checkpoint_path.parent.parent
    
    logger.info(f"Experiment directory: {exp_dir}")
    
    # Check for required files
    required_files = [
        'train_embeddings.pt',
        'eval_embeddings.pt',
        'signal_table.csv',
        'predictions.pt',
        'confidences.pt',
        'auroc_results.csv'
    ]
    
    missing_files = []
    for file in required_files:
        if not (exp_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.warning("Some files are missing:")
        for file in missing_files:
            logger.warning(f"  - {file}")
        logger.warning("The export will continue but may be incomplete.")
        logger.warning("These files are typically generated during training.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            logger.info("Export cancelled.")
            return
    
    # Load data
    logger.info("Loading training data...")
    train_data = torch.load(exp_dir / 'train_embeddings.pt', weights_only=False)
    
    logger.info("Loading evaluation data...")
    eval_data = torch.load(exp_dir / 'eval_embeddings.pt', weights_only=False)
    
    logger.info("Loading results...")
    import pandas as pd
    signal_table = pd.read_csv(exp_dir / 'signal_table.csv')
    predictions = torch.load(exp_dir / 'predictions.pt', weights_only=False)
    confidences = torch.load(exp_dir / 'confidences.pt', weights_only=False)
    auroc_df = pd.read_csv(exp_dir / 'auroc_results.csv')
    
    # Extract from checkpoint
    model = checkpoint['model']
    optimizer_state = checkpoint.get('optimizer', None)
    epoch = checkpoint.get('epoch', 0)
    loss = checkpoint.get('loss', 0.0)
    config = checkpoint.get('config', {})
    
    logger.info(f"Model trained for {epoch} epochs with final loss: {loss:.4f}")
    
    # Call export function
    logger.info(f"Exporting to: {args.output_dir}")
    export_all_for_watsonx(
        model=model,
        optimizer=optimizer_state,
        epoch=epoch,
        loss=loss,
        train_embeddings=train_data['embeddings'],
        train_labels=train_data['labels'],
        train_noisy_labels=train_data.get('noisy_labels', train_data['labels']),
        train_is_noisy=train_data.get('is_noisy', torch.zeros_like(train_data['labels'], dtype=torch.bool)),
        train_indices=train_data.get('indices', torch.arange(len(train_data['labels']))),
        eval_embeddings=eval_data['embeddings'],
        eval_clean_labels=eval_data['clean_labels'],
        eval_noisy_labels=eval_data.get('noisy_labels', eval_data['clean_labels']),
        eval_is_noisy=eval_data.get('is_noisy', torch.zeros_like(eval_data['clean_labels'], dtype=torch.bool)),
        eval_group_labels=eval_data.get('group_labels', torch.zeros_like(eval_data['clean_labels'])),
        eval_indices=eval_data.get('indices', torch.arange(len(eval_data['clean_labels']))),
        signal_table=signal_table,
        predictions=predictions,
        confidences=confidences,
        auroc_rows=auroc_df.to_dict('records'),
        config=config,
        output_base_dir=args.output_dir
    )
    
    logger.info("✅ Export complete!")
    logger.info(f"Deployment package created in: {args.output_dir}")
    logger.info("Next steps:")
    logger.info("1. Review the exported files")
    logger.info("2. Upload to watsonx.ai")
    logger.info("3. Create deployment")
    logger.info("4. Get credentials and use in Streamlit cloud mode")
    logger.info("See WATSONX_DEPLOYMENT_GUIDE.md for detailed instructions.")


if __name__ == '__main__':
    main()

# Made with Bob
