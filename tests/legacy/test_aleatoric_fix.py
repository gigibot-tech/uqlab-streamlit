#!/usr/bin/env python3
"""
Quick test script to verify aleatoric_noise_percentage is properly saved.
Run this after creating a test experiment with 20% custom noise.
"""

import requests
import json
import yaml
from pathlib import Path

API_URL = "http://localhost:8000"

def test_api_config_structure():
    """Test that API accepts aleatoric_noise_percentage"""
    print("=" * 80)
    print("TEST 1: API Config Structure")
    print("=" * 80)
    
    test_config = {
        "name": "test_aleatoric_20pct",
        "config": {
            "noise_type": "worse_label",
            "aleatoric_noise_percentage": 20.0,  # ← KEY FIELD
            "under_supported_classes": "3,5",
            "under_train_per_class": 50,
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
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/experiments/no-auth",
            json=test_config,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Experiment created: {result['id']}")
        print(f"   Name: {result['name']}")
        
        # Check the saved config file
        exp_dir = Path(f"/tmp/uqlab_experiments/{result['id']}")
        config_file = exp_dir / "config.yaml"
        
        if config_file.exists():
            with open(config_file) as f:
                saved_config = yaml.safe_load(f)
            
            aleatoric_value = saved_config.get('data', {}).get('aleatoric_noise_percentage')
            print(f"\n📄 Config file: {config_file}")
            print(f"   aleatoric_noise_percentage: {aleatoric_value}")
            
            if aleatoric_value == 20.0:
                print("   ✅ CORRECT! Value saved properly")
                return True
            else:
                print(f"   ❌ WRONG! Expected 20.0, got {aleatoric_value}")
                return False
        else:
            print(f"   ❌ Config file not found: {config_file}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_recent_experiments():
    """Check recent experiments for aleatoric_noise_percentage"""
    print("\n" + "=" * 80)
    print("TEST 2: Recent Experiments")
    print("=" * 80)
    
    try:
        response = requests.get(f"{API_URL}/api/v1/experiments/no-auth?limit=5")
        response.raise_for_status()
        experiments = response.json()
        
        print(f"Found {len(experiments)} recent experiments:\n")
        
        for exp in experiments[:5]:
            exp_dir = Path(f"/tmp/uqlab_experiments/{exp['id']}")
            config_file = exp_dir / "config.yaml"
            
            if config_file.exists():
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                
                aleatoric = config.get('data', {}).get('aleatoric_noise_percentage', 'NOT FOUND')
                print(f"  {exp['name'][:40]:40} | aleatoric: {aleatoric}")
            else:
                print(f"  {exp['name'][:40]:40} | config file missing")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    print("\n🔬 Testing Aleatoric Noise Percentage Fix\n")
    
    # Test 1: Create experiment via API
    success = test_api_config_structure()
    
    # Test 2: Check recent experiments
    test_recent_experiments()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL TESTS PASSED - Fix is working!")
    else:
        print("❌ TESTS FAILED - Check the output above")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

# Made with Bob
