# Vega-Lite Chart Infinite Extent Error - Fix Summary

## Problem
The Streamlit app was freezing with console errors:
```
WARN Infinite extent for field "value - streamlit-generated_start": [Infinity, -Infinity]
WARN Infinite extent for field "value - streamlit-generated_end": [Infinity, -Infinity]
WARN Dropping "fit-x" because spec has discrete width
```

This occurred in the signal comparison chart in the experiment details view, causing the entire app to become unresponsive.

## Root Cause
The `_render_signal_comparison_chart()` function in `experiment_details.py` was passing invalid data (NaN, Infinity, or None values) to Streamlit's `st.bar_chart()`, which uses Vega-Lite internally. When Vega-Lite received these invalid values, it couldn't calculate proper extents for the chart axes, resulting in infinite extents and causing the rendering to fail.

## Solution Implemented

### File Modified
`src/uqlab/ui_components/results/experiment_details.py`

### Changes Made

1. **Added `math` import** (line 12)
   - Required for `math.isnan()` and `math.isinf()` functions

2. **Enhanced `_render_signal_comparison_chart()` function** (lines 237-307)
   - Added comprehensive input validation
   - Created `is_valid_auroc()` helper function to validate AUROC scores
   - Filters out invalid data before creating the DataFrame
   - Tracks skipped signals and reports them to the user
   - Added try-except block around chart rendering
   - Provides fallback display if chart fails

### Key Features of the Fix

#### Data Validation
```python
def is_valid_auroc(value):
    """Check if value is a valid AUROC score."""
    if value is None:
        return False
    try:
        val = float(value)
        # Check for NaN, Infinity, and valid range
        if not (-1 <= val <= 1) or math.isnan(val) or math.isinf(val):
            return False
        return True
    except (ValueError, TypeError):
        return False
```

This function validates that:
- Value is not None
- Value can be converted to float
- Value is not NaN or Infinity
- Value is within valid AUROC range (-1 to 1)

#### Graceful Degradation
- If no metrics data: Shows info message
- If all data invalid: Shows warning with explanation
- If some data invalid: Shows chart with valid data + warning about skipped signals
- If chart rendering fails: Shows error + displays data in table format

#### User Feedback
- Clear messages about what data is missing or invalid
- Lists which signals were skipped due to invalid data
- Provides debug information if chart fails to render

## Testing Recommendations

1. **Test with valid data**: Verify chart renders correctly with normal AUROC values
2. **Test with NaN values**: Ensure app doesn't freeze, shows appropriate warning
3. **Test with Infinity values**: Ensure app doesn't freeze, shows appropriate warning
4. **Test with missing data**: Ensure graceful handling with info messages
5. **Test with mixed data**: Some valid, some invalid - should show chart with valid data only

## Benefits

1. **No more app freezing**: Invalid data is filtered out before reaching Vega-Lite
2. **Better user experience**: Clear messages about what's wrong
3. **Debugging support**: Shows which signals have invalid data
4. **Robust error handling**: Multiple layers of validation and fallbacks
5. **Maintains functionality**: Chart still works with valid data even if some signals are invalid

## Related Files

- `src/uqlab/ui_components/results/experiment_details.py` - Main fix location
- Other chart functions in the same file may benefit from similar validation patterns

## Future Improvements

Consider applying similar validation patterns to:
- `_render_metrics_table()` function
- `_render_best_signals()` function
- Any other visualization functions that process AUROC or metric data

## Notes

- The fix is backward compatible - works with both old and new data formats
- No changes required to data storage or API
- Fix is defensive - validates at the UI layer before rendering