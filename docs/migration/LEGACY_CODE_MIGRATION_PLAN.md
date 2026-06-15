# Legacy Code Migration Plan

## Objective
Move legacy batch experiment code into `ui_components/legacy/` folder while keeping it functional. Other files can still import from legacy - this is just organizational cleanup.

---

## Files to Move to `ui_components/legacy/`

### 1. Batch Experiment Components
```
ui_components/batch_config.py → ui_components/legacy/batch_config.py
ui_components/batch_2d_sweep.py → ui_components/legacy/batch_2d_sweep.py
```

**Functions in these files**:
- `render_batch_sweep_config()` - 1D parameter sweep configuration
- `render_batch_base_config()` - Base config for batch experiments
- `render_batch_results()` - Batch-specific results display
- `render_2d_sweep_config()` - 2D grid sweep configuration
- `render_2d_results_analysis()` - 2D heatmap visualization

### 2. Single Experiment Components (if deprecated)
```
# These are used by the "Single Experiment" tab which is redundant with Unified Builder
# Consider moving if we deprecate that tab
ui_components/experiment_config.py → Keep (used by unified builder too)
```

**Decision**: Keep `experiment_config.py` in main folder since unified builder uses it

---

## Directory Structure After Migration

```
ui_components/
├── __init__.py (updated imports)
├── unified_builder.py (modern, primary)
├── hypothesis_validation.py (research)
├── model_selector.py (testing)
├── uq_benchmarks.py (analysis)
├── results.py (shared)
├── dataset.py (shared)
├── experiment_config.py (shared - used by unified builder)
├── utils.py (shared)
├── config_types.py (shared)
├── correlation_analysis.py (shared)
├── data_overlap_analysis.py (shared)
├── experiment_validation.py (shared)
├── heatmap_visualization.py (shared)
├── signal_visualization.py (shared)
├── validation_visualization.py (shared)
└── legacy/
    ├── __init__.py (exports legacy functions)
    ├── batch_config.py (1D batch experiments)
    └── batch_2d_sweep.py (2D batch experiments)
```

---

## Migration Steps

### Step 1: Create Legacy Folder
```bash
mkdir -p walaris-cen/ui_components/legacy
```

### Step 2: Move Files
```bash
# Move batch experiment files
mv walaris-cen/ui_components/batch_config.py walaris-cen/ui_components/legacy/
mv walaris-cen/ui_components/batch_2d_sweep.py walaris-cen/ui_components/legacy/
```

### Step 3: Create `ui_components/legacy/__init__.py`
```python
"""
Legacy UI Components

These components support the legacy batch experiment system which remains
functional for production parameter sweeps. While deprecated for new development,
they provide stable, tested batch experiment functionality.

Use the Unified Builder for new single experiments and quick tests.
Use these legacy components for systematic parameter sweeps and batch experiments.
"""

from .batch_config import (
    render_batch_sweep_config,
    render_batch_base_config,
    render_batch_results,
)

from .batch_2d_sweep import (
    render_2d_sweep_config,
    render_2d_results_analysis,
)

__all__ = [
    # 1D Batch Experiments
    'render_batch_sweep_config',
    'render_batch_base_config',
    'render_batch_results',
    
    # 2D Batch Experiments
    'render_2d_sweep_config',
    'render_2d_results_analysis',
]
```

### Step 4: Update `ui_components/__init__.py`
```python
# ... existing imports ...

# Legacy batch experiment components (still functional)
from .legacy import (
    render_batch_sweep_config,
    render_batch_base_config,
    render_batch_results,
    render_2d_sweep_config,
    render_2d_results_analysis,
)

__all__ = [
    # ... existing exports ...
    
    # Legacy (but functional) batch experiments
    'render_batch_sweep_config',
    'render_batch_base_config',
    'render_batch_results',
    'render_2d_sweep_config',
    'render_2d_results_analysis',
]
```

### Step 5: Update `streamlit_app.py` Imports
**No changes needed!** Since `ui_components/__init__.py` re-exports the legacy functions, existing imports continue to work:

```python
from ui_components import (
    # ... other imports ...
    render_batch_sweep_config,  # Still works, now from legacy/
    render_batch_base_config,   # Still works, now from legacy/
    render_batch_results,       # Still works, now from legacy/
    render_2d_sweep_config,     # Still works, now from legacy/
    render_2d_results_analysis, # Still works, now from legacy/
)
```

---

## Benefits of This Approach

### 1. **Clear Organization**
- Modern code in main `ui_components/`
- Legacy code in `ui_components/legacy/`
- Easy to see what's deprecated

### 2. **No Breaking Changes**
- Existing imports continue to work
- `streamlit_app.py` doesn't need updates
- Backward compatible

### 3. **Easy Future Removal**
- When ready to remove legacy code, just delete `legacy/` folder
- Update `__init__.py` to remove legacy exports
- Find and fix any remaining imports

### 4. **Documentation Through Structure**
- Folder name clearly indicates "legacy"
- `__init__.py` docstring explains why it exists
- New developers know not to use these for new features

---

## Import Patterns After Migration

### ✅ Recommended (via main __init__)
```python
from ui_components import render_batch_sweep_config
```

### ✅ Also Works (direct import)
```python
from ui_components.legacy import render_batch_sweep_config
```

### ✅ Also Works (explicit path)
```python
from ui_components.legacy.batch_config import render_batch_sweep_config
```

All three patterns work! The first is recommended for consistency.

---

## Testing After Migration

### 1. Verify Imports
```bash
cd walaris-cen
python -c "from ui_components import render_batch_sweep_config; print('✅ Import works')"
```

### 2. Run Streamlit App
```bash
streamlit run streamlit_app.py
```

### 3. Test Batch Experiment Tab
- Navigate to "Batch Experiments (1D)" tab
- Create a batch experiment
- Verify it works as before

### 4. Test 2D Sweep Tab
- Navigate to "Batch Experiments (2D Grid)" tab
- Configure 2D sweep
- Verify heatmap displays

---

## Future Deprecation Path

### Phase 1: Move to Legacy (This Plan) ✅
- Organize code
- No functional changes
- Clear labeling

### Phase 2: Add Deprecation Warnings (Future)
```python
# In ui_components/legacy/__init__.py
import warnings

def render_batch_sweep_config(*args, **kwargs):
    warnings.warn(
        "render_batch_sweep_config is deprecated. "
        "Use Unified Builder for new experiments.",
        DeprecationWarning,
        stacklevel=2
    )
    return _render_batch_sweep_config(*args, **kwargs)
```

### Phase 3: Hide in UI (Future)
```python
# In streamlit_app.py
with st.expander("⚠️ Legacy Batch Experiments (Deprecated)"):
    st.warning("These tabs are deprecated. Use Unified Builder instead.")
    batch_tab, batch_2d_tab = st.tabs([...])
```

### Phase 4: Remove (Far Future)
- Delete `ui_components/legacy/` folder
- Remove exports from `__init__.py`
- Remove tabs from `streamlit_app.py`

---

## Summary

**What**: Move batch experiment code to `ui_components/legacy/`

**Why**: Clear organization, easy to identify deprecated code

**Impact**: Zero - all imports continue to work

**Next Steps**: 
1. Create `legacy/` folder
2. Move 2 files
3. Create `legacy/__init__.py`
4. Update main `__init__.py`
5. Test

**Time**: 15 minutes

**Risk**: Very low - backward compatible