# Visualization Fix Plan - Matching Paper Figures 3 & 4

## Problem Statement

The user reports that:
1. **Result visualizations don't match the reference paper images** (Figures 3 & 4)
2. **Default settings might be missing sweep configurations**
3. **Both `streamlit_app.py` and `streamlit_app_progressive.py` have inaccurate visualizations**

## Reference Images Analysis

### Figure 3: Dataset Size Sweep (CIFAR-10)
**Layout**: 2 rows × 4 columns grid
- **Row 1**: Information Theoretic (Gaussian Logits) - Epistemic uncertainty (left y-axis) + Accuracy (right y-axis, green)
- **Row 2**: Information Theoretic (Gaussian Logits) - Aleatoric uncertainty (left y-axis) + Accuracy (right y-axis, green)
- **Columns**: MC-Dropout, MC-DropConnect, Flipout, Deep Ensemble
- **X-axis**: Dataset size (normalized 0-1)
- **Expected behavior**:
  - Epistemic uncertainty ↓ as dataset size ↑
  - Aleatoric uncertainty stays relatively constant
  - Accuracy ↑ as dataset size ↑

### Figure 4: Label Noise Sweep (CIFAR-10)
**Layout**: 2 rows × 4 columns grid
- **Row 1**: Information Theoretic (Gaussian Logits) - Epistemic uncertainty (left y-axis) + Accuracy (right y-axis, green)
- **Row 2**: Information Theoretic (Gaussian Logits) - Aleatoric uncertainty (left y-axis) + Accuracy (right y-axis, green)
- **Columns**: MC-Dropout, MC-DropConnect, Flipout, Deep Ensemble
- **X-axis**: Label noise (fraction 0-1)
- **Expected behavior**:
  - Epistemic uncertainty: minimal effect
  - Aleatoric uncertainty ↑ as noise ↑
  - Accuracy ↓ as noise ↑

## Current Implementation Issues

### 1. Architecture Mismatch
**Problem**: Current code uses DINOv2 (single architecture), but paper uses 4 different UQ methods:
- MC-Dropout
- MC-DropConnect  
- Flipout
- Deep Ensemble

**Current code** (`paper_sweep_viz.py:60-75`):
```python
def render_paper_style_sweep_summary(
    metrics_df: pd.DataFrame,
    *,
    architecture: str,  # ← Single architecture!
    sweep_type: str,
    ...
)
```

**What's needed**: Multi-architecture comparison grid (4 methods side-by-side)

### 2. Plot Layout Mismatch
**Problem**: Current implementation shows:
- Single architecture plots
- Different row semantics (architecture row + signal rows)
- Not the 2×4 grid from the paper

**Current approach** (`paper_sweep_viz.py:99-100`):
```python
st.caption(
    f"**{architecture}** — blue = epistemic (mutual information), orange = aleatoric "
```

**What's needed**: 
- 2 rows (epistemic, aleatoric) × 4 columns (methods)
- Dual y-axes: uncertainty (left) + accuracy (right, green)

### 3. Missing Sweep Configuration
**Problem**: Default workflow in `streamlit_app_progressive.py` has sweep enabled but might not be executing properly

**Current defaults** (`streamlit_app_progressive.py:79-86`):
```python
"uncertainty_config": {
    ...
    "sweep_enabled": True,
    "sweep_kind": "label_noise",
    "sweep_mode": "quick",
    "epistemic_sweep_enabled": False,
    "epistemic_sweep_values": DATASET_SIZE_SWEEP["quick"],  # [50, 100, 200]
    "aleatoric_sweep_enabled": True,
    "aleatoric_sweep_values": LABEL_NOISE_SWEEP["quick"],  # [0, 25, 50, 75, 100]
}
```

**Issue**: Sweep is configured but visualization might not be rendering the multi-point comparison correctly

## Root Cause Analysis

### The Code Has Two Different Visualization Systems:

1. **Hypothesis Validation** (notebooks):
   - Uses `method_comparison_plotly.py`
   - Has `create_method_uncertainty_comparison_figure()` 
   - Generates proper 3-row × 4-column grids
   - Compares MC-Dropout, MC-DropConnect, Flipout, Deep Ensemble

