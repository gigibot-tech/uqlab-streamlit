# UI Plot Inventory - Complete Visualization Catalog

**Generated:** 2026-06-18  
**Purpose:** Comprehensive inventory of all plotting functions in the UQ Lab Streamlit UI

---

## 📊 TOTAL COUNT: 11 Plot Functions

### Summary by Category
- **UQ Benchmarks (Analysis):** 4 functions
- **Signal Diagnostics:** 3 functions  
- **Sweep Visualizations:** 4 functions

---

## 1️⃣ UQ BENCHMARKS - Analysis Plots

**File:** `src/uqlab/ui_components/visualization/analysis/uq_benchmarks.py`

### 1.1 `plot_accuracy_comparison()` - Line 85
**Type:** Matplotlib line plot  
**Purpose:** Row 1 - Compare accuracy across all UQ methods  
**Renders:** 1 subplot showing accuracy vs label noise for:
- Gaussian Logits (blue)
- Information Theoretic (orange)
- Production signals (green, optional)

**Data Required:**
- `gaussian_data`: Dict with `parameter_values`, `accuracy`
- `it_data`: Dict with `parameter_values`, `accuracy`
- `prod_data`: Optional Dict with `parameter_values`, `accuracy`

**Usage:** Called by `render_benchmark_comparison_plots()`

---

### 1.2 `plot_uncertainty_with_accuracy()` - Line 112
**Type:** Matplotlib dual-axis plot  
**Purpose:** Row 2 (Gaussian) or Row 3 (IT) - Show uncertainty decomposition + accuracy  
**Renders:** 1 subplot with:
- Left Y-axis: Epistemic (green) and Aleatoric (blue) uncertainty
- Right Y-axis: Accuracy (red dashed)

**Data Required:**
- `data`: Dict with `parameter_values`, `epistemic_auroc`, `aleatoric_auroc`, `accuracy`
- `method_name`: String ("Gaussian Logits" or "Information Theoretic")

**Usage:** Called twice by `render_benchmark_comparison_plots()` for Rows 2 & 3

---

### 1.3 `plot_signal_with_accuracy()` - Line 160
**Type:** Matplotlib dual-axis plot  
**Purpose:** Row 4 - Individual production signal plots (7 subplots)  
**Renders:** 1 subplot per signal showing:
- Left Y-axis: Signal AUROC (purple)
- Right Y-axis: Accuracy (red dashed)

**Data Required:**
- `data`: Dict with `parameter_values`, `{signal_name}_auroc`, `accuracy`
- `signal_name`: One of 7 production signals (from `SIGNAL_NAMES`)

**Current Status:** ⚠️ **NOT RENDERING** - `prod_data = None` (line 415-419)  
**Reason:** Production signal extraction not implemented yet

**Usage:** Would be called 7 times by `render_benchmark_comparison_plots()` for Row 4

---

### 1.4 `render_benchmark_comparison_plots()` - Line 315
**Type:** Orchestrator function (calls other plot functions)  
**Purpose:** Main entry point - renders complete 4-row comparison figure  
**Renders:** 
- **Row 1:** 1 subplot (accuracy comparison)
- **Row 2:** 1 subplot (Gaussian uncertainty decomposition)
- **Row 3:** 1 subplot (IT uncertainty decomposition)
- **Row 4:** 7 subplots (production signals) - **CURRENTLY DISABLED**

**Total Subplots:** 3 active (10 when Row 4 implemented)

**Data Flow:**
1. Fetches sweep data from API
2. Extracts metrics for each method
3. Calls plotting functions to create figure
4. Displays with `st.pyplot()`

**Usage:** Called from Streamlit UI "UQ Benchmarks" tab

---

## 2️⃣ SIGNAL DIAGNOSTICS - Per-Signal Analysis

**File:** `src/uqlab/ui_components/visualization/signals/signal_diagnostic_viz.py`

### 2.1 `_plot_arch_metrics_sweep()` - Line 294
**Type:** Plotly line plot (internal helper)  
**Purpose:** Create mini sweep plot for one architecture  
**Renders:** 1 subplot with 3 traces:
- Epistemic AUROC (green)
- Aleatoric AUROC (blue)
- Accuracy (red, optional)

**Data Required:**
- `metrics_df`: DataFrame with sweep parameter values and metrics
- `sweep_param`: Parameter being swept
- `signal_name`: Signal being analyzed

**Usage:** Called by `plot_architecture_row_sweep()`

---

### 2.2 `plot_architecture_row_sweep()` - Line 373
**Type:** Plotly subplot grid  
**Purpose:** Show sweep behavior across multiple architectures  
**Renders:** 1 row with N subplots (one per architecture)

**Data Required:**
- `run_dirs`: List of run directories
- `signal_name`: Signal to analyze
- `sweep_param`: Parameter being swept

**Usage:** Called from signal diagnostic panel

---

### 2.3 `plot_single_arch_signal_sweep()` - Line 400
**Type:** Plotly line plot  
**Purpose:** Detailed sweep plot for single architecture  
**Renders:** 1 plot with uncertainty decomposition

**Data Required:**
- `run_dir`: Single run directory
- `signal_name`: Signal to analyze
- `sweep_param`: Parameter being swept

**Usage:** Called from signal diagnostic panel for detailed view

---

## 3️⃣ SWEEP VISUALIZATIONS - Parameter Exploration

**File:** `src/uqlab/ui_components/visualization/sweeps/heatmap_visualization.py`

