# Pool-Filtered Sweep Plot: Complete Data Flow

> **Superseded:** [`docs/UQLAB_FLOW.md`](docs/UQLAB_FLOW.md)

## Overview

This document explains **exactly** how the three-line sweep plot gets its data, from experiment execution through to visualization. The key concept is **pool filtering**: computing separate uncertainty means for different evaluation groups (epistemic/aleatoric/clean).

## The Three Lines

1. **Primary pool uncertainty** (solid line) - Mean uncertainty for the swept dimension's pool
2. **Mirror pool uncertainty** (dashed line, optional) - Mean uncertainty for the contrast pool
3. **Model accuracy** (dotted line) - Classification performance

## Complete Data Flow

### Step 1: Experiment Execution

**File**: [`scripts/runners/run_fast_uncertainty_classification.py`](scripts/runners/run_fast_uncertainty_classification.py:534)

```python
# Line 534: Compute uncertainty signals for all eval samples
eval_outputs = compute_eval_signals(
    model=model,
    train_dataset=train_dataset,
    eval_inputs=eval_inputs,  # N evaluation samples
    device=device,
    config=eval_signal_config,
)

# Extract the signal table (per-sample uncertainties)
signal_table = eval_outputs["signal_table"]
# signal_table = {
#     "mutual_info": tensor([0.15, 0.23, 0.08, ...]),  # N values
#     "predictive_entropy": tensor([0.45, 0.67, ...]),
#     "expected_entropy": tensor([0.30, 0.44, ...]),
#     ...
# }
```

### Step 2: Signal Computation (`collect_uncertainty_signals`)

**File**: [`src/uqlab/evaluation/classification/pipeline/fast_pilot_eval.py`](src/uqlab/evaluation/classification/pipeline/fast_pilot_eval.py:39-150)

This function computes **per-sample** uncertainty values using three methods:

#### 2a. MC Dropout (lines 132-142)
```python
# Run model 20 times with dropout enabled
# For each sample, compute uncertainty from prediction variance
if "mc_dropout" in needed:
    # Runs MC dropout and computes:
    # - predictive_entropy: H[p(y|x)] - total uncertainty
    # - mutual_info: I[y;θ|x] - epistemic uncertainty  
    # - expected_entropy: E[H[p(y|x,θ)]] - aleatoric uncertainty
    
    store["mc.entropy"] = ...  # Per-sample values
    store["mc.mutual_info"] = ...  # Per-sample values
```

#### 2b. Attribution Signals (lines 100-109)
```python
# Compute gradient-based attribution for each sample
if "attribution" in needed:
    store["attribution.coherence"] = ...  # How focused is the model?
    store["attribution.mass"] = ...  # How much evidence?
    store["attribution.dominance"] = ...  # How dominant is top class?
```

#### 2c. Build Signal Table (line 144)
```python
# Combine all sources into one table
signal_table = build_signal_table_from_store(
    store,
    enabled=enabled_signals,
    mc_passes=config.mc_passes,
    dropout=config.dropout,
)

# Returns: dict[signal_name → tensor[N_samples]]
# Example:
# {
#   "mutual_info": tensor([0.15, 0.23, 0.08, 0.12, ...]),  # 1000 samples
#   "predictive_entropy": tensor([0.45, 0.67, 0.32, ...]),
#   "attribution_coherence": tensor([0.82, 0.91, 0.76, ...]),
#   ...
# }
```

**Key Point**: At this stage, we have **one uncertainty value per sample** for each signal. No pooling yet!

### Step 3: Save to `results.pt`

**File**: [`scripts/runners/run_fast_uncertainty_classification.py`](scripts/runners/run_fast_uncertainty_classification.py:700+)

```python
# Save all evaluation data to disk
torch.save({
    "signal_table": signal_table,  # ← Per-sample uncertainties
    "eval_group_labels": eval_group_labels,  # ← Pool assignments [0,1,2,...]
    "predictions": mean_pred_det,
    "eval_clean_labels": eval_clean_labels,
    ...
}, results_dir / "results.pt")
```

