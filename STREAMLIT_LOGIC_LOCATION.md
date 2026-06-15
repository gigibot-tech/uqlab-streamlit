# Where is the Logic in streamlit_app.py?

## Executive Summary

**The `streamlit_app.py` file (241 lines) contains MINIMAL logic** - it's a thin orchestration layer that delegates all functionality to modular UI components.

## Architecture Pattern: **Thin Controller + Fat Components**

```
streamlit_app.py (241 LoC)
    ↓ imports & delegates to
ui_components/ (multiple files, 300-1500 LoC each)
    ↓ calls
backend API (FastAPI)
    ↓ executes
ML Pipeline (training, evaluation, etc.)
```

## Logic Distribution

### 1. streamlit_app.py (241 LoC) - **Orchestration Only**

**What it does:**
- Page configuration (lines 101-105)
- API configuration (lines 97-98)
- Tab structure (lines 190-225)
- Minimal helper functions (2 functions, ~20 LoC total)

**What it does NOT do:**
- No form rendering
- No data processing
- No visualization
- No business logic
- No API calls (except 1 helper function)

**Code breakdown:**
```python
# Lines 1-125: Imports, CSS, config, 2 helper functions
# Lines 126-241: main() function - pure orchestration
#   - Calls render_dataset_selection()
#   - Calls render_cloud_mode_toggle()
#   - Creates 3 tabs
#   - Delegates to render_hypothesis_validation_tab()
#   - Delegates to render_unified_builder()
#   - Delegates to render_model_selector()
#   - Delegates to render_uq_benchmarks_tab()
```

### 2. ui_components/ - **Where ALL Logic Lives**

Located at: `src/walaris/ui_components/`

**File sizes (LoC analysis):**

| File | LoC | Purpose |
|------|-----|---------|
| `heatmap_visualization.py` | 1,567 | Signal heatmaps, correlation plots |
| `signal_visualization.py` | 1,131 | Per-sample signal plots |
| `unified_builder.py` | 1,123 | Unified experiment builder (replaces old batch) |
| `signal_diagnostic_viz.py` | 822 | Signal diagnostics & UDE display |
| `hypothesis_validation.py` | 678 | Hypothesis validation tab |
| `validation_visualization.py` | 661 | Validation result plots |
| `uq_benchmarks.py` | 598 | UQ benchmark comparisons |
| `experiment_config.py` | 559 | Experiment configuration forms |
| `results.py` | 417 | Experiment results display |
| `per_sample_signals_viz.py` | 417 | Per-sample signal visualization |
| `model_selector.py` | 389 | Model selection & inference |
| `correlation_analysis.py` | 254 | Signal correlation analysis |
| `data_overlap_analysis.py` | 237 | Data overlap visualization |
| `validation_runner.py` | 156 | Validation execution |
| `experiment_validation.py` | 224 | Experiment validation logic |
| `dataset.py` | 197 | Dataset selection & stats |
| `utils.py` | 205 | Shared utilities |
| `config_types.py` | 89 | Type definitions |

**Total: ~10,724 LoC in ui_components/**

### 3. Backend API (FastAPI) - **Business Logic & ML Pipeline**

Located at: `backend/app/`

**Key files:**

| File | LoC | Purpose |
|------|-----|---------|
| `services/batch_experiment_service.py` | 1,378 | Batch experiment orchestration |
| `api/routes/experiments.py` | 460 | Experiment CRUD endpoints |
| `api/routes/batch_experiments.py` | 385 | Batch experiment endpoints |
| `domain/models.py` | 347 | Domain models |
| `services/storage/wxgov.py` | 300 | watsonx.governance integration |
| `api/routes/datasets.py` | 250 | Dataset stats endpoints |
| `tables.py` | 251 | Database schema |
| `services/metrics_service.py` | 247 | Metrics calculation |

**Total backend: ~11,655 LoC**

### 4. ML Pipeline (Training & Evaluation)

Located at: `scripts/` and `src/walaris/classification/`

**Key files:**

| File | LoC | Purpose |
|------|-----|---------|
| `scripts/run_fast_uncertainty_classification.py` | 1,245 | Main training script |
| `src/walaris/classification/data_loader.py` | 589 | Data loading & preprocessing |
| `src/walaris/classification/feature_extractor.py` | 491 | Feature extraction (DINOv2) |
| `src/models/load_dinov2_model.py` | 678 | Model loading |

**Total ML pipeline: ~3,000+ LoC**

## Answer to "Where is the logic?"

### ❌ NOT in streamlit_app.py
The main file is just 241 lines of orchestration code.

### ✅ Logic is in 3 layers:

1. **UI Layer** (`ui_components/`): ~10,724 LoC
   - Form rendering
   - Data visualization
   - User interaction
   - API calls to backend

2. **API Layer** (`backend/app/`): ~11,655 LoC
   - Request handling
   - Database operations
   - Experiment orchestration
   - Metrics calculation

3. **ML Layer** (`scripts/` + `src/`): ~3,000+ LoC
   - Data loading
   - Model training
   - Evaluation
   - Signal calculation

## Design Pattern: **Separation of Concerns**

```
┌─────────────────────────────────────────┐
│  streamlit_app.py (241 LoC)             │
│  - Page config                          │
│  - Tab structure                        │
│  - Delegates to components              │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  ui_components/ (~10,724 LoC)           │
│  - Forms & inputs                       │
│  - Visualizations                       │
│  - API calls                            │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  backend/app/ (~11,655 LoC)             │
│  - REST API endpoints                   │
│  - Database operations                  │
│  - Experiment orchestration             │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  ML Pipeline (~3,000+ LoC)              │
│  - Data loading                         │
│  - Model training                       │
│  - Evaluation & metrics                 │
└─────────────────────────────────────────┘
```

## Key Insight

**streamlit_app.py is intentionally thin** - it follows the **Single Responsibility Principle**:
- Its ONLY job is to set up the page and delegate to specialized components
- All actual logic is in modular, testable components
- This makes the codebase maintainable and scalable

## Example: Where is "Create Experiment" logic?

1. **streamlit_app.py** (line 204): Calls `render_unified_builder()`
2. **ui_components/unified_builder.py** (1,123 LoC): Renders form, collects inputs
3. **ui_components/unified_builder.py**: Makes POST request to `/api/v1/experiments`
4. **backend/app/api/routes/experiments.py** (460 LoC): Handles request
5. **backend/app/services/batch_experiment_service.py** (1,378 LoC): Orchestrates execution
6. **scripts/run_fast_uncertainty_classification.py** (1,245 LoC): Runs training

**Total logic: ~4,200 LoC across 5 files**
**streamlit_app.py contribution: 1 line (function call)**

## Conclusion

The logic is **NOT** in `streamlit_app.py` - it's distributed across:
- **UI components** (10,724 LoC)
- **Backend API** (11,655 LoC)  
- **ML pipeline** (3,000+ LoC)

**Total codebase: ~25,000+ LoC**
**streamlit_app.py: 241 LoC (< 1% of total)**

This is **excellent architecture** - thin orchestration layer with modular, reusable components.