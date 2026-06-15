#!/usr/bin/env python3
"""
Example: Batch Experiment with Parameter Sweep

This example demonstrates how to run a batch experiment
that sweeps over a parameter (e.g., noise rate).

Features:
- Automated parameter sweep
- Multiple runs with different configurations
- Aggregated results analysis
"""

import requests
import time
import sys
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
API_TOKEN = "your-jwt-token-here"  # Replace with actual token

def get_headers() -> Dict[str, str]:
    """Get API request headers."""
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

def create_batch_experiment() -> str:
    """Create a batch experiment with noise rate sweep."""
    
    print("="*60)
    print("Creating Batch Experiment: Noise Rate Sweep")
    print("="*60)
    print()
    
    # Batch experiment configuration
    batch_config = {
        "name": "DINOv2 Noise Rate Sweep",
        "description": "Sweep aleatoric noise from 0% to 50%",
        "method_type": "attribution",
        "base_config": {
            "architecture": "dinov2_mlp",
            "training_mode": "feature_space",
            "dinov2_model": "small",
            "hidden_dim": 256,
            "dropout": 0.2,
            "noise_type": "worse_label",
            "under_supported_classes": "3,5",
            "under_train_per_class": 50,
            "regular_train_per_class": 300,
            "eval_per_group": 600,
            "epochs": 12,
            "learning_rate": 0.001,
            "weight_decay": 0.0001,
            "train_batch_size": 256,
            "mc_passes": 20
        },
        "sweep_definitions": [
            {
                "parameter": "aleatoric_noise_percentage",
                "value_type": "float",
                "range": {
                    "start": 0.0,
                    "end": 0.5,
                    "step": 0.1
                }
            }
        ],
        "execution_mode": "sequential"
    }
    
    # Create batch experiment
    response = requests.post(
        f"{API_BASE_URL}/batch-experiments",
        json=batch_config,
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create batch experiment: {response.text}")
        sys.exit(1)
    
    batch_data = response.json()
    batch_id = batch_data["id"]
    
    print(f"✅ Batch experiment created!")
    print(f"   ID: {batch_id}")
    print(f"   Name: {batch_data['name']}")
    print(f"   Total runs: {batch_data['total_runs']}")
    print()
    
    return batch_id

def monitor_batch_progress(batch_id: str):
    """Monitor batch experiment progress."""
    
    print("="*60)
    print("Monitoring Batch Progress")
    print("="*60)
    print()
    
    while True:
        # Get batch status
        response = requests.get(
            f"{API_BASE_URL}/batch-experiments/{batch_id}",
            headers=get_headers()
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get batch status: {response.text}")
            break
        
        batch_data = response.json()
        status = batch_data["status"]
        progress = batch_data["progress"]
        completed = batch_data["completed_runs"]
        total = batch_data["total_runs"]
        
        print(f"\rStatus: {status} | Progress: {progress:.1f}% | Runs: {completed}/{total}", end="")
        
        if status in ["completed", "failed", "completed_with_errors"]:
            print()
            print()
            break
        
        time.sleep(5)
    
    return batch_data

def display_results(batch_id: str):
    """Display batch experiment results."""
    
    print("="*60)
    print("Batch Experiment Results")
    print("="*60)
    print()
    
    # Get all runs
    response = requests.get(
        f"{API_BASE_URL}/batch-experiments/{batch_id}/runs",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get runs: {response.text}")
        return
    
    runs_data = response.json()
    runs = runs_data["runs"]
    
    # Display results table
    print(f"{'Noise Rate':<12} {'Aleatoric AUROC':<18} {'Epistemic AUROC':<18} {'Status':<12}")
    print("-"*60)
    
    for run in runs:
        noise_rate = run["swept_value_numeric"]
        aleatoric = run.get("aleatoric_auroc", "N/A")
        epistemic = run.get("epistemic_auroc", "N/A")
        status = run["status"]
        
        if isinstance(aleatoric, float):
            aleatoric = f"{aleatoric:.4f}"
        if isinstance(epistemic, float):
            epistemic = f"{epistemic:.4f}"
        
        print(f"{noise_rate:<12.1f} {aleatoric:<18} {epistemic:<18} {status:<12}")
    
    print()
    
    # Get summary statistics
    response = requests.get(
        f"{API_BASE_URL}/batch-experiments/{batch_id}/results/summary",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        summary = response.json()
        stats = summary.get("statistics", {})
        
        print("Summary Statistics:")
        print(f"  Mean Aleatoric AUROC: {stats.get('mean_aleatoric_auroc', 'N/A'):.4f}")
        print(f"  Std Aleatoric AUROC:  {stats.get('std_aleatoric_auroc', 'N/A'):.4f}")
        print(f"  Mean Epistemic AUROC: {stats.get('mean_epistemic_auroc', 'N/A'):.4f}")
        print(f"  Std Epistemic AUROC:  {stats.get('std_epistemic_auroc', 'N/A'):.4f}")
        print()

def main():
    """Run batch experiment example."""
    
    print()
    print("🚀 Batch Experiment Example")
    print()
    
    # Check API token
    if API_TOKEN == "your-jwt-token-here":
        print("⚠️  Please set your API token in the script!")
        print("   Get token by logging in: POST /api/v1/auth/login")
        print()
        return 1
    
    try:
        # Create batch experiment
        batch_id = create_batch_experiment()
        
        # Monitor progress
        batch_data = monitor_batch_progress(batch_id)
        
        # Display results
        if batch_data["status"] == "completed":
            display_results(batch_id)
            print("✅ Batch experiment completed successfully!")
        else:
            print(f"⚠️  Batch experiment finished with status: {batch_data['status']}")
        
        print()
        return 0
        
    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