**What's in `eval_group_labels`?**
```python
# Each sample is assigned to one of three pools:
eval_group_labels = [
    GROUP_EPISTEMIC,   # 2 - Under-supported class sample
    GROUP_EPISTEMIC,   # 2
    GROUP_ALEATORIC,   # 1 - Noisy label sample
    GROUP_CLEAN,       # 0 - Clean sample
    GROUP_EPISTEMIC,   # 2
    GROUP_ALEATORIC,   # 1
    ...  # 1000 total samples
]

# Constants defined in run_artifacts.py:
GROUP_CLEAN = 0
GROUP_ALEATORIC = 1  
GROUP_EPISTEMIC = 2
```

### Step 4: Pool Filtering (`_signal_means_from_results_pt`)

**File**: [`src/uqlab/run_artifacts.py`](src/uqlab/run_artifacts.py:405-458)

**This is where the magic happens!** This function loads `results.pt` and computes **pool-filtered means**.

```python
def _signal_means_from_results_pt(results_pt: Path) -> dict[str, float]:
    """
    Extract per-signal means, FILTERED BY EVALUATION POOL.
    
    This creates the separate lines in the sweep plot:
    - signal_mean_epistemic → for epistemic pool samples only
    - signal_mean_aleatoric → for aleatoric pool samples only
    - signal_mean_clean → for clean samples only
    """
    # Load the saved data
    data = torch.load(results_pt, map_location="cpu", weights_only=False)
    signal_table = data["signal_table"]  # Per-sample uncertainties
    group_labels = data.get("eval_group_labels")  # Pool assignments
    
    metrics = {}
    
    # For each uncertainty signal...
    for name, values in signal_table.items():
        # values = tensor([0.15, 0.23, 0.08, 0.12, 0.19, 0.07, ...])
        # group_labels = [2, 2, 1, 0, 2, 1, ...]
        
        # Compute OVERALL mean (all samples)
        metrics[f"{name}_mean"] = float(np.nanmean(values))
        
        # ========== POOL FILTERING HAPPENS HERE ==========
        
        # Filter to ONLY epistemic pool samples
        epistemic_mask = (group_labels == GROUP_EPISTEMIC)  # [True, True, False, False, True, False, ...]
        if epistemic_mask.any():
            epistemic_values = values[epistemic_mask]  # [0.15, 0.23, 0.19, ...]
            metrics[f"{name}_mean_epistemic"] = float(np.nanmean(epistemic_values))
        
        # Filter to ONLY aleatoric pool samples
        aleatoric_mask = (group_labels == GROUP_ALEATORIC)  # [False, False, True, False, False, True, ...]
        if aleatoric_mask.any():
            aleatoric_values = values[aleatoric_mask]  # [0.08, 0.07, ...]
            metrics[f"{name}_mean_aleatoric"] = float(np.nanmean(aleatoric_values))
        
        # Filter to ONLY clean samples
        clean_mask = (group_labels == GROUP_CLEAN)  # [False, False, False, True, False, False, ...]
        if clean_mask.any():
            clean_values = values[clean_mask]  # [0.12, ...]
            metrics[f"{name}_mean_clean"] = float(np.nanmean(clean_values))
    
    return metrics
    # Returns:
    # {
    #   "mutual_info_mean": 0.18,
    #   "mutual_info_mean_epistemic": 0.25,  # ← Mean of epistemic samples only
    #   "mutual_info_mean_aleatoric": 0.075, # ← Mean of aleatoric samples only
    #   "mutual_info_mean_clean": 0.12,      # ← Mean of clean samples only
    #   "predictive_entropy_mean": 0.52,
    #   "predictive_entropy_mean_epistemic": 0.68,
    #   "predictive_entropy_mean_aleatoric": 0.42,
    #   ...
    # }
```

