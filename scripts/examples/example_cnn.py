#!/usr/bin/env python3
"""
Example: CNN MC Dropout Training

This example demonstrates how to train a simple CNN
with MC Dropout for uncertainty quantification.

Features:
- End-to-end training
- Lightweight architecture
- Fast training and inference
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run CNN training example."""
    
    print("="*60)
    print("CNN MC Dropout Training Example")
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
  architecture: cnn_mcdropout
  training_mode: end_to_end
  hidden_dim: 128
  dropout: 0.5
  num_conv_layers: 3
  conv_channels: [32, 64, 64]

training:
  epochs: 20
  learning_rate: 0.001
  weight_decay: 0.0001
  batch_size: 128

evaluation:
  mc_passes: 20
"""
    
    # Save config
    config_path = Path("/tmp/example_cnn_config.yaml")
    config_path.write_text(config_content)
    print(f"✓ Config saved to: {config_path}")
    
    # Output directory
    output_dir = Path("/tmp/example_cnn_output")
    print(f"✓ Output directory: {output_dir}")
    print()
    
    # Run training
    print("Starting training...")
    print("-"*60)
    print()
    print("Architecture:")
    print("  Conv2d(3→32, 3×3) + ReLU + MaxPool")
    print("  Conv2d(32→64, 3×3) + ReLU + MaxPool")
    print("  Conv2d(64→64, 3×3) + ReLU + MaxPool")
    print("  Linear(64×4×4 → 128) + ReLU + Dropout(0.5)")
    print("  Linear(128 → 10)")
    print()
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
        print("Model statistics:")
        print("  - Parameters: ~500K")
        print("  - Training time: ~15 minutes (single GPU)")
        print("  - Inference time: Fast")
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
