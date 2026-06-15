# Method Uncertainty Comparison Plots - Implementation Guide

## Overview

Enhanced validation notebooks with 3-row method uncertainty comparison plots that show how uncertainty and accuracy evolve across validation sweeps.

## What Was Added

### Files Modified
1. `architecture_comparison_dataset_size.ipynb` - Dataset size sweep validation
2. `architecture_comparison_label_noise.ipynb` - Label noise sweep validation

### New Sections in Each Notebook

Each notebook now includes a new section: **"Method Uncertainty Comparison (Dual Y-Axes)"**

This section contains:
1. **Markdown explanation** - Describes the 3-row layout and what each row shows
2. **Import cell** - Imports from `notebook_support` (see `notebook_support/README.md`)
3. **Top signals display** - Shows which signals were selected for Row 3
4. **Plot generation** - Creates the interactive Plotly visualization
5. **Interpretation notes** - Guidance on how to interpret the results

## The 3-Row Layout

### Row 1: Gaussian Logits Methods
- Shows MC-Dropout, MC-DropConnect, Flipout, Deep Ensemble
- Compares epistemic (green), aleatoric (blue) uncertainty with accuracy (orange)

### Row 2: Information Theoretic Methods
- Same methods, different uncertainty quantification approach
- Uses information-theoretic measures for uncertainty

### Row 3: Attribution + Best Baseline Signal
- **Fixed columns:** `inverse_coherence`, `dominance`, `inverse_mass`
- **4th column:** best mean AUROC among `msp_uncertainty`, `predictive_entropy`, `mutual_info`, `inverse_logit_magnitude` (ranked with the sweep-relevant AUROC: epistemic for dataset size, aleatoric for label noise)
- Each subplot shows epistemic AUROC, aleatoric AUROC (left axis) and accuracy (right axis), aggregated across architectures

## Legend
- 🟢 **Green**: Epistemic Uncertainty (model uncertainty)
- 🔵 **Blue**: Aleatoric Uncertainty (data noise)
- 🟠 **Orange**: Classification Accuracy

## Usage

### Running the Notebooks

1. **Open Jupyter Lab/Notebook**:
   ```bash
   cd walaris-cen
   jupyter lab
   ```

2. **Navigate to validation notebooks**:
   - `notebooks/validation/architecture_comparison_dataset_size.ipynb`
   - `notebooks/validation/architecture_comparison_label_noise.ipynb`

3. **Run all cells** or run the new section specifically:
   - The new section is at the end of each notebook
   - Requires that previous cells have been run (to load `df_metrics`)

### Expected Output

Each notebook will generate:
1. A list of top 4 signals with their AUROC scores
2. An interactive Plotly figure with 3 rows × 4 columns of subplots
3. Dual Y-axes showing uncertainty (left) and accuracy (right)

### Dataset Size Sweep
- **X-axis**: Dataset size (samples per class)
- **Focus**: Epistemic uncertainty
- **Expected**: Epistemic uncertainty should decrease as dataset size increases

### Label Noise Sweep
- **X-axis**: Noise rate (%)
- **Focus**: Aleatoric uncertainty
- **Expected**: Aleatoric uncertainty should increase with noise rate

## Technical Details

### Function Signatures

```python
def plot_method_uncertainty_comparison(
    df: pd.DataFrame, 
    x_col: str, 
    sweep_type: str
) -> None:
    """
    Create 3-row comparison plot with dual Y-axes.
    
    Args:
        df: DataFrame with metrics
        x_col: X-axis column name (dataset_size or noise_rate)
        sweep_type: "dataset_size" or "label_noise"
    """
```

```python
def get_row3_signals(df: pd.DataFrame, sweep_type: str) -> list[tuple[str, float]]:
    """
    Row 3: inverse_coherence, dominance, inverse_mass, plus best-ROC baseline signal.
    """
```

### Import Path

Notebooks import from the local package (run with cwd `notebooks/validation/`):

```python
from notebook_support import plot_method_uncertainty_comparison, get_row3_signals
```

Streamlit uses the same logic via `ui_components/hypothesis_validation.py` (Plotly backend).

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError: No module named 'ui_components'`:
1. Ensure you're running from the correct directory
2. Check that `sys.path.append('../..')` is executed before imports
3. Verify the notebook is in `walaris-cen/notebooks/validation/`

### Missing Data

If plots show "No data":
1. Ensure previous cells have been run to load `df_metrics`
2. Check that the metrics CSV files exist in `results/validation/`
3. Run the validation experiments if needed (set `RUN_NEW_EXPERIMENTS = True`)

### Plotly Not Displaying

If plots don't render:
1. Ensure Plotly is installed: `pip install plotly`
2. For JupyterLab, install the extension: `jupyter labextension install jupyterlab-plotly`
3. Try restarting the kernel

## Maintenance

### Updating the Plots

To modify the plotting logic:
1. **Notebooks:** edit `notebook_support/method_comparison.py` (matplotlib)
2. **Streamlit:** edit `notebook_support/method_comparison_plotly.py` (plotly)
3. Shared signal selection: `notebook_support/signals.py`
4. Regenerate notebook skeleton: `python repair_validation_notebooks.py`

### Adding More Notebooks

To add the same plots to other validation notebooks:
1. Use the `add_method_comparison_plots.py` script as a template
2. Adjust the sweep_type, x_col, and signal_type parameters
3. Run the script to update the notebook

## References

- Original implementation: `ui_components/hypothesis_validation.py`
- Streamlit dashboard: Uses the same plotting functions
- Validation runner: `scripts/run_validation_experiments.py`

## Questions?

For issues or questions:
1. Check the function docstrings in `hypothesis_validation.py`
2. Review the Streamlit dashboard implementation
3. Consult the validation experiment documentation