**Example with Real Numbers**:
```python
# Input (per-sample):
signal_table["mutual_info"] = [0.15, 0.23, 0.08, 0.12, 0.19, 0.07, 0.21, 0.09]
eval_group_labels =           [  2,    2,    1,    0,    2,    1,    2,    1  ]
#                              epis  epis  alea clean epis  alea  epis  alea

# Output (pool-filtered means):
metrics = {
    "mutual_info_mean": 0.143,  # mean([0.15, 0.23, 0.08, 0.12, 0.19, 0.07, 0.21, 0.09])
    "mutual_info_mean_epistemic": 0.195,  # mean([0.15, 0.23, 0.19, 0.21]) ← FILTERED!
    "mutual_info_mean_aleatoric": 0.08,   # mean([0.08, 0.07, 0.09]) ← FILTERED!
    "mutual_info_mean_clean": 0.12,       # mean([0.12]) ← FILTERED!
}
```

### Step 5: Aggregate Across Sweep

**File**: [`src/uqlab/evaluation/classification/pipeline/sweep_line_plot.py`](src/uqlab/evaluation/classification/pipeline/sweep_line_plot.py:291-304)

```python
def build_sweep_metrics_frame(run_ids, experiments_dir):
    """
    Call metrics_row_from_run() for EACH completed experiment.
    Build DataFrame with ONE ROW PER SWEEP POINT.
    """
    rows = []
    for run_id in run_ids:
        results_dir = experiments_dir / run_id / "results"
        # This calls _signal_means_from_results_pt() internally
        row = _enrich_metrics_row(results_dir)
        rows.append(row)
    
    return pd.DataFrame(rows)
    # Returns DataFrame like:
    # noise% | mutual_info_mean_aleatoric | mutual_info_mean_epistemic | accuracy
    # -------|----------------------------|----------------------------|----------
    #   0    |          0.08              |          0.25              |   0.92
    #  20    |          0.25              |          0.27              |   0.85
    #  40    |          0.45              |          0.29              |   0.75
    #  60    |          0.68              |          0.31              |   0.62
    #  80    |          0.85              |          0.33              |   0.48
    # 100    |          0.95              |          0.35              |   0.35
```

### Step 6: Determine Which Traces to Plot

**File**: [`src/uqlab/evaluation/classification/pipeline/sweep_plot_pools.py`](src/uqlab/evaluation/classification/pipeline/sweep_plot_pools.py:109-150)

```python
def resolve_sweep_plot_traces(signal, sweep_kind, plot_df):
    """
    Determine which pool-filtered columns to plot based on:
    1. Sweep type (label_noise → aleatoric primary, dataset_size → epistemic primary)
    2. Data availability (only plot if column exists with values)
    """
    # Determine primary pool based on sweep type
    primary = primary_pool_for_sweep(sweep_kind)
    # label_noise → "aleatoric" (noise affects data ambiguity)
    # dataset_size → "epistemic" (scarcity affects model confidence)
    
    secondary = secondary_pool_for_sweep(sweep_kind)
    # The opposite pool (for mirror line)
    
    traces = []
    
    # Try to add PRIMARY line (solid)
    primary_col = f"{signal}_mean_{primary}"  # e.g., "mutual_info_mean_aleatoric"
    if pool_has_values(plot_df, primary_col):  # ← Check if column exists with data
        traces.append(SweepPlotTraceSpec(
            column=primary_col,
            dash="solid",  # Solid line for primary
            color=ALEATORIC_COLOR if primary == "aleatoric" else EPISTEMIC_COLOR,
            primary=True
        ))
    
    # Try to add MIRROR line (dashed, optional)
    secondary_col = f"{signal}_mean_{secondary}"  # e.g., "mutual_info_mean_epistemic"
    if pool_has_values(plot_df, secondary_col):  # ← Check if column exists with data
        traces.append(SweepPlotTraceSpec(
            column=secondary_col,
            dash="dash",  # Dashed line for mirror
            color=EPISTEMIC_COLOR if secondary == "epistemic" else ALEATORIC_COLOR,
            primary=False
        ))
    
    return traces
```

**Why Mirror Line Might Be Missing**:
```python
# Your epistemic sweep (0% noise):
# - aleatoric_noise_percentage = 0
# - No aleatoric eval pool created (no noisy samples)
# - results.pt has NO "mutual_info_mean_aleatoric" column
# - pool_has_values() returns False
# - Mirror line is NOT added
# - Result: Only 2 lines (epistemic + accuracy)
```

