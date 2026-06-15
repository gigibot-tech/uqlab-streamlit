# Logical Consistency Validation

## Overview

This directory contains the comprehensive logical consistency validation notebook that validates the model-agnostic uncertainty quantification system across all three architectures and both experimental sweeps (dataset size and label noise).

## Purpose

The logical consistency validation ensures that:
1. The uncertainty quantification system behaves correctly
2. All three architectures show consistent patterns
3. Fundamental UQ principles are satisfied
4. Results are statistically significant and reproducible

## Validation Checks

### 1. Uncertainty Decomposition Validation
**Principle**: Total uncertainty should equal the sum of epistemic and aleatoric uncertainty.

**Check**: `total_uncertainty ≈ epistemic_uncertainty + aleatoric_uncertainty`

**Tolerance**: ±5% relative error

**Why it matters**: This validates that our uncertainty decomposition is mathematically correct and that we're properly separating model uncertainty from data uncertainty.

### 2. Non-Negativity and Bounds Validation
**Principles**:
- All uncertainty values must be ≥ 0
- Accuracy must be in [0, 1]
- No NaN or infinite values

**Why it matters**: Ensures all metrics are within valid ranges and there are no numerical instabilities.

### 3. Monotonicity Validation
**Expected Trends**:
- **Dataset size sweep**: 
  - Accuracy should increase (more data → better performance)
  - Epistemic uncertainty should decrease (more data → less model uncertainty)
- **Label noise sweep**:
  - Accuracy should decrease (more noise → worse performance)
  - Aleatoric uncertainty should increase (more noise → more data uncertainty)

**Method**: Spearman correlation (tests monotonic relationships)

**Significance**: p < 0.05

**Why it matters**: Validates that the system responds correctly to changes in data quantity and quality.

### 4. Cross-Architecture Consistency
**Principle**: All three architectures should show similar behavioral patterns.

**Method**: 
- Normalize metrics to [0, 1] for each architecture
- Calculate pairwise Pearson correlations
- Check if correlations > 0.7 (strong correlation threshold)

**Why it matters**: Ensures the model-agnostic approach works consistently across different architectures.

### 5. Uncertainty Bounds Validation
**Principles**:
- Epistemic uncertainty ≤ log(num_classes) ≈ 2.303 for CIFAR-10
- Aleatoric uncertainty ≤ log(num_classes)
- Total uncertainty ≤ 1.5 × log(num_classes) (with margin)

**Why it matters**: Ensures uncertainties are within theoretical limits based on entropy.

### 6. Trade-off Analysis
**Principle**: Higher uncertainty should correlate with lower accuracy.

**Method**: Calculate correlation between accuracy and total uncertainty

**Why it matters**: Validates that uncertainty is a meaningful indicator of prediction quality.

### 7. Statistical Significance
**Principle**: All claimed relationships must be statistically significant.

**Method**: 
- Use appropriate statistical tests (Spearman, Pearson, etc.)
- Apply Bonferroni correction for multiple testing
- Report confidence intervals

**Significance level**: p < 0.05

**Why it matters**: Ensures findings are not due to random chance.

## Files

### Main Notebook
- **`logical_consistency_validation.ipynb`**: Complete validation notebook with all checks

### Supporting Scripts
- **`build_consistency_notebook.py`**: Script to generate the notebook programmatically
- **`generate_consistency_notebook.py`**: Alternative generation script (deprecated)

### Input Data
The notebook loads results from:
- `../../results/validation/dataset_size_sweep/metrics.csv`
- `../../results/validation/label_noise_sweep/metrics.csv`

### Output
Results are saved to:
- `../../results/validation/consistency_checks/`
  - `decomposition_validation.png`: Uncertainty decomposition scatter plots
  - `monotonicity_validation.png`: Monotonicity heatmaps
  - `consistency_validation.png`: Cross-architecture correlation heatmaps
  - `validation_report.txt`: Comprehensive text report

## Usage

### Quick Start: Generate Validation Data

**NEW**: Use the automated validation experiment runner to generate all required data:

```bash
# Quick validation (for testing - 2 epochs, fewer samples)
python scripts/run_validation_experiments.py --mode quick

# Full validation (for production - 10 epochs, complete sweeps)
python scripts/run_validation_experiments.py --mode full

# Run only dataset size sweep
python scripts/run_validation_experiments.py --sweep dataset_size

# Run only label noise sweep
python scripts/run_validation_experiments.py --sweep label_noise
```

