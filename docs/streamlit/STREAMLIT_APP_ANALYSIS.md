# Streamlit App Structure Analysis & Restructuring Recommendations

## Current Implementation Overview

### File: `streamlit_app.py` (517 lines)

**Current Structure:**
```
streamlit_app.py (main entry point)
├── Imports (39 UI component functions)
├── Custom CSS styling
├── Configuration (API_BASE_URL, API_TOKEN)
├── Helper functions (get_headers, fetch_dataset_stats)
└── main() function with 7 tabs:
    ├── 🚀 Unified Builder (NEW - recommended)
    ├── Single Experiment (LEGACY - complex form)
    ├── Batch Experiments (1D) (LEGACY - complex form)
    ├── Batch Experiments (2D Grid) (LEGACY - complex form)
    ├── 🎯 Model Selector (inference/testing)
    ├── 🔬 UQ Benchmarks (Phase 5 addition)
    └── 🧪 Hypothesis Validation (Phase 12 addition)
```

### UI Components Structure

**Directory: `ui_components/`**
```
ui_components/
├── __init__.py (exports all render functions)
├── batch_2d_sweep.py (2D sweep configuration)
├── batch_config.py (1D batch configuration)
├── config_types.py (type definitions)
├── correlation_analysis.py (signal correlation)
├── data_overlap_analysis.py (train/eval overlap)
├── dataset.py (dataset selection & stats)
├── experiment_config.py (epistemic/aleatoric/model/training config)
├── experiment_validation.py (validation logic)
├── heatmap_visualization.py (2D heatmaps)
├── hypothesis_validation.py (NEW - validation experiments)
├── model_selector.py (model inference panel)
├── results.py (experiment results display)
├── signal_visualization.py (signal plots)
├── unified_builder.py (NEW - simplified experiment builder)
├── uq_benchmarks.py (benchmarking tab)
├── utils.py (shared utilities)
└── validation_visualization.py (validation plots)
```

## Current Issues

### 1. **Tab Redundancy**
- **Unified Builder** (new, clean) vs **Single/Batch Experiment** tabs (old, complex)
- Users have 3 ways to create experiments → confusing
- Old tabs have 300+ lines of inline form logic in `streamlit_app.py`

### 2. **Logic Location Confusion**
- **streamlit_app.py**: Contains significant business logic (lines 115-517)
  - Form handling for single experiments (lines 206-355)
  - Form handling for batch experiments (lines 371-502)
  - API calls mixed with UI code
  - Dataset comparison calculations inline
  
