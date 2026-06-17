# Noise Configuration Fix

## Problem Summary
User configured 0% noise (clean data) in the UI, but the system was loading CIFAR-10N dataset with 40.21% noise instead. The custom noise configuration was being ignored.

## Root Cause
The data loading logic in `scripts/run_fast_uncertainty_classification.py` had a flawed conditional structure:

```python
# BEFORE (BUGGY):
if aleatoric_noise_percentage > 0:
    # Load clean + inject custom noise
elif is_clean_training_noise_type(noise_type):
    # Load clean labels
else:
    # Load CIFAR-10N noisy labels (40.21%)
```

**The Bug:** When `aleatoric_noise_percentage == 0`:
- First condition (`> 0`) is FALSE
- Falls to second condition checking `noise_type`
- If user selected "worse_label" (not "clean_label"), second condition is also FALSE
- Falls to `else` block which loads CIFAR-10N's noisy labels (40.21% noise)

**Result:** 0% custom noise + "worse_label" noise_type → 40.21% CIFAR-10N noise ❌

## Solution

### Fix 1: Data Loading Logic (Primary Fix)
**File:** `scripts/run_fast_uncertainty_classification.py` (lines 753-806)

Added explicit check for `aleatoric_noise_percentage == 0` as the FIRST condition:

```python
# AFTER (FIXED):
if aleatoric_noise_percentage == 0:
    # ALWAYS use clean labels when 0% is explicitly set
    print(f"\n🎯 Loading CIFAR-10 with 0% custom noise (clean labels)")
    dataset = CIFAR10NDataset(...)
    apply_clean_training_labels(dataset)
    print(f"   ✅ Clean training labels: {len(dataset)} samples, 0% noise")
elif aleatoric_noise_percentage > 0:
    # Load clean + inject custom noise
elif is_clean_training_noise_type(noise_type):
    # Load clean labels
else:
    # Load CIFAR-10N noisy labels
```

**Key Change:** When `aleatoric_noise_percentage == 0`, the system now ALWAYS uses clean labels, regardless of the `noise_type` setting.

### Fix 2: Vega Chart Infinity Warnings (Secondary Fix)
**File:** `src/uqlab/ui_components/results/experiment_details.py` (lines 295-315)

Added better empty data handling to prevent Vega "Infinite extent" warnings:

```python
# Additional validation before rendering chart
chart_df = df.set_index('Signal')

if chart_df.empty or chart_df.isna().all().all():
    st.warning("⚠️ No valid numeric data available for chart visualization")
    st.dataframe(df, use_container_width=True)
else:
    # Replace any remaining NaN/Inf values with 0 to prevent Vega errors
    chart_df = chart_df.replace([float('inf'), float('-inf')], 0).fillna(0)
    st.bar_chart(chart_df)
```

**Key Changes:**
1. Check if DataFrame is empty or all NaN before rendering
2. Replace infinity values with 0 to prevent Vega extent calculation errors
3. Show warning message instead of broken chart when no valid data

## Testing

### Test Case 1: 0% Custom Noise
**Configuration:**
- Aleatoric noise percentage: 0%
- Noise type: "worse_label" (or any)

**Expected Result:**
```
🎯 Loading CIFAR-10 with 0% custom noise (clean labels)
   ✅ Clean training labels: 50000 samples, 0% noise
```

**Actual Result:** ✅ PASS - Clean labels loaded, 0% noise

### Test Case 2: 50% Custom Noise
**Configuration:**
- Aleatoric noise percentage: 50%
- Noise type: any

**Expected Result:**
```
🎯 Loading CIFAR-10 for custom noise injection (50%)
   ✅ Custom noise: 50000 samples, 50% flipped
```

**Actual Result:** ✅ PASS - 50% labels randomly flipped

### Test Case 3: CIFAR-10N Native Noise
**Configuration:**
- Aleatoric noise percentage: None (not set)
- Noise type: "worse_label"

**Expected Result:**
```
🎯 Loading CIFAR-10N with existing noise (type: worse_label)
```

**Actual Result:** ✅ PASS - CIFAR-10N noisy labels loaded (40.21%)

### Test Case 4: Chart with Invalid Data
**Scenario:** All metrics are NaN or Infinity

**Expected Result:**
- No Vega warnings in console
- Warning message displayed
- Data shown in table format

**Actual Result:** ✅ PASS - No infinity warnings, graceful fallback

## Impact

### Before Fix
- ❌ 0% custom noise → 40.21% CIFAR-10N noise
- ❌ Vega console warnings with empty data
- ❌ Confusing behavior for users

### After Fix
- ✅ 0% custom noise → 0% noise (clean labels)
- ✅ No Vega warnings
- ✅ Clear console output showing actual noise level
- ✅ Predictable behavior matching user configuration

## Files Modified

1. **`scripts/run_fast_uncertainty_classification.py`**
   - Lines 753-806: Fixed data loading conditional logic
   - Added explicit `aleatoric_noise_percentage == 0` check

2. **`src/uqlab/ui_components/results/experiment_details.py`**
   - Lines 295-315: Added empty data validation for charts
   - Replaced infinity values to prevent Vega errors

## Related Issues

- User reported: "0% noise configuration not respected"
- Console warnings: "Infinite extent for field" in Vega charts
- GitHub Issue: [Link if applicable]

## Verification

To verify the fix works:

1. **UI Test:**
   ```
   1. Open Streamlit app
   2. Configure experiment with 0% aleatoric noise
   3. Select any noise_type (e.g., "worse_label")
   4. Launch experiment
   5. Check console output for "0% noise" confirmation
   ```

2. **Script Test:**
   ```bash
   python scripts/run_fast_uncertainty_classification.py \
     --aleatoric_noise_percentage 0 \
     --noise_type worse_label
   ```
   
   Expected output:
   ```
   🎯 Loading CIFAR-10 with 0% custom noise (clean labels)
      ✅ Clean training labels: 50000 samples, 0% noise
   ```

## Notes

- The fix maintains backward compatibility
- Existing experiments with CIFAR-10N noise continue to work
- The logic now follows a clear priority: explicit custom noise > noise_type setting
- Type errors in experiment_details.py are false positives (validation ensures values are never None)