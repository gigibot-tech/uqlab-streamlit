# MC Dropout Configuration Update

## Summary

Updated MC Dropout configuration to allow `mc_passes=0` (disabled) while defaulting to an efficient value of 5 passes for better performance.

## Changes Made

### 1. Backend Validation (`scripts/run_fast_uncertainty_classification.py`)

**Lines 711-724**: Relaxed validation to allow `mc_passes >= 0`

```python
# Before: Required mc_passes >= 1
if mc_passes < 1:
    raise ValueError(...)

# After: Allow mc_passes >= 0 with warning
if mc_passes < 0:
    raise ValueError(...)
elif mc_passes == 0:
    logger.warning("⚠️  MC Dropout disabled...")
```

### 2. MC Dropout Computation (`scripts/run_fast_uncertainty_classification.py`)

**Lines 327-368**: Handle `mc_passes=0` gracefully

```python
if mc_passes > 0:
    # Normal MC Dropout computation
    mc_predictions = mc_forward_efficient(...)
    uq = calculate_mc_dropout_uncertainty(mc_predictions)
else:
    # MC Dropout disabled - use deterministic predictions
    mc_predictions = mean_pred_det.unsqueeze(0)
    uq = {
        "entropy": torch.zeros(n_samples),
        "mutual_info": torch.zeros(n_samples),
        "mean_variance": torch.zeros(n_samples),
        "mean_prediction": mean_pred_det,
    }
```

### 3. UI Components

#### Progressive App (`streamlit_app_progressive.py` Line 1161-1167)
```python
# Before: min_value=1, value=20
# After:  min_value=0, value=5
mc_passes = st.number_input(
    "MC Dropout passes",
    min_value=0,
    max_value=50,
    value=5,
    help="Set to 0 to disable MC Dropout (faster but no uncertainty). Recommended: 5-10 for efficiency, 20-50 for accuracy."
)
```

#### UI Components Package (`src/uqlab/ui_components/config/experiment_config.py` Line 385-390)
```python
# Before: min_value=5, value=20
# After:  min_value=0, value=5
mc_passes = st.number_input(
    "MC Dropout Passes",
    min_value=0, max_value=100, value=5,
    help="Set to 0 to disable MC Dropout (faster but no uncertainty). Recommended: 5-10 for efficiency, 20-50 for accuracy."
)
```

#### Batch Config (`src/uqlab/ui_components/legacy/batch_config.py` Line 426-433)
```python
# Before: min_value=5, value=20
# After:  min_value=0, value=5
config["mc_passes"] = st.number_input(
    "MC Dropout Passes",
    min_value=0,
    max_value=100,
    value=5,
    help="Set to 0 to disable MC Dropout (faster but no uncertainty). Recommended: 5-10 for efficiency, 20-50 for accuracy."
)
```

## Behavior

### When `mc_passes=0` (MC Dropout Disabled)
- ⚠️ Warning logged: "MC Dropout disabled - no uncertainty quantification"
- All uncertainty metrics set to zero:
  - `entropy = 0`
  - `mutual_info = 0`
  - `mean_variance = 0`
- Uses deterministic prediction for `mean_prediction`
- Faster execution (no multiple forward passes)
- No epistemic uncertainty estimates

### When `mc_passes > 0` (MC Dropout Enabled)
- Normal MC Dropout computation with multiple forward passes
- Full uncertainty quantification:
  - Entropy (predictive uncertainty)
  - Mutual Information (epistemic uncertainty)
  - Mean Variance (aleatoric uncertainty proxy)
- Slower but provides uncertainty estimates

## Recommendations

- **Fast prototyping**: `mc_passes=0` (no uncertainty)
- **Efficient uncertainty**: `mc_passes=5-10` (good balance)
- **Accurate uncertainty**: `mc_passes=20-50` (thorough estimation)
- **Research quality**: `mc_passes=50-100` (high precision)

## Testing

All changes maintain backward compatibility:
- Existing experiments with `mc_passes >= 1` work unchanged
- New experiments can use `mc_passes=0` for faster execution
- Default changed from 20 to 5 for better efficiency

## Files Modified

1. `scripts/run_fast_uncertainty_classification.py` (validation + computation)
2. `streamlit_app_progressive.py` (UI)
3. `src/uqlab/ui_components/config/experiment_config.py` (UI component)
4. `src/uqlab/ui_components/legacy/batch_config.py` (batch UI)

## Related Documentation

- See `RESNET_FIX_SUMMARY.md` for ResNet training mode fixes
- See `ISSUE_1_TEST_RESULTS.md` for ResNet training mode tests
- See `ISSUE_3_TEST_RESULTS.md` for uncertainty metrics tests