# UI Components Reorganization Plan

**Date**: 2026-06-24  
**Status**: Analysis Complete - Ready for Review  
**Goal**: Consolidate related folders and restructure visualization components

---

## Executive Summary

After analyzing the `uqlab-streamlit/src/uqlab/ui_components/` directory, I found that **previous reorganization work has already been completed** (see `UI_COMPONENTS_REORGANIZATION_COMPLETE.md`). However, several folders require further consolidation:

### Key Findings:
1. ✅ **Major reorganization already done** (2026-06-07) - 23 files organized into 9 subdirectories
2. ⚠️ **grouping/** - Actively used, should stay (not dead code)
3. ⚠️ **integrations/** - Contains watsonx.ai integration (active feature)
4. ⚠️ **orchestration/** - Compatibility shim for workflow/ (can be removed)
5. ⚠️ **selectors/** - Minimal, actively used (keep)
6. ✅ **progressive/** - Core feature for progressive disclosure UI
7. ⚠️ **visualization/** - Well-organized but has unused components

---

## Part 1: Consolidation Analysis

### 1.1 grouping/ → **KEEP (Active)**

**Decision**: ✅ **Keep in current location**

**Rationale**:
- **Actively imported** by 7 files across the codebase
- Core functionality for sweep campaign grouping
- Used by both `progressive/` and `results/` modules
- Has comprehensive README.md documentation
- Provides intelligent experiment grouping (3 strategies: metadata, name pattern, config-based)

**Import Usage**:
```python
# Used by:
- ui_components/selectors/smart_experiment_selector.py
- ui_components/progressive/launch_results.py
- ui_components/progressive/sweep_analysis_section.py
- ui_components/results/experiment_results_panel.py
- ui_components/results/checkpoint_resume.py
- ui_components/grouping/sweep_grouping.py (internal)
- ui_components/grouping/campaign_groups.py (internal)
```

**Files**:
- `__init__.py` - Public API exports
- `campaign_format.py` - Human-readable campaign labels (123 lines)
- `campaign_groups.py` - Unified campaign grouping (86 lines)
- `sweep_grouping.py` - Streamlit render layer (135 lines)
- `README.md` - Comprehensive documentation (257 lines)

**Recommendation**: No action needed. This is a well-organized, actively used module.

---

### 1.2 integrations/ → **KEEP (Active Feature)**

**Decision**: ✅ **Keep in current location**

**Rationale**:
- Contains **watsonx.ai cloud inference integration** (335 lines)
- Active feature for cloud-based model inference
- Provides UI components for cloud mode toggle and configuration
- Not imported yet but ready for use (feature flag pattern)
- Documented in `WATSONX_DEPLOYMENT_GUIDE.md`

**Files**:
- `__init__.py` - Module marker
- `watsonx.py` - Complete watsonx.ai integration (335 lines)
  - `render_cloud_mode_toggle()` - Cloud mode UI
  - `render_cloud_inference_status()` - Performance comparison
  - `create_cloud_inference_client()` - Client creation
  - `run_cloud_inference()` - Cloud inference execution
  - `render_cloud_deployment_guide()` - Deployment instructions

**Recommendation**: No action needed. This is a complete, production-ready feature.

---

### 1.3 orchestration/ → **REMOVE (Compatibility Shim)**

**Decision**: ⚠️ **Remove - Redirect imports to workflow/**

**Rationale**:
- **Compatibility re-export layer** only (19 lines)
- All actual code lives in `workflow/` directory
- Only imported by 1 file: `visualization/validation/hypothesis_validation.py`
- Comment says: "Compatibility re-exports — orchestration modules live under `workflow/`"

**Current Structure**:
```python
# orchestration/__init__.py
from ..workflow.unified_builder import (
    render_experiment_execution_panel,
    render_unified_builder,
)
from ..workflow.validation_runner import (
    render_local_validation_viz,
    render_preset_validation_sweeps,
    run_validation_experiments,
)
```

**Migration Plan**:
1. Update `visualization/validation/hypothesis_validation.py` line 79:
   ```python
   # OLD
   from uqlab.ui_components.orchestration.validation_runner import (...)
   
   # NEW
   from uqlab.ui_components.workflow.validation_runner import (...)
   ```
2. Delete `orchestration/` directory
3. Update root `__init__.py` if needed

**Risk**: Low - only 1 import to update

---

### 1.4 selectors/ → **KEEP (Active)**

**Decision**: ✅ **Keep in current location**

**Rationale**:
- Actively used for experiment selection UI
- Lazy-loaded via `__getattr__` pattern (modern Python)
- Contains `smart_experiment_selector.py` (actively imported)
- Part of the reorganized structure from 2026-06-07

**Import Usage**:
```python
# Used by:
- ui_components/grouping/campaign_groups.py
```

**Files**:
- `__init__.py` - Lazy loading exports (19 lines)
- `dataset.py` - Dataset selection UI
- `model_selector.py` - Model selection UI
- `paper_sweep_launch.py` - Paper sweep launcher
- `sidebar_controls.py` - Sidebar controls
- `smart_experiment_selector.py` - Smart experiment selector (actively used)

**Recommendation**: No action needed. Well-organized selector components.

---

### 1.5 progressive/ → **KEEP (Core Feature)**

**Decision**: ✅ **Keep in current location**

**Rationale**:
- **Core feature** for `streamlit_app_progressive.py` (the main app)
- Progressive disclosure UI pattern implementation
- Actively used by workflow steps
- Well-documented in module docstring

**Purpose**: "Components specific to the progressive disclosure UI pattern used in streamlit_app_progressive.py"

**Files** (11 files):
- `__init__.py` - Public API (26 lines)
- `api_client.py` - API client for experiments
- `config_helpers.py` - Config loading utilities
- `launch_panel.py` - Launch panel UI
- `launch_results.py` - Launch results display
- `launch_session.py` - Session management
- `plot_probe_panel.py` - Plot probe panel
- `results_section.py` - Results section
- `sweep_analysis_section.py` - Sweep analysis
- `sweep_launch_cards.py` - Launch cards UI

**Recommendation**: No action needed. This is the heart of the progressive UI.

---

## Part 2: Visualization Restructuring

### 2.1 Current Structure Analysis

```
visualization/
├── __init__.py
├── plot_export.py              # PNG export utility (159 lines)
├── analysis/
│   ├── __init__.py
│   ├── correlation_analysis.py
│   ├── data_overlap_analysis.py
│   └── uq_benchmarks.py
├── campaign/
│   └── campaign_report_viz.py  # Campaign report download
├── signals/
│   ├── __init__.py
│   ├── per_sample_signals_viz.py
│   ├── signal_diagnostic_viz.py
│   └── signal_visualization.py
├── sweeps/
│   ├── __init__.py
│   ├── batch_2d_sweep.py       # ⚠️ Potentially unused
│   ├── heatmap_visualization.py
│   ├── paper_benchmark_plot_viz.py
│   └── sweep_line_plot_viz.py
├── thesis/
│   └── thesis_diagram_viz.py   # Thesis-specific diagram
└── validation/
    ├── __init__.py
    ├── hypothesis_validation.py
    └── validation_visualization.py
```

### 2.2 Import Usage Analysis

**Actively Used**:
- ✅ `plot_export.py` - Used by sweep_line_plot_viz.py, paper_benchmark_plot_viz.py
- ✅ `signals/per_sample_signals_viz.py` - Used by hypothesis_validation.py
- ✅ `signals/signal_diagnostic_viz.py` - Used by hypothesis_validation.py, validation_runner.py
- ✅ `sweeps/sweep_line_plot_viz.py` - Used by sweep_grouping.py, sweep_analysis_section.py, paper_benchmark_plot_viz.py
- ✅ `sweeps/paper_benchmark_plot_viz.py` - Used by sweep_analysis_section.py
- ✅ `thesis/thesis_diagram_viz.py` - Used by sweep_analysis_section.py, step5_review.py
- ✅ `campaign/campaign_report_viz.py` - Used by sweep_analysis_section.py

**Potentially Unused** (no imports found):
- ⚠️ `analysis/correlation_analysis.py` - No imports found
- ⚠️ `analysis/data_overlap_analysis.py` - No imports found
- ⚠️ `analysis/uq_benchmarks.py` - No imports found
- ⚠️ `signals/signal_visualization.py` - No imports found
- ⚠️ `sweeps/batch_2d_sweep.py` - No imports found
- ⚠️ `sweeps/heatmap_visualization.py` - No imports found
- ⚠️ `validation/validation_visualization.py` - No imports found
- ⚠️ `validation/hypothesis_validation.py` - Imported but may be legacy

### 2.3 Proposed Actions

#### Move to dead_code/:

1. **analysis/** (entire directory) - No active imports
   - `correlation_analysis.py`
   - `data_overlap_analysis.py`
   - `uq_benchmarks.py`

2. **sweeps/batch_2d_sweep.py** - No imports found

3. **sweeps/heatmap_visualization.py** - No imports found

4. **signals/signal_visualization.py** - No imports found

5. **validation/validation_visualization.py** - No imports found

#### Keep (Actively Used):

- ✅ `plot_export.py` - Core utility
- ✅ `signals/per_sample_signals_viz.py`
- ✅ `signals/signal_diagnostic_viz.py`
- ✅ `sweeps/sweep_line_plot_viz.py`
- ✅ `sweeps/paper_benchmark_plot_viz.py`
- ✅ `thesis/thesis_diagram_viz.py`
- ✅ `campaign/campaign_report_viz.py`
- ✅ `validation/hypothesis_validation.py` (verify usage first)

### 2.4 Proposed New Structure

```
visualization/
├── __init__.py
├── plot_export.py              # Core PNG export utility
├── campaign/
│   └── campaign_report_viz.py  # Campaign reports
├── signals/
│   ├── __init__.py
│   ├── per_sample_signals_viz.py
│   └── signal_diagnostic_viz.py
├── sweeps/
│   ├── __init__.py
│   ├── paper_benchmark_plot_viz.py
│   └── sweep_line_plot_viz.py
├── thesis/
│   └── thesis_diagram_viz.py   # Thesis-specific
└── validation/
    ├── __init__.py
    └── hypothesis_validation.py
```

**Removed**:
- `analysis/` → `dead_code/ui_components/visualization/analysis/`
- `signals/signal_visualization.py` → `dead_code/`
- `sweeps/batch_2d_sweep.py` → `dead_code/`
- `sweeps/heatmap_visualization.py` → `dead_code/`
- `validation/validation_visualization.py` → `dead_code/`

---

## Part 3: Implementation Plan

### Phase 1: Remove orchestration/ Shim (Low Risk)

**Steps**:
1. Update import in `visualization/validation/hypothesis_validation.py`:
   ```bash
   # Line 79
   sed -i '' 's/from uqlab.ui_components.orchestration/from uqlab.ui_components.workflow/' \
     src/uqlab/ui_components/visualization/validation/hypothesis_validation.py
   ```

2. Delete orchestration directory:
   ```bash
   rm -rf src/uqlab/ui_components/orchestration/
   ```

3. Test import:
   ```bash
   cd uqlab-streamlit
   PYTHONPATH=src python3 -c "from uqlab.ui_components.workflow.validation_runner import render_preset_validation_sweeps; print('✅ Import works')"
   ```

**Risk**: Low - only 1 file affected  
**Estimated Time**: 5 minutes

---

### Phase 2: Move Unused Visualization Components (Medium Risk)

**Steps**:

1. Create dead_code structure:
   ```bash
   mkdir -p dead_code/ui_components/visualization/{analysis,signals,sweeps,validation}
   ```

2. Move unused files:
   ```bash
   # Analysis directory (entire)
   mv src/uqlab/ui_components/visualization/analysis/* \
      dead_code/ui_components/visualization/analysis/
   
   # Individual files
   mv src/uqlab/ui_components/visualization/signals/signal_visualization.py \
      dead_code/ui_components/visualization/signals/
   
   mv src/uqlab/ui_components/visualization/sweeps/batch_2d_sweep.py \
      dead_code/ui_components/visualization/sweeps/
   
   mv src/uqlab/ui_components/visualization/sweeps/heatmap_visualization.py \
      dead_code/ui_components/visualization/sweeps/
   
   mv src/uqlab/ui_components/visualization/validation/validation_visualization.py \
      dead_code/ui_components/visualization/validation/
   ```

3. Remove empty analysis directory:
   ```bash
   rmdir src/uqlab/ui_components/visualization/analysis/
   ```

4. Update `__init__.py` files if they reference moved files

5. Test application:
   ```bash
   streamlit run streamlit_app_progressive.py
   ```

**Risk**: Medium - multiple files moved, but none actively imported  
**Estimated Time**: 15 minutes

---

### Phase 3: Verification & Documentation

**Steps**:

1. Run import tests:
   ```bash
   cd uqlab-streamlit
   PYTHONPATH=src python3 -c "
   from uqlab.ui_components.grouping import group_experiments_intelligently
   from uqlab.ui_components.progressive import render_launch_result
   from uqlab.ui_components.visualization.sweeps import sweep_line_plot_viz
   print('✅ All imports work')
   "
   ```

2. Test Streamlit apps:
   ```bash
   # Test progressive app (main)
   streamlit run streamlit_app_progressive.py
   
   # Test legacy app
   streamlit run streamlit_app.py
   ```

3. Update documentation:
   - Update `UI_COMPONENTS_REORGANIZATION_COMPLETE.md`
   - Add entry to `FOLDER_CONSOLIDATION_COMPLETE.md`
   - Update `README.md` if needed

**Risk**: Low - verification only  
**Estimated Time**: 10 minutes

---

## Part 4: Summary of Changes

### Files to Move to dead_code:

**Total**: 8 files

1. `visualization/analysis/correlation_analysis.py`
2. `visualization/analysis/data_overlap_analysis.py`
3. `visualization/analysis/uq_benchmarks.py`
4. `visualization/analysis/__init__.py`
5. `visualization/signals/signal_visualization.py`
6. `visualization/sweeps/batch_2d_sweep.py`
7. `visualization/sweeps/heatmap_visualization.py`
8. `visualization/validation/validation_visualization.py`

### Directories to Remove:

1. `orchestration/` - Compatibility shim (redirect to workflow/)
2. `visualization/analysis/` - Entire directory unused

### Directories to Keep:

1. ✅ `grouping/` - Actively used (7 imports)
2. ✅ `integrations/` - Active watsonx.ai feature
3. ✅ `selectors/` - Active experiment selection
4. ✅ `progressive/` - Core progressive UI feature
5. ✅ `visualization/` - Keep active components only

---

## Part 5: Risk Assessment

### Low Risk:
- ✅ Removing `orchestration/` shim (1 import to update)
- ✅ Moving unused visualization files (no imports found)

### Medium Risk:
- ⚠️ Verify `hypothesis_validation.py` is actually used
- ⚠️ Check if any dynamic imports exist (e.g., `importlib`)

### High Risk:
- ❌ None identified

---

## Part 6: Rollback Plan

If issues arise:

1. **Restore orchestration/**:
   ```bash
   git checkout src/uqlab/ui_components/orchestration/
   ```

2. **Restore moved files**:
   ```bash
   mv dead_code/ui_components/visualization/* \
      src/uqlab/ui_components/visualization/
   ```

3. **Revert import changes**:
   ```bash
   git checkout src/uqlab/ui_components/visualization/validation/hypothesis_validation.py
   ```

---

## Recommendations

### Immediate Actions (High Priority):

1. ✅ **Remove orchestration/ shim** - Clean up compatibility layer
2. ✅ **Move unused visualization files** - Reduce clutter

### Future Considerations (Low Priority):

1. **Verify hypothesis_validation.py usage** - May be legacy
2. **Document watsonx.ai integration** - Add usage examples
3. **Consider merging thesis/ into campaign/** - Both are report-related
4. **Add tests for active components** - Ensure stability

### Do NOT Change:

1. ❌ **grouping/** - Actively used, well-documented
2. ❌ **integrations/** - Production-ready feature
3. ❌ **progressive/** - Core UI pattern
4. ❌ **selectors/** - Active components
5. ❌ **workflow/** - Core workflow logic

---

## Conclusion

The `ui_components/` directory is **already well-organized** from the 2026-06-07 reorganization. The main opportunities for improvement are:

1. **Remove orchestration/ compatibility shim** (5 min, low risk)
2. **Move 8 unused visualization files to dead_code** (15 min, medium risk)
3. **Keep everything else as-is** (already well-structured)

**Total Estimated Time**: 30 minutes  
**Total Risk**: Low to Medium  
**Breaking Changes**: None (all changes are internal)

---

**Status**: 📋 Ready for Review  
**Next Step**: Execute Phase 1 (Remove orchestration/ shim)  
**Made with Bob** 🤖