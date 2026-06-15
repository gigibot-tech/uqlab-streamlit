# CRITICAL VALIDATION SYSTEM BUGS - SCIENTIFIC CORRECTNESS ISSUE

**Status**: 🟡 PARTIALLY FIXED - Dataset size methodology fixed, noise scale bug remains
**Date Identified**: 2026-05-25
**Date Fixed**: 2026-05-25 (Dataset size methodology)
**Impact**: Label noise sweep validation results still invalid; dataset size sweep now scientifically correct

---

## Executive Summary

Two critical bugs were identified in the validation system:

1. **CONFIRMED: Noise Scale Mismatch (100x error)** - ⏳ NOT YET FIXED - Label noise is being applied at 100x lower than intended
2. **FIXED: Dataset Size Methodology Mismatch** - ✅ FIXED - Now matches original paper methodology with epoch adjustment

---

## Bug #1: Noise Scale Mismatch (CONFIRMED CRITICAL)

### The Problem

The validation runner passes noise values on a **0-1 scale** (0.0, 0.1, 0.2, 0.3, 0.4, 0.5), but the training code interprets `aleatoric_noise_percentage` on a **0-100 scale**.

### Evidence

**File: `scripts/run_validation_experiments.py`**
```python
# Line 72-75: Noise sweep defined on 0-1 scale
LABEL_NOISE_SWEEP = {
    'quick': [0.0, 0.2, 0.4],
    'full': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]  # ← 0-1 scale
}

# Line 352: Printed as percentage (misleading)
print(f"{arch_info['name']} - {noise_rate*100:.0f}% label noise")

# Line 118: Passed directly without conversion
'aleatoric_noise_percentage': noise_rate if noise_rate is not None else 0.0
```

**File: `scripts/run_fast_uncertainty_classification.py`**
```python
# Line 464: Expects 0-100 scale
print(f"Loading CIFAR-10N for custom noise injection ({aleatoric_noise_percentage}%)")

# Line 481: Passes to inject_custom_noise() which expects 0-100
dataset.inject_custom_noise(noise_percentage=aleatoric_noise_percentage, seed=42)
```

**File: `src/data/cifar10n_loader.py`**
```python
# Line 89-106: inject_custom_noise() clearly expects 0-100 scale
def inject_custom_noise(self, noise_percentage: float, seed: int = 42):
    """
    Args:
        noise_percentage: Percentage of labels to corrupt (0-100)  # ← 0-100 scale!
    """
    if noise_percentage > 100:
        raise ValueError(f"noise_percentage must be between 0 and 100, got {noise_percentage}")
    
    # Line 119: Divides by 100 to get fraction
    num_noisy = int(num_samples * (noise_percentage / 100.0))
```

### Impact

| Intended Noise | Actual Noise | Error Factor |
|----------------|--------------|--------------|
| 10% | 0.1% | 100x too low |
| 20% | 0.2% | 100x too low |
| 30% | 0.3% | 100x too low |
| 40% | 0.4% | 100x too low |
| 50% | 0.5% | 100x too low |

**This explains why the uncertainty curves barely move in the validation results!**

### Root Cause

The validation runner was written assuming a 0-1 scale (common in ML code), but the noise injection function uses a 0-100 scale (more intuitive for percentages). No validation or unit tests caught this mismatch.

### Fix Required

**Option A: Multiply by 100 in validation runner (RECOMMENDED)**
```python
# Line 118 in run_validation_experiments.py
'aleatoric_noise_percentage': noise_rate * 100 if noise_rate is not None else 0.0
```

**Option B: Change inject_custom_noise() to use 0-1 scale**
- More invasive
- Requires updating all callers
- Not recommended

---

## Bug #2: Dataset Size Methodology Mismatch (✅ FIXED)

### The Problem (RESOLVED)

The original paper uses a different methodology for dataset size sweeps than the current implementation. **This has been confirmed by examining the research package code and has now been FIXED.**

### Original Paper Methodology (CONFIRMED)

**File: `uq_disentanglement_comparison-72CC/disentanglement/benchmarks/decreasing_dataset.py`**
```python
# Lines 48-62: Original research implementation
dataset_sizes = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]  # Fractions of full dataset

for dataset_size in dataset_sizes:
    small_dataset = create_subsampled_dataset(X_train, y_train, dataset, dataset_size)
    adjusted_epochs = int(epochs / dataset_size)  # ← KEY: Epochs scale inversely
    
    # Train with adjusted epochs
    results.append_values(*disentanglement_func(small_dataset, model_function, adjusted_epochs))
```

**Example**: If base epochs = 10:
- 10% dataset → 100 epochs (10 / 0.1)
- 50% dataset → 20 epochs (10 / 0.5)
- 100% dataset → 10 epochs (10 / 1.0)

**Rationale**: Keeps total gradient steps approximately constant across dataset sizes.

### Current Implementation

