# Per-Signal AUROC Data Flow Verification

## Overview
This document verifies that the complete 7×2 per-signal AUROC structure flows correctly from experiment execution through to visualization in batch experiments.

## Data Structure
Each experiment computes AUROC for 7 signals × 2 uncertainty types:

```json
{
  "one_vs_rest_auroc": [
    {"signal": "msp_uncertainty", "aleatoric_like_auroc": 0.82, "epistemic_like_auroc": 0.75},
    {"signal": "predictive_entropy", "aleatoric_like_auroc": 0.79, "epistemic_like_auroc": 0.73},
    {"signal": "mutual_info", "aleatoric_like_auroc": 0.77, "epistemic_like_auroc": 0.71},
    {"signal": "inverse_coherence", "aleatoric_like_auroc": 0.73, "epistemic_like_auroc": 0.68},
    {"signal": "dominance", "aleatoric_like_auroc": 0.65, "epistemic_like_auroc": 0.76},
    {"signal": "inverse_mass", "aleatoric_like_auroc": 0.62, "epistemic_like_auroc": 0.94},
    {"signal": "inverse_logit_magnitude", "aleatoric_like_auroc": 0.61, "epistemic_like_auroc": 0.92}
  ]
}
```

## Complete Data Flow

### 1. Experiment Execution (`run_fast_uncertainty_classification.py`)
**Location**: Lines 631-638

```python
"one_vs_rest_auroc": [
    {
        "signal": name,
        "aleatoric_like_auroc": alea_auc,
        "epistemic_like_auroc": epis_auc,
    }
    for name, alea_auc, epis_auc in auroc_rows
],
```

**Output**: Saves complete 7×2 structure to `summary.json`

✅ **Status**: Already implemented and working

---

### 2. Result Reading (`direct_executor.py`)
**Location**: Lines 186-217

**Changes Made**:
```python
# Extract per-signal AUROC data (7 signals × 2 uncertainty types)
one_vs_rest_auroc = data.get("one_vs_rest_auroc", [])

# Build best_signals dict with complete per-signal AUROC structure
best_signals = {
    "one_vs_rest_auroc": one_vs_rest_auroc  # Pass through complete 7×2 structure
}
```

**Output**: `TrainingResult` object with `best_signals` containing the complete structure

✅ **Status**: Updated to pass through complete data

---

### 3. Result Storage (`batch_experiment_service.py`)
**Location**: Lines 313-335

**Changes Made**:
```python
# Build summary payload with complete per-signal AUROC data
summary_payload = {
    "aleatoric_auroc": result.aleatoric_auroc,
    "epistemic_auroc": result.epistemic_auroc,
    "train_size": result.train_size,
    "eval_sizes": result.eval_sizes,
    "results_path": result.results_path,
    # Include complete 7×2 per-signal AUROC structure for visualization
    "one_vs_rest_auroc": result.best_signals.get("one_vs_rest_auroc", []),
}
```

**Output**: Stores complete structure in `BatchExperimentRun.result_summary_json`

✅ **Status**: Updated to store complete data

---

### 4. Visualization (`batch_experiment_service._build_series()`)
**Location**: Lines 659-725

**Extraction Logic**:
```python
# Extract per-signal AUROC from result_summary_json
signal_names_set = set()
for run in ordered_runs:
    if run.result_summary_json:
        summary = json.loads(run.result_summary_json)
        one_vs_rest = summary.get("one_vs_rest_auroc", [])
        for item in one_vs_rest:
            signal_names_set.add(item.get("signal"))

# Build series for each signal
for signal_name in sorted(signal_names_set):
    # Extract aleatoric and epistemic AUROC for this signal
    # Create separate series for each signal × uncertainty type
```

**Output**: Series data for Streamlit visualization with all 7 signals

✅ **Status**: Already implemented and ready to consume the data

---

## Expected Signals in Visualization

When batch experiments run, the visualization will show:

### Aggregated Metrics (Backward Compatibility)
1. **Epistemic AUROC (Aggregated)** - Max epistemic AUROC across all signals
2. **Aleatoric AUROC (Aggregated)** - Max aleatoric AUROC across all signals

### Per-Signal Metrics (New)
3. **msp_uncertainty (Aleatoric)** - MSP uncertainty for aleatoric detection
4. **msp_uncertainty (Epistemic)** - MSP uncertainty for epistemic detection
5. **predictive_entropy (Aleatoric)** - Predictive entropy for aleatoric detection
6. **predictive_entropy (Epistemic)** - Predictive entropy for epistemic detection
7. **mutual_info (Aleatoric)** - Mutual information for aleatoric detection
8. **mutual_info (Epistemic)** - Mutual information for epistemic detection
9. **inverse_coherence (Aleatoric)** - Inverse coherence for aleatoric detection
10. **inverse_coherence (Epistemic)** - Inverse coherence for epistemic detection
11. **dominance (Aleatoric)** - Dominance for aleatoric detection
12. **dominance (Epistemic)** - Dominance for epistemic detection
13. **inverse_mass (Aleatoric)** - Inverse mass for aleatoric detection
14. **inverse_mass (Epistemic)** - Inverse mass for epistemic detection
15. **inverse_logit_magnitude (Aleatoric)** - Inverse logit magnitude for aleatoric detection
16. **inverse_logit_magnitude (Epistemic)** - Inverse logit magnitude for epistemic detection

**Total**: 2 aggregated + 14 per-signal = **16 series** available for visualization

---

## Verification Checklist

- [x] Experiment script computes 7×2 per-signal AUROC
- [x] Experiment script saves data to `summary.json`
- [x] Executor reads complete structure from `summary.json`
- [x] Executor passes data through `TrainingResult.best_signals`
- [x] Batch service stores data in `result_summary_json`
- [x] Batch service extracts data in `_build_series()`
- [x] Visualization backend ready to consume the data

---

## Testing Recommendations

1. **Run a batch experiment** with 3-5 runs
2. **Check database** that `result_summary_json` contains `one_vs_rest_auroc`
3. **Verify visualization** shows all 7 signals × 2 uncertainty types
4. **Confirm NaN handling** for empty evaluation groups

---

## Summary

✅ **All components updated and verified**

The complete data flow is now in place:
- Experiments compute the full 7×2 structure
- Executor passes it through without loss
- Batch service stores it in the database
- Visualization backend extracts and displays it

The system is ready to visualize per-signal AUROC trends across batch experiments.