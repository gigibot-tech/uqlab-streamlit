#!/usr/bin/env python3
"""Test script to verify batch experiment API accepts None for swept parameters."""

import json
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Test payload that mimics what the frontend sends
# When under_train_per_class is swept, it should be None in base_config
test_payload = {
    "name": "Test Epistemic Sweep",
    "description": "Testing validation fix",
    "base_config": {
        "noise_type": "worse_label",
        "under_supported_classes": "3,5",
        "under_train_per_class": None,  # This is being swept, so it's None
        "regular_train_per_class": 300,
        "eval_per_group": 600,
        "dinov2_model": "small",
        "hidden_dim": 256,
        "dropout": 0.2,
        "epochs": 12,
        "learning_rate": 0.001,
        "weight_decay": 0.0001,
        "train_batch_size": 256,
        "mc_passes": 20,
        "attribution_method": "dualxda"
    },
    "sweep_definitions": [
        {
            "parameter": "under_train_per_class",
            "value_type": "int",
            "range": {
                "start": 10,
                "end": 100,
                "step": 10
            }
        }
    ],
    "auto_start": False
}

# Test with Pydantic validation
try:
    from app.domain.models import TrainingConfig
    
    print("Testing TrainingConfig validation with None values...")
    config = TrainingConfig(**test_payload["base_config"])
    print("✓ TrainingConfig accepts None for swept parameters")
    print(f"  under_train_per_class: {config.under_train_per_class}")
    print(f"  regular_train_per_class: {config.regular_train_per_class}")
    
    # Test model_dump
    dumped = config.model_dump()
    print("\n✓ model_dump() works correctly")
    print(f"  Dumped config keys: {list(dumped.keys())[:5]}...")
    
    # Test to_yaml_dict
    yaml_dict = config.to_yaml_dict()
    print("\n✓ to_yaml_dict() works correctly")
    print(f"  data.under_train_per_class: {yaml_dict['data']['under_train_per_class']}")
    
    print("\n✅ All validation tests passed!")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Made with Bob