- **ui_components/**: Well-organized but some overlap
  - `unified_builder.py` - Clean, modern approach
  - `experiment_config.py` - Reusable config components
  - `batch_config.py` - Batch-specific logic
  
### 3. **Maintenance Burden**
- Changes need to be made in multiple places
- Duplicate logic between tabs
- Hard to test (UI and logic tightly coupled)

### 4. **User Experience**
- Too many tabs (7 total)
- Unclear which tab to use
- Legacy tabs still prominent despite better alternatives

## Recommended Restructuring

### Phase 1: Simplify Tab Structure (High Priority)

**Consolidate to 4 Core Tabs:**

```
streamlit_app.py
└── main() with 4 tabs:
    ├── 🚀 Experiment Builder (unified single + batch)
    ├── 📊 Results & Analysis (experiments + benchmarks)
    ├── 🎯 Model Testing (inference panel)
    └── 🧪 Validation (hypothesis testing)
```

**Changes:**
1. **Merge** "Unified Builder" + "Single" + "Batch 1D" + "Batch 2D" → "Experiment Builder"
2. **Merge** "UQ Benchmarks" + experiment results → "Results & Analysis"
3. **Keep** "Model Testing" (unique functionality)
4. **Keep** "Validation" (research-focused)

### Phase 2: Extract Business Logic (Medium Priority)

**Create New Module: `streamlit_logic/`**

```
streamlit_logic/
├── __init__.py
├── api_client.py (all API calls)
├── experiment_builder.py (experiment creation logic)
├── results_processor.py (results fetching & processing)
└── validation_runner.py (validation experiment logic)
```

**Benefits:**
- Testable business logic
- Clear separation of concerns
- Reusable across different UIs

### Phase 3: Modernize Architecture (Low Priority)

**Adopt Page-Based Structure:**

```
pages/
├── 1_🚀_Experiment_Builder.py
├── 2_📊_Results_Analysis.py
├── 3_🎯_Model_Testing.py
└── 4_🧪_Validation.py

streamlit_app.py (landing page only)
```

**Benefits:**
- Streamlit's native multi-page support
- Better code organization
- Easier navigation
- Independent page development

## Implementation Plan

### Step 1: Create Unified Experiment Builder Tab ✅ (DONE)
- Already implemented in `ui_components/unified_builder.py`
- Handles both single and batch experiments
- Clean, modern interface

### Step 2: Deprecate Legacy Tabs (NEXT)
```python
# In streamlit_app.py
with st.expander("⚠️ Legacy Experiment Tabs (Deprecated)"):
    st.warning("These tabs are deprecated. Please use 'Unified Builder' instead.")
    single_tab, batch_tab, batch_2d_tab = st.tabs([...])
```

### Step 3: Extract API Logic
```python
# streamlit_logic/api_client.py
class UQAPIClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url
        self.token = token
    
    def fetch_dataset_stats(self, dataset_name: str, noise_type: str) -> dict:
        """Fetch dataset statistics"""
        ...
    
    def create_experiment(self, experiment_data: dict) -> dict:
        """Create a new experiment"""
        ...
    
    def get_experiment_results(self, experiment_id: str) -> dict:
        """Get experiment results"""
        ...
```

### Step 4: Consolidate Results Tabs
```python
# Merge benchmarks + experiment results
with results_tab:
    view_type = st.radio("View", ["Experiments", "Benchmarks"])
    
    if view_type == "Experiments":
        render_experiment_results(...)
    else:
        render_uq_benchmarks_tab(...)
```

### Step 5: Migrate to Pages (Optional)
- Move each tab to separate page file
- Keep `streamlit_app.py` as landing page
- Add navigation sidebar

## Comparison: Before vs After

### Before (Current)
```
streamlit_app.py: 517 lines
├── 7 tabs (confusing)
├── Inline business logic (hard to test)
├── Duplicate experiment creation flows
└── Mixed concerns (UI + API + logic)
```

### After (Proposed)
```
streamlit_app.py: ~150 lines (or landing page only)
├── 4 clear tabs
├── Clean UI code only
└── Delegates to:
    ├── ui_components/ (rendering)
    └── streamlit_logic/ (business logic)
```

## Migration Strategy

### Immediate (This Week)
1. ✅ Keep Unified Builder as primary tab
2. Move legacy tabs to expander with deprecation warning
3. Update documentation to recommend Unified Builder

### Short-term (Next Sprint)
1. Extract API client to `streamlit_logic/api_client.py`
2. Consolidate Results + Benchmarks tabs
3. Remove deprecated tabs after user migration

### Long-term (Future)
1. Migrate to page-based structure
2. Add user preferences/settings page
3. Implement experiment templates

## Recommendations

### Priority 1: User Experience
- **Action**: Hide legacy tabs behind expander with deprecation notice
- **Benefit**: Reduces confusion, guides users to better interface
- **Effort**: 30 minutes

### Priority 2: Code Quality
- **Action**: Extract API logic to separate module
- **Benefit**: Testable, maintainable, reusable
- **Effort**: 2-3 hours

### Priority 3: Architecture
- **Action**: Migrate to page-based structure
- **Benefit**: Better organization, scalability
- **Effort**: 4-6 hours

## Conclusion

**Current State**: Functional but cluttered with legacy code and redundant tabs

**Recommended State**: Clean 4-tab interface with separated concerns

**Key Insight**: The "Unified Builder" tab already provides a better UX than the legacy tabs. We should promote it and deprecate the old ones rather than maintaining parallel systems.

**Next Steps**:
1. Deprecate legacy tabs (quick win)
2. Extract API client (improves testability)
3. Consider page-based migration (long-term scalability)