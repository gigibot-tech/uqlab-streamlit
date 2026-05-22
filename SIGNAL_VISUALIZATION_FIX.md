# Per-Signal AUROC Visualization Fix

## Problem
The per-signal AUROC visualization in `ui_components.py` was showing "No per-signal data found in experiment directories" even though batch experiments completed successfully with all 7 signals.

## Root Cause
The code had an incorrect path construction when searching for experiment directories:

```python
# WRONG - This was looking for experiments/exp_* inside batch_dir
exp_dirs = sorted([d for d in Path(batch_dir).glob("experiments/exp_*") if d.is_dir()])
```

The actual directory structure is:
```
/tmp/walaris_experiments/batch_{id}/
├── experiments/
│   ├── exp_1_under_train_per_class_5/
│   ├── exp_2_under_train_per_class_10/
│   └── ...
```

The glob pattern `"experiments/exp_*"` was incorrect because it was being applied to `batch_dir`, not to the experiments subdirectory.

## Solution

### 1. Fixed Path Construction
Changed to properly construct the experiments directory path first:

```python
# CORRECT - First get the experiments directory, then glob within it
experiments_dir = Path(batch_dir) / "experiments"
exp_dirs = sorted([d for d in experiments_dir.glob("exp_*") if d.is_dir()])
```

### 2. Fixed Config Parameter Extraction
The config structure has parameters nested under a `data` key:

```yaml
data:
  under_train_per_class: 5
  regular_train_per_class: null
  eval_per_group: 100
```

Updated the code to look in `config.get("data", {})` instead of directly in `config`.

### 3. Added Comprehensive Debugging
Added a debug expander that shows:
- Batch ID and directory path
- Whether directories exist
- Number of experiment directories found
- List of experiment directory names

Added informative warnings and error messages at each step:
- When experiments directory doesn't exist
- When no experiment directories are found
- When summary.json or config.yaml are missing
- When parameter values can't be extracted
- When one_vs_rest_auroc data is missing

### 4. Added Error Handling
Wrapped file reading in try-except blocks with detailed error messages and stack traces to help diagnose issues.

## Testing

Created `test_signal_loading.py` to verify the fix works correctly. Test results:

```
✅ Successfully loaded 7 signals from 10 experiments
   X-axis values: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
   Signals found: ['msp_uncertainty', 'predictive_entropy', 'mutual_info', 
                    'inverse_coherence', 'dominance', 'inverse_mass', 
                    'inverse_logit_magnitude']
```

All 7 signals are now correctly loaded with both aleatoric and epistemic AUROC values across all parameter sweep points.

## Files Modified

1. **walaris-cen/ui_components.py** (lines 1783-1870)
   - Fixed path construction for experiment directories
   - Fixed config parameter extraction to look in `data` section
   - Added comprehensive debugging output
   - Added detailed error handling and informative messages
   - Initialized `exp_dirs` to avoid unbound variable issues

2. **walaris-cen/test_signal_loading.py** (new file)
   - Test script to verify signal data loading
   - Can be run standalone to diagnose issues
   - Usage: `python3 test_signal_loading.py [batch_id]`

## Verification Steps

To verify the fix works in the UI:

1. Start the Streamlit app
2. Navigate to a completed batch experiment
3. Scroll to the "📊 Per-Signal AUROC Analysis" section
4. You should now see:
   - Debug information showing the batch directory and experiment count
   - Success message: "✅ Loaded 7 signals from N experiments"
   - Three tabs with visualizations of all 7 signals
   - Both aleatoric and epistemic curves for each signal

## Signal Categories

The visualization organizes signals into three categories:

1. **Predictive Uncertainty**: msp_uncertainty, predictive_entropy, mutual_info
2. **Attribution-Based (DualXDA)**: inverse_coherence, dominance
3. **Logit-Based (Representer)**: inverse_mass, inverse_logit_magnitude

Each signal shows both aleatoric-like and epistemic-like AUROC values across the parameter sweep.