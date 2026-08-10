#!/usr/bin/env python3
"""
Script to generate the logical consistency validation notebook.
This approach is more manageable than creating a large JSON file directly.
"""

import json
from pathlib import Path

# Define the notebook structure
notebook = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.9.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Helper function to add cells
def add_markdown(text):
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": text.split("\n")
    })

def add_code(code):
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": code.split("\n")
    })

# Title and introduction
add_markdown("""# Logical Consistency Validation: Comprehensive Cross-Experiment Analysis

This notebook performs comprehensive logical consistency checks across all three architectures and both sweep types (dataset size and label noise). It validates fundamental uncertainty quantification principles and ensures the model-agnostic system behaves correctly.

## Validation Checks

1. **Uncertainty Decomposition**: Total ≈ Epistemic + Aleatoric
2. **Non-Negativity**: All uncertainties and accuracy in valid ranges
3. **Monotonicity**: Expected trends with dataset size and label noise
4. **Cross-Architecture Consistency**: Similar behavioral patterns
5. **Uncertainty Bounds**: Values within theoretical limits
6. **Trade-off Analysis**: Accuracy-uncertainty relationships
7. **Statistical Significance**: All relationships are statistically valid

## Data Sources
- Dataset size sweep: `results/validation/dataset_size_sweep/`
- Label noise sweep: `results/validation/label_noise_sweep/`""")

# Section 1: Setup
add_markdown("## 1. Setup and Imports")

add_code("""import sys
import os
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import spearmanr, pearsonr
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Add project root to path
project_root = Path.cwd().parent.parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Python version: {sys.version}")""")

# Section 2: Configuration
add_markdown("## 2. Configuration and Constants")

add_code("""# Results directories
DATASET_SIZE_DIR = project_root / 'results' / 'validation' / 'dataset_size_sweep'
LABEL_NOISE_DIR = project_root / 'results' / 'validation' / 'label_noise_sweep'
OUTPUT_DIR = project_root / 'results' / 'validation' / 'consistency_checks'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Validation thresholds
DECOMPOSITION_TOLERANCE = 0.05  # ±5% for uncertainty decomposition
SIGNIFICANCE_LEVEL = 0.05  # p < 0.05 for statistical tests
CORRELATION_THRESHOLD = 0.7  # Strong correlation threshold

# Architecture names
ARCHITECTURES = ['DINOv2 + MLP', 'CNN MC Dropout', 'ResNet18 MC Dropout']

print(f"Output directory: {OUTPUT_DIR}")
print(f"Decomposition tolerance: ±{DECOMPOSITION_TOLERANCE*100}%")
print(f"Significance level: {SIGNIFICANCE_LEVEL}")""")

# Section 3: Data Loading
add_markdown("""## 3. Data Loading and Preprocessing

Load results from both validation notebooks and combine into unified DataFrames.""")

add_code("""def load_sweep_results(results_dir, sweep_type):
    \"\"\"Load results from a sweep directory.
    
    Args:
        results_dir: Path to results directory
        sweep_type: 'dataset_size' or 'label_noise'
    
    Returns:
        DataFrame with all results
    \"\"\"
    metrics_file = results_dir / 'metrics.csv'
    
    if not metrics_file.exists():
        print(f"Warning: {metrics_file} not found")
        return pd.DataFrame()
    
    df = pd.read_csv(metrics_file)
    df['sweep_type'] = sweep_type
    
    return df


# Load both sweeps
df_dataset_size = load_sweep_results(DATASET_SIZE_DIR, 'dataset_size')
df_label_noise = load_sweep_results(LABEL_NOISE_DIR, 'label_noise')

print(f"Dataset size sweep: {len(df_dataset_size)} experiments")
print(f"Label noise sweep: {len(df_label_noise)} experiments")

# Combine for unified analysis
df_all = pd.concat([df_dataset_size, df_label_noise], ignore_index=True)
print(f"\\nTotal experiments: {len(df_all)}")

# Display sample
print("\\nDataset Size Sweep Sample:")
display(df_dataset_size.head())

print("\\nLabel Noise Sweep Sample:")
display(df_label_noise.head())""")

# Save the notebook
output_path = Path(__file__).parent / "logical_consistency_validation.ipynb"
with open(output_path, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"Notebook generated: {output_path}")
print(f"Total cells: {len(notebook['cells'])}")

# Made with Bob