### Step 7: Build Plot Traces

**File**: [`src/uqlab/evaluation/classification/pipeline/sweep_line_plot.py`](src/uqlab/evaluation/classification/pipeline/sweep_line_plot.py:663-677)

```python
# Sort DataFrame by X-axis (creates smooth curve when points connected)
plot_df = df[cols].copy()
plot_df = plot_df.dropna(subset=[x_col]).sort_values(x_col)

# Extract X and Y values
x_vals = [float(v) for v in plot_df[x_col].tolist()]
# x_vals = [0, 20, 40, 60, 80, 100]  # Noise percentages

# Build uncertainty traces (primary + optional mirror)
traces = _build_uncertainty_traces(plot_df, x_vals, trace_specs)
# For each trace spec:
#   y_vals = plot_df[spec.column].tolist()
#   # e.g., plot_df["mutual_info_mean_aleatoric"] = [0.08, 0.25, 0.45, 0.68, 0.85, 0.95]
#   traces.append({
#       "name": "Aleatoric (primary)",
#       "x": [0, 20, 40, 60, 80, 100],
#       "y": [0.08, 0.25, 0.45, 0.68, 0.85, 0.95],  # ← Pool-filtered means!
#       "yaxis": "left",
#       "dash": "solid"
#   })

# Add accuracy trace (right Y-axis)
if "accuracy" in plot_df.columns:
    traces.append(_build_accuracy_trace(plot_df, x_vals))
    # {
    #   "name": "Accuracy",
    #   "x": [0, 20, 40, 60, 80, 100],
    #   "y": [0.92, 0.85, 0.75, 0.62, 0.48, 0.35],
    #   "yaxis": "right",
    #   "dash": "dot"
    # }
```

### Step 8: Render Plot

Plotly/matplotlib connects the points → smooth curves!

## Key Takeaways

1. **Per-Sample Computation**: `collect_uncertainty_signals()` computes one uncertainty value per evaluation sample
2. **Pool Filtering**: `_signal_means_from_results_pt()` filters samples by pool (epistemic/aleatoric/clean) and computes separate means
3. **Data-Driven Traces**: Traces are only added if the corresponding pool-filtered column exists in the data
4. **Sorting Creates Curves**: Sorting the DataFrame by X-axis value creates smooth curves when points are connected

## Why Your Epistemic Sweep Has No Dashed Line

```
Your Configuration:
  aleatoric_noise_percentage: 0
  under_supported_classes: [0, 1]

Result:
  ✓ Epistemic pool exists (under-supported classes)
  ✗ Aleatoric pool does NOT exist (no noise)
  
Data in results.pt:
  ✓ mutual_info_mean_epistemic: 0.25
  ✗ mutual_info_mean_aleatoric: MISSING
  
Plot:
  ✓ Solid epistemic line (primary)
  ✗ Dashed aleatoric line (mirror) - MISSING
  ✓ Dotted accuracy line
```

To get the dashed mirror line, run a label noise sweep with `aleatoric_noise_percentage > 0`.

## File References

- **Signal Computation**: [`fast_pilot_eval.py:39`](src/uqlab/evaluation/classification/pipeline/fast_pilot_eval.py:39)
- **Pool Filtering**: [`run_artifacts.py:405`](src/uqlab/run_artifacts.py:405)
- **Sweep Aggregation**: [`sweep_line_plot.py:291`](src/uqlab/evaluation/classification/pipeline/sweep_line_plot.py:291)
- **Trace Selection**: [`sweep_plot_pools.py:109`](src/uqlab/evaluation/classification/pipeline/sweep_plot_pools.py:109)
- **Plot Building**: [`sweep_line_plot.py:623`](src/uqlab/evaluation/classification/pipeline/sweep_line_plot.py:623)

---

**Last Updated**: 2026-06-21  
**Purpose**: Complete explanation of pool-filtered sweep plot data flow