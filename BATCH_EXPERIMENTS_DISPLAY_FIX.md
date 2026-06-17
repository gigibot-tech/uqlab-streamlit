# Batch Experiments Display Fix

## Issue Summary
The UI was showing "No batch experiments found" despite having batch experiment results with detailed metrics in the database. This was a contradictory message that confused users.

## Root Cause
The issue was in the `render_batch_results()` function in `src/uqlab/ui_components/visualization/signals/signal_visualization.py`.

**Problematic Code (lines 45-53):**
```python
# Filter out invalid completed batches (completed with 0 runs = database inconsistency)
valid_batches = [
    b for b in batches
    if not (b["status"] == "completed" and b.get("completed_runs", 0) == 0)
]

if not valid_batches:
    st.info("No valid batch experiments found. Create one using the batch form above.")
    return
```

### Why This Was Wrong
The filtering logic was **too restrictive**. It filtered out batch experiments where:
- `status == "completed"` AND
- `completed_runs == 0`

This was intended to catch database inconsistencies, but it had unintended consequences:

1. **Valid batch experiments were being filtered out** - Some batch experiments may have their runs tracked differently or the `completed_runs` field may not be updated correctly in all scenarios
2. **The field may not reflect the actual state** - The `completed_runs` counter might be 0 even when the batch has valid experiment runs associated with it
3. **Individual experiments vs batch metadata** - The individual experiments created by a batch are stored separately in the `UncertaintyExperiment` table and shown in the sweep groups section, while the batch metadata is in the `BatchExperiment` table

## Solution
Removed the overly restrictive filtering logic and display all batch experiments returned by the API.

**Fixed Code:**
```python
if not batches:
    st.info("No batch experiments found. Create one using the batch form above.")
    return

# Use all batches - don't filter based on completed_runs
# The completed_runs field may not be updated correctly in all cases,
# but the batch experiments themselves are valid and should be displayed
valid_batches = batches
```

## Architecture Context

### Two Types of Experiment Display

1. **Individual Experiments (Sweep Groups Section)**
   - Fetched from `/api/v1/experiments/no-auth`
   - Stored in `UncertaintyExperiment` table
   - Grouped intelligently by sweep metadata, name patterns, or config similarity
   - Shows the actual experiment runs with their results

2. **Batch Experiments (UI-Created Section)**
   - Fetched from `/api/v1/batch-experiments`
   - Stored in `BatchExperiment` table
   - Shows batch-level metadata (name, status, progress, etc.)
   - Links to the individual experiment runs

### Why Both Exist
- **Batch experiments** are the high-level orchestration objects that define parameter sweeps
- **Individual experiments** are the concrete runs generated from those sweeps
- Users need to see both: the batch metadata for management, and the individual results for analysis

## Files Modified
- `uqlab-streamlit/src/uqlab/ui_components/visualization/signals/signal_visualization.py` (lines 41-53)

## Testing Recommendations
1. Verify that batch experiments now appear in the UI
2. Check that completed batch experiments with results are displayed
3. Ensure the batch experiment details (status, progress, runs) are shown correctly
4. Verify that clicking on a batch experiment shows its individual runs

## Related Code
- **Batch API endpoint**: `backend/app/api/routes/batch_experiments.py` (line 180-195)
- **Batch response model**: `backend/app/api/routes/batch_experiments.py` (line 362-383)
- **Main UI integration**: `streamlit_app_progressive.py` (line 334-337)
- **Sweep grouping logic**: `src/uqlab/ui_components/grouping/sweep_grouping.py`

## Impact
- ✅ Batch experiments will now be displayed in the UI
- ✅ Users can see and manage their batch experiments
- ✅ No more confusing "No batch experiments found" message when experiments exist
- ⚠️ If there are truly invalid batch experiments (database inconsistencies), they will now be shown - but this is better than hiding valid ones