# Backfill Best Signals for Existing Experiments

## Problem

Your 87 existing experiments have all 7 uncertainty signals calculated and saved in their `summary.json` files, but the database only has the aggregated `epistemic_auroc` and `aleatoric_auroc` values. This means the multi-signal visualizations show "No multi-signal data available".

## Solution

The `backfill_signals.py` script reads the `summary.json` files from your results directory and populates the `best_signals_json` column in the database.

## How It Works

1. **Finds all experiments** in the database
2. **Skips experiments** that already have `best_signals_json`
3. **Locates summary.json** using the `results_path` field
4. **Extracts signals** from `one_vs_rest_auroc` array
5. **Updates database** with the 7-signal data

## Usage

### Step 1: Run the Migration (if not done yet)

```bash
cd walaris-cen/backend
python run_migration.py
```

This adds the `best_signals_json` column to your database.

### Step 2: Run the Backfill Script

```bash
cd walaris-cen/backend
python backfill_signals.py
```

### Expected Output

```
🔄 Starting backfill of best_signals_json...
📊 Found 87 experiments in database
✅ Updated grid_20260522_185339_e50_a0 with 7 signals
✅ Updated grid_20260522_185339_e50_a20 with 7 signals
✅ Updated grid_20260522_185339_e50_a40 with 7 signals
...
============================================================
📊 Backfill Summary:
  ✅ Updated: 87
  ⏭️  Skipped (already had data): 0
  ❌ Errors: 0
  📈 Total processed: 87
============================================================

🎉 Backfill completed successfully!
💡 Refresh your Streamlit dashboard to see all 7 signals!
```

### Step 3: Refresh Dashboard

1. Refresh your Streamlit dashboard (F5 or Ctrl+R)
2. Navigate to "Batch Experiments" tab
3. Click on "🔬 All 7 Signals" tab
4. See your 3×3 heatmap grid with all signals!

## What Gets Updated

For each experiment, the script creates a JSON structure like:

```json
{
  "one_vs_rest_auroc": [
    {
      "signal": "msp_uncertainty",
      "aleatoric_like_auroc": 0.65,
      "epistemic_like_auroc": 0.72
    },
    {
      "signal": "predictive_entropy",
      "aleatoric_like_auroc": 0.68,
      "epistemic_like_auroc": 0.75
    },
    {
      "signal": "mutual_info",
      "aleatoric_like_auroc": 0.62,
      "epistemic_like_auroc": 0.70
    },
    {
      "signal": "inverse_coherence",
      "aleatoric_like_auroc": 0.73,
      "epistemic_like_auroc": 0.65
    },
    {
      "signal": "dominance",
      "aleatoric_like_auroc": 0.60,
      "epistemic_like_auroc": 0.76
    },
    {
      "signal": "inverse_mass",
      "aleatoric_like_auroc": 0.70,
      "epistemic_like_auroc": 0.94
    },
    {
      "signal": "inverse_logit_magnitude",
      "aleatoric_like_auroc": 0.68,
      "epistemic_like_auroc": 0.88
    }
  ]
}
```

## Troubleshooting

### "No summary.json found"

**Problem**: The experiment's `results_path` doesn't point to a valid directory with `summary.json`.

**Solution**: Check that your results are in the expected location. The script looks for:
```
{results_path}/summary.json
```

### "No one_vs_rest_auroc data"

**Problem**: The `summary.json` file doesn't have the expected structure.

**Solution**: This might be an old experiment format. Check the JSON structure manually.

### "Experiment has no results_path"

**Problem**: The experiment in the database doesn't have a `results_path` set.

**Solution**: These experiments can't be backfilled automatically. They might be incomplete or failed experiments.

## Safety

- ✅ **Non-destructive**: Only updates experiments that don't have `best_signals_json`
- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Read-only on files**: Only reads `summary.json`, doesn't modify them
- ✅ **Transactional**: All updates committed together

## Verification

After running the backfill, verify in your database:

```sql
SELECT 
    name,
    CASE 
        WHEN best_signals_json IS NULL THEN 'Missing'
        ELSE 'Present'
    END as signal_data_status
FROM uncertaintyexperiment
WHERE status = 'COMPLETED'
LIMIT 10;
```

All completed experiments should show "Present".

## Next Steps

After backfilling:

1. **View 3×3 Heatmaps**: See all 7 signals in 2D grid
2. **Use 1D Filters**: Select which signals to compare
3. **Compare Performance**: Identify best signals for your use case
4. **Export Data**: Download signal data for analysis

---

**Made with Bob** 🤖