### 3.1 `create_multi_signal_subplot_grid()` - Line 356
**Type:** Plotly heatmap grid  
**Purpose:** 2D parameter sweep showing multiple signals  
**Renders:** Grid of heatmaps (one per signal)
- X-axis: Epistemic parameter (under_train_per_class)
- Y-axis: Aleatoric parameter (aleatoric_noise_percentage)
- Color: Signal AUROC value

**Data Required:**
- `experiments`: List of experiment results
- `epistemic_param`: X-axis parameter name
- `aleatoric_param`: Y-axis parameter name
- `signals`: List of signal names to plot

**Usage:** Called from 2D sweep visualization tab

---

### 3.2 `render_enhanced_1d_sweep_plot()` - Line 1098
**Type:** Plotly line plot with validation overlay  
**Purpose:** Enhanced 1D sweep with C1/C2/O1/O2 compliance markers  
**Renders:** 1 plot with:
- Main line: Signal vs swept parameter
- Markers: Validation compliance status
- Annotations: Constraint violations

**Data Required:**
- `experiments`: List of experiment results
- `swept_param`: Parameter being swept
- `signal_name`: Signal to plot
- `validation_results`: Optional validation data

**Usage:** Called from 1D sweep visualization tab (Phase 4 enhanced version)

---

### 3.3 `create_1d_line_plot()` - Line 1272
**Type:** Plotly line plot  
**Purpose:** Basic 1D sweep visualization  
**Renders:** 1 line plot showing signal vs parameter

**Data Required:**
- `experiments`: List of experiment results
- `swept_param`: Parameter being swept
- `signal_name`: Signal to plot

**Usage:** Called by `render_1d_sweep_plot()` (legacy version)

---

### 3.4 `render_1d_sweep_plot()` - Line 1410
**Type:** Orchestrator function  
**Purpose:** Main entry point for 1D sweep visualization  
**Renders:** Calls `create_1d_line_plot()` or `render_enhanced_1d_sweep_plot()`

**Usage:** Called from Streamlit UI sweep tabs

---

## 📍 WHERE PLOTS ARE RENDERED

### Main Streamlit App Entry Points

1. **`streamlit_app_progressive.py`** (Progressive UI)
   - Imports from `ui_components.visualization.*`
   - Renders in experiment results panels
   - Renders in sweep analysis tabs

2. **UQ Benchmarks Tab**
   - Entry: `render_benchmark_comparison_plots()`
   - Location: Analysis section
   - Plots: 3 active rows (10 when complete)

3. **Signal Diagnostics Panel**
   - Entry: `plot_architecture_row_sweep()`, `plot_single_arch_signal_sweep()`
   - Location: Per-signal analysis
   - Plots: Architecture comparison grids

4. **Sweep Visualization Tabs**
   - Entry: `render_enhanced_1d_sweep_plot()`, `create_multi_signal_subplot_grid()`
   - Location: Parameter exploration
   - Plots: 1D/2D heatmaps

---

## 🔧 MODULAR RENDERING STRATEGY

### Current Architecture
```
Streamlit App (streamlit_app_progressive.py)
    ↓
Orchestration Layer (unified_builder.py)
    ↓
Visualization Components
    ├── analysis/uq_benchmarks.py (4 functions)
    ├── signals/signal_diagnostic_viz.py (3 functions)
    └── sweeps/heatmap_visualization.py (4 functions)
```

### Recommended Usage Pattern

```python
# Import specific plot functions
from uqlab.ui_components.visualization.analysis.uq_benchmarks import (
    render_benchmark_comparison_plots
)
from uqlab.ui_components.visualization.sweeps.heatmap_visualization import (
    render_enhanced_1d_sweep_plot,
    create_multi_signal_subplot_grid
)

# Render in appropriate Streamlit sections
with st.expander("📊 UQ Benchmarks"):
    render_benchmark_comparison_plots(api_base_url, get_headers)

with st.expander("📈 Parameter Sweeps"):
    render_enhanced_1d_sweep_plot(experiments, swept_param, signal_name)
```

---

## 🐛 KNOWN ISSUES

### Issue #1: Row 4 Not Rendering
**File:** `uq_benchmarks.py` line 415-419  
**Problem:** `prod_data = None` because production signal extraction not implemented  
**Impact:** 7 production signal subplots don't render  
**Fix Required:** Implement production signal extraction from batch experiments

### Issue #2: Hardcoded Signal Names (FIXED)
**File:** `uq_benchmarks.py` line 267-275  
**Problem:** Signal names were hardcoded  
**Solution:** Now imports from `uqlab.shared.types.SIGNAL_NAMES` (SSOT)  
**Status:** ✅ Fixed

---

## 📚 RELATED DOCUMENTATION

- **Signal Names:** `src/uqlab/shared/types.py` (SIGNAL_NAMES constant)
- **Metric Specs:** `src/uqlab/notebook_support/metric_specs.py`
- **UI Components README:** `src/uqlab/ui_components/README.md`
- **Architecture Guide:** `.bob/skills/architecture-aware-refactoring.md`

---

## 🎯 NEXT STEPS

1. **Implement Row 4 Production Signals**
   - Extract production signal metrics from batch experiments
   - Enable 7-subplot rendering in `render_benchmark_comparison_plots()`

2. **Create UI Debug Module**
   - Add `src/uqlab/ui_components/debug/plot_gallery.py`
   - Render all plots with sample data for testing
   - Add to Streamlit sidebar for development

3. **Consolidate Plot Styles**
   - Create shared color palette
   - Standardize axis labels
   - Unify legend positioning

4. **Add Plot Export**
   - Enable PNG/SVG download
   - Add high-DPI rendering option
   - Support batch export for papers

---

**End of Inventory**