**What it does**:
- Runs experiments for all 3 architectures (DINOv2+MLP, CNN MC Dropout, ResNet18 MC Dropout)
- Dataset size sweep: 50, 100, 200, 300, 500 samples per class (full mode)
- Label noise sweep: 0%, 10%, 20%, 30%, 40%, 50% noise rates (full mode)
- Automatically saves results to `results/validation/dataset_size_sweep/metrics.csv` and `results/validation/label_noise_sweep/metrics.csv`
- Shows progress and estimated time remaining

**Time estimates**:
- Quick mode: ~30-60 minutes (9 experiments total)
- Full mode: ~3-5 hours (30 experiments total)

### Running the Validation Notebooks

1. **Prerequisites**:
   ```bash
   # Option 1: Use the automated script (recommended)
   python scripts/run_validation_experiments.py --mode full
   
   # Option 2: Run validation notebooks manually
   # - architecture_comparison_dataset_size.ipynb
   # - architecture_comparison_label_noise.ipynb
   ```

2. **Open and run**:
   ```bash
   jupyter notebook logical_consistency_validation.ipynb
   ```

3. **Run all cells**: The notebook will:
   - Load results from both sweeps
   - Perform all 7 validation checks
   - Generate visualizations
   - Create a comprehensive report

### Regenerating the Notebook

If you need to modify the notebook structure:

```bash
python build_consistency_notebook.py
```

This will regenerate `logical_consistency_validation.ipynb` with the latest structure.

## Interpreting Results

### Pass/Fail Criteria

Each validation check has clear pass/fail criteria:

- **✅ PASS**: All checks within tolerance, statistically significant
- **⚠️ WARNING**: Some checks marginal but acceptable
- **❌ FAIL**: Violations detected, requires investigation

### What to Do If Checks Fail

1. **Uncertainty Decomposition Failures**:
   - Check if total_uncertainty is being calculated correctly
   - Verify epistemic and aleatoric calculations
   - Review numerical precision issues

2. **Non-Negativity Failures**:
   - Check for numerical instabilities
   - Review data preprocessing
   - Verify model outputs

3. **Monotonicity Failures**:
   - Review experimental setup
   - Check if trends are as expected
   - Investigate outliers

4. **Consistency Failures**:
   - Compare architecture implementations
   - Check for architecture-specific bugs
   - Review training procedures

## Expected Results

When the system is working correctly, you should see:

- **Decomposition**: >95% of checks pass with mean relative error < 2%
- **Non-Negativity**: 100% pass rate
- **Monotonicity**: All correlations significant (p < 0.05) with correct direction
- **Consistency**: Pairwise correlations > 0.7 for most architecture pairs
- **Overall**: >90% of all checks pass

## Integration with Other Notebooks

This notebook is the **final validation step** in the validation pipeline:

```
1. architecture_comparison_dataset_size.ipynb
   ↓ (generates dataset_size_sweep/metrics.csv)
   
2. architecture_comparison_label_noise.ipynb
   ↓ (generates label_noise_sweep/metrics.csv)
   
3. logical_consistency_validation.ipynb ← YOU ARE HERE
   ↓ (generates consistency_checks/validation_report.txt)
   
4. Final sign-off for model-agnostic system
```

## Troubleshooting

### Common Issues

1. **"File not found" errors**:
   - Ensure you've run the previous validation notebooks
   - Check that results directories exist
   - Verify file paths are correct

2. **"Insufficient data" warnings**:
   - Run more experiments to get sufficient data points
   - Check that experiments completed successfully

3. **Visualization errors**:
   - Ensure matplotlib and seaborn are installed
   - Check that output directory is writable

### Getting Help

If validation checks fail unexpectedly:
1. Review the detailed output in the notebook
2. Check the validation_report.txt for specifics
3. Compare with expected results above
4. Investigate specific failing experiments

## Future Enhancements

Potential additions to this validation notebook:

1. **Calibration checks**: Verify uncertainty calibration
2. **Robustness tests**: Test with adversarial examples
3. **Efficiency metrics**: Compare computational costs
4. **Ablation studies**: Test individual components
5. **Cross-dataset validation**: Test on other datasets

## References

- Uncertainty decomposition: Depeweg et al. (2018)
- Epistemic vs Aleatoric: Kendall & Gal (2017)
- Model-agnostic UQ: Lakshminarayanan et al. (2017)

## Changelog

- **2026-05-24**: Initial creation with 7 core validation checks
- Future updates will be documented here

---

**Note**: This validation notebook is critical for ensuring the reliability and correctness of the uncertainty quantification system. All checks should pass before deploying the system in production.