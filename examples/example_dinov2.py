#!/usr/bin/env python3
"""
Example: DINOv2 + MLP Training

This example demonstrates how to train a DINOv2-based classifier
with MC Dropout for uncertainty quantification.

Features:
- Feature space training (fast)
- Pre-extracted DINOv2 embeddings
- Attribution-based uncertainty signals
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run DINOv2 training example."""
    
    print("="*60)
    print("DINOv2 + MLP Training Example")
    print("="*60)
    print()
    
    # Configuration
    config_content = """
dataset:
  name: cifar10n
  noise_type: worse_label
  under_supported: "3,5"
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 600

model:
  architecture: dinov2_mlp
  training_mode: feature_space
  dinov2_model: small  # Options: small, base, large, giant
  hidden_dim: 256
  dropout: 0.2

training:
  epochs: 12
  learning_rate: 0.001
  weight_decay: 0.0001
  batch_size: 256

evaluation:
  mc_passes: 20
"""
    
    # Save config
    config_path = Path("/tmp/example_dinov2_config.yaml")
    config_path.write_text(config_content)
    print(f"✓ Config saved to: {config_path}")
    
    # Output directory
    output_dir = Path("/tmp/example_dinov2_output")
    print(f"✓ Output directory: {output_dir}")
    print()
    
    # Run training
    print("Starting training...")
    print("-"*60)
    
    cmd = [
        "python",
        "scripts/run_fast_uncertainty_classification.py",
        str(config_path),
        str(output_dir)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        
        print()
        print("="*60)
        print("✅ Training completed successfully!")
        print("="*60)
        print()
        print(f"Results saved to: {output_dir}")
        print()
        print("Key files:")
        print(f"  - {output_dir}/results.json")
        print(f"  - {output_dir}/model.pt")
        print(f"  - {output_dir}/attribution_signals.npz")
        print()
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print()
        print("="*60)
        print("❌ Training failed!")
        print("="*60)
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
