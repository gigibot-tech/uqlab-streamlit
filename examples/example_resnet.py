#!/usr/bin/env python3
"""
Example: ResNet18 MC Dropout Training

This example demonstrates how to train a ResNet18-based classifier
with MC Dropout for uncertainty quantification.

Features:
- End-to-end training
- High-capacity architecture
- Optional pretrained weights
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run ResNet18 training example."""
    
    print("="*60)
    print("ResNet18 MC Dropout Training Example")
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
  architecture: resnet18_mcdropout
  training_mode: end_to_end
  hidden_dim: 512
  dropout: 0.3
  use_untrained_resnet: false  # Use pretrained ImageNet weights

training:
  epochs: 15
  learning_rate: 0.0001  # Lower LR for fine-tuning
  weight_decay: 0.0001
  batch_size: 128

evaluation:
  mc_passes: 20
"""
    
    # Save config
    config_path = Path("/tmp/example_resnet_config.yaml")
    config_path.write_text(config_content)
    print(f"✓ Config saved to: {config_path}")
    
    # Output directory
    output_dir = Path("/tmp/example_resnet_output")
    print(f"✓ Output directory: {output_dir}")
    print()
    
    # Run training
    print("Starting training...")
    print("-"*60)
    print()
    print("Architecture:")
    print("  ResNet18 Backbone (pretrained on ImageNet)")
    print("    - Conv1 (7×7)")
    print("    - Layer1 (2 residual blocks)")
    print("    - Layer2 (2 residual blocks)")
    print("    - Layer3 (2 residual blocks)")
    print("    - Layer4 (2 residual blocks)")
    print("    - AvgPool")
    print("  Dropout(0.3)")
    print("  Linear(512 → 10)")
    print()
    print("Training mode: Fine-tuning with pretrained weights")
    print("Learning rate: 0.0001 (lower for fine-tuning)")
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
        print("  - Parameters: ~11M")
        print("  - Training time: ~30 minutes (single GPU)")
        print("  - Inference time: Medium")
        print("  - Expected accuracy: 90-95%")
        print()
        print("Tips:")
        print("  - Set use_untrained_resnet: true to train from scratch")
        print("  - Increase learning_rate to 0.001 for random init")
        print("  - Adjust dropout (0.2-0.5) based on dataset size")
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