**File: `scripts/run_validation_experiments.py`**
```python
# Lines 67-69: Current implementation
DATASET_SIZE_SWEEP = {
    'full': [50, 100, 200, 300, 500]  # Absolute per-class sample counts (not fractions!)
}

# Lines 87-88: Fixed epochs
'epochs': 10  # Same for ALL dataset sizes
```

### Impact

| Dataset Size | Paper Approach | Current Approach | Gradient Steps Ratio |
|--------------|----------------|------------------|---------------------|
| 50 samples/class | ~100 epochs | 10 epochs | 10x fewer |
| 100 samples/class | ~50 epochs | 10 epochs | 5x fewer |
| 500 samples/class | ~10 epochs | 10 epochs | Same |

**Scientific Issues**:

1. **Convergence inequality**: Smaller datasets get 10x fewer gradient steps
   - May not converge properly
   - Unfair comparison across dataset sizes

2. **Uncertainty measurement bias**: Under-trained models show higher epistemic uncertainty
   - Not due to dataset size, but due to under-training
   - Confounds the experimental variable

3. **Non-comparable to paper**: Results cannot be compared to published research

### Fix Implemented ✅

**Implementation: Option B - Keep absolute counts with epoch adjustment**

The fix was implemented in `scripts/run_validation_experiments.py` (lines 280-325) using the following approach:

```python
# Calculate adjusted epochs to maintain constant total gradient steps
max_dataset_size = max(dataset_sizes)  # 500 for full mode
base_epochs = TRAINING_CONFIG[mode]['epochs']  # 10 for full mode

for dataset_size in dataset_sizes:
    # Formula: adjusted_epochs = base_epochs * (max_size / current_size)
    adjusted_epochs = int(base_epochs * (max_dataset_size / dataset_size))
    
    # Override epochs in config
    config['training']['epochs'] = adjusted_epochs
```

**Resulting epoch schedule for full mode:**
- 50 samples/class: 100 epochs (10 * 500/50)
- 100 samples/class: 50 epochs (10 * 500/100)
- 200 samples/class: 25 epochs (10 * 500/200)
- 300 samples/class: 16 epochs (10 * 500/300, rounded down)
- 500 samples/class: 10 epochs (10 * 500/500)

**Benefits:**
1. ✅ Maintains approximately constant total gradient steps across dataset sizes
2. ✅ Ensures fair comparison - uncertainty differences are due to dataset size, not under-training
3. ✅ Matches scientific methodology from original research paper
4. ✅ Keeps intuitive absolute sample counts instead of fractions

---

## Action Plan

### Immediate Actions (Critical)

1. ✅ **Document the bugs** (this file)
2. ⏳ **Fix noise scale bug** in `run_validation_experiments.py` - NOT YET DONE
3. ✅ **Fix dataset size methodology** - COMPLETED (2026-05-25)
4. ⏳ **Re-run dataset size validation experiments** with corrected epoch adjustment
5. ⏳ **Fix noise scale bug and re-run label noise experiments**
6. ⏳ **Update validation notebooks** to use new results

### Validation Steps

Before accepting new results:
- [ ] Verify noise injection is working correctly (check actual noise rates)
- [ ] Verify uncertainty curves show expected behavior with noise
- [ ] Compare results to paper's reported values
- [ ] Document any remaining discrepancies

### Prevention Measures

- [ ] Add unit tests for noise injection scale
- [ ] Add validation checks in config loading
- [ ] Add assertions to verify noise rates match expectations
- [ ] Document parameter scales in docstrings

---

## Files Affected

### Fixed ✅
- `scripts/run_validation_experiments.py` - Lines 280-325 (dataset size epoch adjustment implemented)
- `CRITICAL_VALIDATION_BUGS.md` - Updated to reflect fix status

### Must Fix ⏳
- `scripts/run_validation_experiments.py` - Line 118 (noise scale conversion) - NOT YET FIXED

### Must Re-run
- All experiments in `results/validation/dataset_size_sweep/` - with new epoch adjustment
- All experiments in `results/validation/label_noise_sweep/` - after noise scale bug is fixed
- All validation notebooks that use these results

---

## Timeline Estimate

- **Bug fix**: 5 minutes
- **Investigation of dataset size methodology**: 30-60 minutes
- **Re-running validation experiments**:
  - Quick mode: ~30 minutes
  - Full mode: ~2-4 hours (depending on hardware)
- **Notebook updates**: 30 minutes
- **Total**: 3-6 hours for complete fix and validation

---

## Notes

- The noise scale bug is **100% confirmed** - the code is unambiguous - ⏳ NOT YET FIXED
- The dataset size methodology issue has been **FIXED** ✅ (2026-05-25)
- All current validation results for label noise sweeps are **scientifically invalid** and must be discarded
- All current dataset size sweep results are **scientifically invalid** and must be re-run with the new epoch adjustment
- After re-running with the fix, dataset size results will be scientifically valid and comparable to the original paper

---

**Prepared by**: Bob (AI Assistant)  
**Review Required**: Human validation of fix before re-running experiments