2. **Production/API Experiments** (Streamlit apps):
   - Uses `paper_sweep_viz.py` + `signal_diagnostic_viz.py`
   - Shows single-architecture plots
   - Designed for DINOv2 production system
   - **Does NOT match paper figures**

## Solution Plan

### Option A: Use Hypothesis Validation Plotting (Recommended)

**Pros**:
- Already implements correct paper figures
- Tested in notebooks
- Proper multi-method comparison

**Cons**:
- Requires running 4 different UQ methods (MC-Dropout, MC-DropConnect, Flipout, Deep Ensemble)
- More computationally expensive

**Implementation**:
1. Import from `uqlab.shared.notebook_utils.comparisons.method_comparison_plotly`
2. Use `create_method_uncertainty_comparison_figure()` in Streamlit
3. Run experiments with all 4 UQ methods
4. Display the 2×4 grid

### Option B: Adapt Current System for Multi-Architecture

**Pros**:
- Works with existing DINOv2 experiments
- Faster (single model architecture)

**Cons**:
- Won't match paper exactly (only 1 architecture, not 4 methods)
- Need to modify visualization code

**Implementation**:
1. Modify `paper_sweep_viz.py` to accept multiple architectures
2. Create 2×N grid (N = number of architectures)
3. Show epistemic/aleatoric rows with dual y-axes

### Option C: Hybrid Approach (Best for User)

**Show both**:
1. **Production view**: Current DINOv2 single-architecture plots (fast)
2. **Research comparison**: Paper-style 4-method grid (when available)

**Implementation**:
1. Keep current `paper_sweep_viz.py` for quick DINOv2 results
2. Add tab/section for "Research Method Comparison"
3. Use `method_comparison_plotly.py` when benchmark data exists
4. Guide user to run proper benchmarks if they want paper figures

## Immediate Fixes Needed

### Fix 1: Clarify What's Being Shown

Add clear labels in Streamlit apps:

```python
st.info("""
**Current view**: Production system (DINOv2 single architecture)

For paper-style 4-method comparison (MC-Dropout, MC-DropConnect, Flipout, Deep Ensemble),
use the **Hypothesis Validation** tab or run benchmark experiments.
""")
```

### Fix 2: Ensure Sweep is Actually Running

Check that batch experiments are:
1. Creating multiple runs with different sweep values
2. All completing successfully
3. Being aggregated correctly for visualization

### Fix 3: Add Proper Multi-Point Visualization

When sweep has ≥2 points, show:
- X-axis: sweep parameter (normalized)
- Left Y-axis: Uncertainty (epistemic/aleatoric)
- Right Y-axis: Accuracy (green line)
- Proper dual-axis scaling

## Testing Plan

### Test 1: Quick Label Noise Sweep
```python
# In streamlit_app_progressive.py, verify:
"aleatoric_sweep_values": [0, 25, 50, 75, 100]  # 5 points
```

**Expected output**:
- 5 experiments created
- All complete successfully
- Plot shows 5 points on x-axis (0.0, 0.25, 0.5, 0.75, 1.0)
- Aleatoric uncertainty increases
- Accuracy decreases

### Test 2: Quick Dataset Size Sweep
```python
"epistemic_sweep_values": [50, 100, 200]  # 3 points
```

**Expected output**:
- 3 experiments created
- Plot shows 3 points (normalized)
- Epistemic uncertainty decreases
- Accuracy increases

## Recommended Action

1. **Document current behavior**: Add warning that current plots are single-architecture production view
2. **Fix sweep execution**: Ensure batch experiments run all sweep points
3. **Add research comparison tab**: Import and use `method_comparison_plotly.py` for paper figures
4. **Update defaults**: Make sure quick sweep has good default values

## Files to Modify

1. `streamlit_app_progressive.py` - Add clarifying text
2. `ui_components/paper_sweep_viz.py` - Improve single-arch visualization
3. `ui_components/results.py` - Add research comparison option
4. New: `ui_components/hypothesis_validation_viz.py` - Bridge to notebook plotting

## Next Steps

1. User confirms which approach they prefer (A, B, or C)
2. Implement chosen solution
3. Test with actual sweep data
4. Verify plots match expectations
5. Document usage in README