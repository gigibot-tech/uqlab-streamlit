# Why Am I Only Seeing 2 Signals in Batch Experiments?

## TL;DR

**Your existing batch experiments don't have per-signal AUROC data.** You need to run NEW batch experiments to see the per-signal visualization.

## The Problem

The batch experiment visualization is showing only 2 signals (epistemic_auroc and aleatoric_auroc) because:

1. **Old experiments don't have the data**: Experiments that were run BEFORE the per-signal tracking was added don't have `result_summary_json` populated with per-signal AUROC values
2. **Data is captured at runtime**: The per-signal AUROC data is only saved when experiments actually run
3. **Database doesn't retroactively populate**: We can't add this data to old experiments without re-running them

## The Solution

### Option 1: Run a NEW Batch Experiment (Recommended)

1. Go to the "Batch Experiments" tab in Streamlit
2. Create a new batch experiment with your desired parameter sweep
3. Start the batch execution
4. Wait for it to complete
5. The new results will include per-signal AUROC data
6. You'll see all signals in the visualization

### Option 2: Check if Backend Needs Restart

If you just ran a batch experiment and still see only 2 signals:

1. **Restart the FastAPI backend server**
   ```bash
   # Stop the backend (Ctrl+C if running in terminal)
   # Then restart it
   cd walaris-cen/backend
   uvicorn app.main:app --reload
   ```

2. **Refresh the Streamlit page** (F5 or Ctrl+R)

3. Check the "Debug Info" expander - it should now show more than 2 series

## How to Verify What Data You Have

Run this diagnostic script:

```bash
cd walaris-cen
python check_batch_data.py
```

This will show you:
- Which batch runs exist
- Whether they have per-signal data
- What signals are available

## What Changed

### Before (Old Experiments)
```json
{
  "aleatoric_auroc": 0.73,
  "epistemic_auroc": 0.85
}
```
Only 2 aggregated values stored in database.

### After (New Experiments)
```json
{
  "aleatoric_auroc": 0.73,
  "epistemic_auroc": 0.85,
  "one_vs_rest_auroc": [
    {
      "signal": "msp_uncertainty",
      "aleatoric_like_auroc": 0.82,
      "epistemic_like_auroc": 0.75
    },
    {
      "signal": "inverse_coherence",
      "aleatoric_like_auroc": 0.73,
      "epistemic_like_auroc": 0.68
    },
    {
      "signal": "dominance",
      "aleatoric_like_auroc": 0.65,
      "epistemic_like_auroc": 0.76
    },
    {
      "signal": "inverse_mass",
      "aleatoric_like_auroc": 0.71,
      "epistemic_like_auroc": 0.94
    },
    ...
  ]
}
```
Full per-signal data captured in `result_summary_json`.

## Expected Signals

When you run a new batch experiment, you should see these signals:

### Predictive Uncertainty (3 signals)
- `msp_uncertainty` (Aleatoric + Epistemic)
- `predictive_entropy` (Aleatoric + Epistemic)
- `mutual_info` (Aleatoric + Epistemic)

### Attribution-Based DualXDA (2 signals)
- `inverse_coherence` (Aleatoric + Epistemic)
- `dominance` (Aleatoric + Epistemic)

### Logit-Based Representer (2 signals)
- `inverse_mass` (Aleatoric + Epistemic)
- `inverse_logit_magnitude` (Aleatoric + Epistemic)

### Aggregated (2 signals)
- `epistemic_auroc` (Aggregated)
- `aleatoric_auroc` (Aggregated)

**Total: 16 series** (7 signals × 2 types + 2 aggregated)

## Troubleshooting

### "I ran a new batch but still see only 2 signals"

1. Check if experiments actually completed successfully
2. Restart the backend server
3. Clear browser cache and refresh Streamlit
4. Check the Debug Info expander for series count

### "The Debug Info shows 2 series"

This confirms the backend is returning only aggregated data. Either:
- Backend hasn't been restarted after code changes
- Experiments don't have per-signal data (old experiments)

### "I see more than 2 in Debug Info but charts are empty"

This is a frontend rendering issue:
- Check browser console for JavaScript errors
- Try a different browser
- Check if Plotly is loading correctly

## Quick Test

To quickly test if everything works:

1. Create a small batch experiment (e.g., sweep `under_train_per_class` from 50 to 100 in steps of 50)
2. This creates only 2 runs, completes quickly
3. Check if you see 16 series in the visualization
4. If yes, everything is working!
5. If no, follow troubleshooting steps above

## Need Help?

If you're still stuck:
1. Run `python check_batch_data.py` and share the output
2. Check the backend logs for errors
3. Look at the Debug Info expander in Streamlit
4. Verify the batch experiment status is "completed"