# Fix: Detailed Metrics Not Rendering in Progressive UI

## Problem
Users reported that the "detailed metrics" section was not being rendered in the progressive Streamlit app. The metrics were actually being rendered, but they were hidden behind collapsed expanders, making them difficult to discover.

## Root Cause Analysis

The detailed metrics functionality was **already implemented** and working correctly:

1. **`experiment_details.py`** - Contains `render_experiment_details_with_metrics()` function that displays:
   - All 7 uncertainty signals with AUROC scores
   - Best signal recommendations
   - Training data inspection
   - Visual comparisons
   - Uncertainty type explanations

2. **`sweep_grouping.py`** - Contains `render_sweep_group_summary()` that calls the detailed metrics function for sweep experiments

3. **`streamlit_app_progressive.py`** - Already imports and calls these functions

**The issue:** All expanders were collapsed by default (`expanded=False`), so users didn't realize the detailed metrics were available.

## Solution Implemented

### Changes to `streamlit_app_progressive.py`

#### 1. Parameter Sweeps Section (Lines 290-302)
**Before:**
- All sweep group expanders collapsed by default
- No guidance on where to find detailed metrics

**After:**
```python
# Added helpful tip
st.info("💡 **Tip:** Expand a sweep group below to see detailed metrics for each experiment, including all 7 uncertainty signals with AUROC scores!")

# Expand first sweep group by default
with st.expander(
    f"🔬 {group['name']} ({len(group['experiments'])} runs)",
    expanded=(i == 0)  # Expand first group by default
):
    render_sweep_group_summary(group, show_details=True)
```

#### 2. Standalone Experiments Section (Lines 304-344)
**Before:**
- Standalone experiments expander always collapsed
- First experiment's detailed metrics collapsed

**After:**
```python
# Auto-expand if there are completed experiments with metrics
completed_standalone = [e for e in standalone if e['status'] == 'completed' and e.get('best_signals_json')]
has_metrics = len(completed_standalone) > 0

with st.expander(f"📋 View {len(standalone)} Standalone Experiments", expanded=has_metrics):
    # ... table view ...
    
    # Added clear section header and helpful info
    st.markdown("**📊 Detailed Metrics (All 7 Uncertainty Signals):**")
    
    if completed_standalone:
        st.info("💡 **Expand an experiment below to see:**\n- All 7 uncertainty signals with AUROC scores\n- Best signal recommendations\n- Training data inspection\n- Visual comparisons")
        
        # Expand first completed experiment by default
        for i, exp in enumerate(completed_standalone):
            with st.expander(f"🔬 {exp['name']} - Detailed Metrics", expanded=(i == 0)):
                render_experiment_details_with_metrics(exp, show_explanation=True)
```

## What Users Will See Now

### 1. **Parameter Sweeps**
- Clear tip message explaining where to find detailed metrics
- First sweep group automatically expanded
- Within each sweep group, detailed metrics for all completed experiments

### 2. **Standalone Experiments**
- Section automatically expands if there are completed experiments with metrics
- Clear section header: "Detailed Metrics (All 7 Uncertainty Signals)"
- Helpful info box explaining what's available
- First completed experiment's detailed metrics automatically expanded

### 3. **Detailed Metrics Content**
When expanded, users see:
- **Comprehensive metrics table** with all 7 signals
- **Performance indicators** (🟢 Excellent, 🟡 Good, 🟠 Fair, 🔴 Poor)
- **Best performing signals** for aleatoric, epistemic, and overall
- **Visual comparison chart** (bar chart)
- **Training data inspection** (if available)
- **Uncertainty explanation** (expandable)

## Testing Recommendations

1. **With sweep experiments:**
   - Launch a parameter sweep
   - Verify first sweep group is expanded by default
   - Verify tip message appears
   - Expand a sweep group and verify detailed metrics are shown

2. **With standalone experiments:**
   - Launch a single experiment
   - Wait for completion
   - Verify standalone section auto-expands
   - Verify first experiment's detailed metrics are expanded
   - Verify info box with bullet points appears

3. **With no completed experiments:**
   - Verify appropriate "will be available after completion" messages appear

## Files Modified

1. **`streamlit_app_progressive.py`**
   - Lines 290-302: Parameter sweeps section
   - Lines 304-344: Standalone experiments section

## No Breaking Changes

- All existing functionality preserved
- Only UI/UX improvements (auto-expansion and guidance)
- No changes to data structures or API calls
- Backward compatible with existing experiments

## Benefits

1. **Improved discoverability** - Users immediately see where detailed metrics are
2. **Better UX** - First items auto-expand to show what's available
3. **Clear guidance** - Info messages explain what users will find
4. **Progressive disclosure** - Still uses expanders to keep UI clean, but makes content more accessible

## Related Files

- `src/uqlab/ui_components/results/experiment_details.py` - Detailed metrics rendering (unchanged)
- `src/uqlab/ui_components/grouping/sweep_grouping.py` - Sweep group summary (unchanged)
- `streamlit_app_progressive.py` - Main UI file (modified)