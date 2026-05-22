# Batch Experiment Per-Signal AUROC Visualization

## Overview

This document describes the enhancement to batch experiment visualizations to display AUROC metrics for each individual attribution signal, rather than just aggregated epistemic and aleatoric AUROC values.

## Changes Made

### 1. Frontend (Streamlit UI) - `ui_components.py`

**Modified Function:** `render_batch_results()`

**Changes:**
- Added tabbed visualization with three views:
  - **"All Signals"**: Shows all AUROC signals in a single chart
  - **"By Category"**: Organizes signals into categories (Predictive, Attribution-Based, Logit-Based, Aggregated) with separate charts
  - **"Aggregated Only"**: Shows only the original epistemic/aleatoric aggregated metrics (backward compatible view)

**Signal Categories:**
- **Predictive Uncertainty**: `msp_uncertainty`, `predictive_entropy`, `mutual_info`
- **Attribution-Based (DualXDA)**: `inverse_coherence`, `dominance`
- **Logit-Based (Representer)**: `inverse_mass`, `inverse_logit_magnitude`
- **Aggregated**: `epistemic_auroc`, `aleatoric_auroc`

### 2. Backend (FastAPI Service) - `batch_experiment_service.py`

**Modified Function:** `_build_series()`

**Changes:**
- Extracts per-signal AUROC data from `result_summary_json` field in each batch run
- Parses the `one_vs_rest_auroc` array from experiment results
- Creates separate series for each signal's aleatoric and epistemic AUROC
- Maintains backward compatibility by keeping aggregated metrics

**Data Structure:**
Each experiment's `result_summary_json` contains:
```json
{
  "one_vs_rest_auroc": [
    {
      "signal": "msp_uncertainty",
      "aleatoric_like_auroc": 0.85,
      "epistemic_like_auroc": 0.72
    },
    {
      "signal": "inverse_coherence",
      "aleatoric_like_auroc": 0.73,
      "epistemic_like_auroc": 0.68
    },
    ...
  ]
}
```

**Series Output:**
The backend now returns series in this format:
```json
{
  "series": [
    {
      "metric": "epistemic_auroc",
      "display_name": "Epistemic AUROC (Aggregated)",
      "points": [{"x": 50, "y": 0.85, "run_index": 0, "status": "completed"}]
    },
    {
      "metric": "msp_uncertainty_aleatoric",
      "display_name": "msp_uncertainty (Aleatoric)",
      "points": [{"x": 50, "y": 0.82, "run_index": 0, "status": "completed"}]
    },
    {
      "metric": "msp_uncertainty_epistemic",
      "display_name": "msp_uncertainty (Epistemic)",
      "points": [{"x": 50, "y": 0.75, "run_index": 0, "status": "completed"}]
    },
    ...
  ]
}
```

## Benefits

1. **Granular Analysis**: Users can now see how each individual uncertainty signal performs across parameter sweeps
2. **Signal Comparison**: Easy comparison between different attribution methods (DualXDA vs logit-based vs predictive)
3. **Better Insights**: Identify which specific signals are most sensitive to parameter changes
4. **Organized Views**: Categorized visualization helps understand signal families
5. **Backward Compatible**: Aggregated view still available for high-level analysis

## Usage

### Running Batch Experiments

No changes needed to how batch experiments are created or run. The per-signal data is automatically captured from experiment results.

### Viewing Results

1. Navigate to the "Batch Experiments" tab in Streamlit
2. Select a completed batch experiment
3. Use the three tabs to explore results:
   - **All Signals**: See everything at once (can be crowded with many signals)
   - **By Category**: Best for comparing signals within their category
   - **Aggregated Only**: Quick overview using traditional metrics

### Interpreting Results

- **Aleatoric AUROC**: How well the signal detects noisy/ambiguous labels
- **Epistemic AUROC**: How well the signal detects under-supported classes
- Higher AUROC = better detection capability for that uncertainty type
- Compare signals within categories to find the best performer

## Example Insights

From a typical batch experiment sweeping `under_train_per_class`:

- **inverse_mass** (logit-based) typically shows highest epistemic AUROC (~0.94)
- **inverse_coherence** (attribution-based) excels at aleatoric detection (~0.73)
- **predictive_entropy** provides balanced performance across both types
- Performance trends reveal optimal training data sizes for each signal type

## Technical Notes

- NaN values are filtered out (occur when a class is empty in evaluation)
- Series are sorted by swept parameter value for proper line plotting
- Signal names are extracted dynamically from experiment results
- Empty series are not displayed (e.g., if a signal wasn't computed)

## Future Enhancements

Potential improvements:
- Add statistical significance indicators
- Include confidence intervals for AUROC estimates
- Export per-signal data to CSV
- Add signal ranking/leaderboard view
- Interactive signal selection/filtering