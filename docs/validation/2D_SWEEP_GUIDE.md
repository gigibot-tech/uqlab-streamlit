# 2D Grid Sweep Feature Guide

## Overview

The 2D Grid Sweep feature enables comprehensive parameter exploration by sweeping **epistemic** and **aleatoric** uncertainty simultaneously, creating a grid of experiments similar to the `watsonx_deployment_experiment.ipynb` notebook.

## Features

### 1. **2D Parameter Sweep Configuration**
- **Epistemic Dimension**: `under_train_per_class` (samples per under-supported class)
- **Aleatoric Dimension**: `aleatoric_noise_percentage` (label noise percentage)
- **Preset Options**:
  - Quick (3×3 = 9 experiments)
  - Standard (5×5 = 25 experiments)
  - Comprehensive (7×6 = 42 experiments)
  - Custom (user-defined values)

### 2. **Interactive Heatmap Visualization**
- **Plotly-based** interactive heatmaps
- **Per-signal AUROC** visualization
- **Epistemic vs Aleatoric** detection comparison
- **Color-coded** performance (Red-Yellow-Green scale)
- **Hover details** for each grid cell

### 3. **Comprehensive Analysis**
- Summary statistics (mean, max, min AUROC)
- Signal comparison across the grid
- Experiment status tracking
- Export-ready results

## Usage

### Step 1: Access the 2D Sweep Tab

In the Streamlit app, navigate to:
```
🧪 Experiments → Batch Experiments (2D Grid)
```

### Step 2: Configure the Grid

1. **Choose Epistemic Preset**:
   - Quick: `[1, 101, 301]` samples/class
   - Standard: `[1, 51, 101, 201, 301]` samples/class
   - Comprehensive: `[1, 51, 101, 151, 201, 251, 301]` samples/class
   - Custom: Enter your own values

2. **Choose Aleatoric Preset**:
   - Quick: `[0, 25, 50]%` noise
   - Standard: `[0, 20, 40, 60, 80]%` noise
   - Comprehensive: `[0, 20, 40, 60, 80, 100]%` noise
   - Custom: Enter your own values

3. **Configure Base Parameters**:
   - Model: DINOv2 size, hidden dim, dropout
   - Training: epochs, learning rate, batch size
   - Evaluation: samples per group, MC passes

### Step 3: Create the Grid

Click **"🚀 Create 2D Grid Sweep"** to generate all experiments.

Example: 7 epistemic × 6 aleatoric = **42 experiments**

### Step 4: Analyze Results

Once experiments complete, use the visualization panel to:

1. **Select Signal**: Choose from 7 uncertainty signals
   - `msp_uncertainty`
   - `predictive_entropy`
   - `mutual_info`
   - `inverse_coherence`
   - `dominance`
   - `inverse_mass`
   - `inverse_logit_magnitude`

2. **Select Detection Type**:
   - Epistemic Detection (how well it finds under-supported classes)
   - Aleatoric Detection (how well it finds noisy labels)

3. **View Heatmap**: Interactive visualization showing AUROC across the grid

## Example Workflow

### Quick Pilot (9 experiments, ~30 minutes)

```yaml
Epistemic: [1, 101, 301]
Aleatoric: [0, 25, 50]
Grid: 3 × 3 = 9 experiments

Expected insights:
- How epistemic uncertainty changes with training data
- How aleatoric uncertainty changes with noise level
- Signal performance across different conditions
```

### Comprehensive Study (42 experiments, ~2-4 hours)

```yaml
Epistemic: [1, 51, 101, 151, 201, 251, 301]
Aleatoric: [0, 20, 40, 60, 80, 100]
Grid: 7 × 6 = 42 experiments

Expected insights:
- Full epistemic-aleatoric interaction map
- Optimal operating points for each signal
- Signal robustness across conditions
- Publication-ready heatmaps
```

## Comparison with Notebook

### Similarities
- Same grid structure (epistemic × aleatoric)
- Same 7 uncertainty signals
- Same AUROC evaluation metrics
- Same heatmap visualization style

### Advantages of Streamlit Version
- **Interactive**: Real-time parameter adjustment
- **Incremental**: View results as they complete
- **Persistent**: Results stored in database
- **Shareable**: Web-based, no notebook required
- **Scalable**: Backend handles execution

### Advantages of Notebook Version
- **Batch Processing**: All experiments in one run
- **Reproducible**: Single script with all parameters
- **Exportable**: Direct watsonx.ai package generation
- **Documented**: Markdown cells explain each step

## Technical Details

### Implementation

**Frontend** (`ui_components/batch_2d_sweep.py`):
- `render_2d_sweep_config()`: Grid configuration UI
- `render_2d_heatmap()`: Plotly heatmap generation
- `render_2d_results_analysis()`: Comprehensive analysis panel

**Backend** (uses existing experiment API):
- Creates individual experiments for each grid point
- Stores epistemic/aleatoric values in experiment config
- Aggregates results for visualization

### Data Flow

```
User Input → Grid Configuration → N×M Experiments
    ↓
Individual Experiments → FastAPI Backend → ML Script
    ↓
Results → Database → Streamlit Visualization
    ↓
Interactive Heatmap → Signal Analysis → Export
```

## Best Practices

### 1. Start Small
Begin with Quick preset (9 experiments) to validate configuration before running comprehensive sweeps.

### 2. Monitor Progress
Check experiment status regularly. Failed experiments can be re-run individually.

### 3. Save Results
Export heatmaps and summary statistics for documentation and publication.

### 4. Compare Signals
Use the signal selector to compare all 7 signals across the same grid.

### 5. Iterate
Based on initial results, refine your grid ranges for focused exploration.

## Troubleshooting

### Issue: Experiments not starting
**Solution**: Check backend logs, ensure sufficient resources

### Issue: Heatmap shows NaN values
**Solution**: Wait for experiments to complete, check for failed runs

### Issue: Grid too large
**Solution**: Use Custom preset with fewer values, or run in batches

## Future Enhancements

- [ ] Multi-signal heatmap comparison (subplot grid)
- [ ] Export to watsonx.ai packages directly from UI
- [ ] Automatic optimal point detection
- [ ] Statistical significance testing
- [ ] 3D visualization (epistemic × aleatoric × signal)

## Related Documentation

- `ARCHITECTURE_SIMPLE.md`: Core experiment flow
- `IMPROVEMENTS_GUIDE.md`: Code quality features
- `watsonx_deployment_experiment.ipynb`: Original notebook implementation
- `AUROC_METRICS_EXPLAINED.md`: Understanding AUROC metrics

---

**Created**: 2026-05-22  
**Version**: 1.0  
**Status**: Production Ready