#!/usr/bin/env python3
"""
Test script to verify per-signal AUROC data loading from batch experiments.
This simulates what the UI component does.
"""

import json
import yaml
from pathlib import Path

def test_signal_loading(batch_id):
    """Test loading signal data from a batch experiment."""
    
    batch_dir = Path(f"/tmp/uqlab_experiments/batch_{batch_id}")
    
    print(f"Testing batch: {batch_id}")
    print(f"Batch directory: {batch_dir}")
    print(f"Directory exists: {batch_dir.exists()}\n")
    
    if not batch_dir.exists():
        print("❌ Batch directory not found!")
        return
    
    experiments_dir = batch_dir / "experiments"
    print(f"Experiments directory: {experiments_dir}")
    print(f"Experiments dir exists: {experiments_dir.exists()}\n")
    
    if not experiments_dir.exists():
        print("❌ Experiments directory not found!")
        return
    
    exp_dirs = sorted([d for d in experiments_dir.glob("exp_*") if d.is_dir()])
    print(f"Found {len(exp_dirs)} experiment directories:")
    for exp_dir in exp_dirs[:3]:
        print(f"  - {exp_dir.name}")
    if len(exp_dirs) > 3:
        print(f"  ... and {len(exp_dirs) - 3} more\n")
    else:
        print()
    
    if not exp_dirs:
        print("❌ No experiment directories found!")
        return
    
    # Test loading from first experiment
    exp_dir = exp_dirs[0]
    print(f"Testing first experiment: {exp_dir.name}")
    
    summary_file = exp_dir / "summary.json"
    config_file = exp_dir / "config.yaml"
    
    print(f"  summary.json exists: {summary_file.exists()}")
    print(f"  config.yaml exists: {config_file.exists()}\n")
    
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        one_vs_rest = summary.get("one_vs_rest_auroc", [])
        print(f"  Found {len(one_vs_rest)} signals in one_vs_rest_auroc:")
        for signal in one_vs_rest:
            print(f"    - {signal['signal']}: "
                  f"alea={signal['aleatoric_like_auroc']:.3f}, "
                  f"epis={signal['epistemic_like_auroc']:.3f}")
        print()
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        print("  Config structure:")
        print(f"    Top-level keys: {list(config.keys())}")
        
        data_config = config.get("data", {})
        print(f"    data keys: {list(data_config.keys())}")
        
        # Try to extract parameter value
        x_val = None
        for key in ["under_train_per_class", "regular_train_per_class", "eval_per_group"]:
            if key in data_config and data_config[key] is not None:
                x_val = data_config[key]
                print(f"    Found swept parameter: {key} = {x_val}")
                break
        
        if x_val is None:
            print("    ⚠️ Could not find swept parameter!")
        print()
    
    # Now test loading all experiments
    print("="*70)
    print("Loading all experiments...")
    print("="*70)
    
    signal_data = {}
    x_values = []
    
    for exp_dir in exp_dirs:
        summary_file = exp_dir / "summary.json"
        config_file = exp_dir / "config.yaml"
        
        if not summary_file.exists() or not config_file.exists():
            print(f"⚠️ Skipping {exp_dir.name}: missing files")
            continue
        
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Extract parameter value
            data_config = config.get("data", {})
            x_val = None
            for key in ["under_train_per_class", "regular_train_per_class", "eval_per_group"]:
                if key in data_config and data_config[key] is not None:
                    x_val = data_config[key]
                    break
            
            if x_val is None:
                print(f"⚠️ Skipping {exp_dir.name}: no parameter value")
                continue
            
            x_values.append(x_val)
            
            # Extract signals
            one_vs_rest = summary.get("one_vs_rest_auroc", [])
            for signal_item in one_vs_rest:
                signal_name = signal_item.get("signal", "unknown")
                alea_auroc = signal_item.get("aleatoric_like_auroc", 0)
                epis_auroc = signal_item.get("epistemic_like_auroc", 0)
                
                if signal_name not in signal_data:
                    signal_data[signal_name] = {"aleatoric": [], "epistemic": []}
                
                signal_data[signal_name]["aleatoric"].append((x_val, alea_auroc))
                signal_data[signal_name]["epistemic"].append((x_val, epis_auroc))
            
            print(f"✅ Loaded {exp_dir.name}: x={x_val}, {len(one_vs_rest)} signals")
        
        except Exception as e:
            print(f"❌ Error loading {exp_dir.name}: {e}")
    
    print()
    print("="*70)
    print("RESULTS:")
    print("="*70)
    print(f"✅ Successfully loaded {len(signal_data)} signals from {len(exp_dirs)} experiments")
    print(f"   X-axis values: {sorted(set(x_values))}")
    print(f"   Signals found: {list(signal_data.keys())}")
    print()
    
    for signal_name, data in sorted(signal_data.items()):
        alea_points = len(data["aleatoric"])
        epis_points = len(data["epistemic"])
        print(f"   {signal_name}: {alea_points} aleatoric points, {epis_points} epistemic points")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        batch_id = sys.argv[1]
    else:
        # Use the most recent batch
        import os
        batches = sorted([d for d in Path("/tmp/uqlab_experiments").glob("batch_*") if d.is_dir()])
        if batches:
            batch_id = batches[-1].name.replace("batch_", "")
            print(f"Using most recent batch: {batch_id}\n")
        else:
            print("No batch experiments found!")
            sys.exit(1)
    
    test_signal_loading(batch_id)

# Made with Bob
