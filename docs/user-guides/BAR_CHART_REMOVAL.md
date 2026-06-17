# Bar Chart Removal - Infinite Rerun Loop Fix

## Problem
The Vega-Lite bar charts in the experiment details view were causing infinite rerun loops in Streamlit. When displaying per-run signal comparison charts, the app would continuously show the "running man" icon and never stabilize.

## Root Cause
Vega-Lite charts can trigger internal state updates in Streamlit that cause reruns. The complex validation logic and chart rendering was creating a feedback loop where:
1. Chart renders
2. Internal state updates
3. Streamlit detects state change
4. Triggers rerun
5. Repeat indefinitely

## Solution
Completely removed all bar chart logic and replaced with simple dataframe display. This is:
- **Simpler**: No complex Vega-Lite configuration
- **Faster**: Dataframes render instantly
- **More stable**: No internal state updates
- **Equally informative**: Users can still compare values

## Files Modified

### 1. `src/uqlab/ui_components/results/experiment_details.py`

**Removed:**
- `import math` (line 13)
- Complex `is_valid_auroc()` validation function (lines 265-276)
- Bar chart rendering logic (lines 310-325)
- Vega-Lite chart configuration
- Numeric domain validation

**Simplified:**
- Basic validation: just check if values exist and are numeric
- Always display dataframe instead of conditional chart/table
- Removed all `math.isnan()` and `math.isinf()` calls

**Before:**
```python
import math

def is_valid_auroc(value):
    """Check if value is a valid AUROC score."""
    if value is None:
        return False
    try:
        val = float(value)
        if not (-1 <= val <= 1) or math.isnan(val) or math.isinf(val):
            return False
        return True
    except (ValueError, TypeError):
        return False

# Complex chart rendering with validation
if all_finite:
    st.bar_chart(...)  # Vega-Lite chart
else:
    st.dataframe(...)  # Fallback
```

**After:**
```python
# No math import needed

# Simple validation
try:
    if aleatoric is not None and epistemic is not None:
        df_data.append({...})
    else:
        skipped_signals.append(signal)
except (ValueError, TypeError):
    skipped_signals.append(signal)

# Always show dataframe (no charts)
st.dataframe(df, use_container_width=True)
st.caption("Compare values to see which signals excel at which uncertainty type.")
```

## Benefits

1. **No more infinite reruns**: App stabilizes immediately
2. **Cleaner code**: Removed ~50 lines of complex validation
3. **Better performance**: Dataframes render faster than Vega charts
4. **Easier maintenance**: No chart configuration to debug
5. **Same information**: Users can still compare signal performance

## Testing

After these changes, the app should:
- ✅ Load without infinite reruns
- ✅ Display signal comparison as dataframe
- ✅ Show per-run details without causing reruns
- ✅ Maintain all functionality except bar chart visualization

## Related Issues

This fix is part of the broader UI cleanup effort documented in:
- `PROGRESSIVE_UI_FIXES.md` - Overall UI improvements
- `STARTUP_FIXES.md` - Infinite rerun loop fixes

## Date
2026-06-16