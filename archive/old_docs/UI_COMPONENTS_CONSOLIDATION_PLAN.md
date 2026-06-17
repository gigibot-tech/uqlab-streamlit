# UI Components Consolidation Plan

## Problem Identified

Two **identical duplicate** `ui_components` folders exist:
1. **`/uqlab-streamlit/ui_components/`** (root level) - **ACTIVE** ✅
2. **`/uqlab-streamlit/src/uqlab/ui_components/`** (package level) - **DUPLICATE** ❌

## Analysis

### File Comparison
```bash
$ diff -r ui_components/ src/uqlab/ui_components/
# No output = 100% identical
```

### Import Analysis

**Root-level usage (ACTIVE):**
- [`streamlit_app.py`](streamlit_app.py:24): `from ui_components import ...`
- Main Streamlit app imports from root level

**Package-level usage (SELF-REFERENCING ONLY):**
- [`src/uqlab/ui_components/hypothesis_validation.py`](src/uqlab/ui_components/hypothesis_validation.py:74): `from uqlab.ui_components.per_sample_signals_viz import ...`
- Only files **within** the duplicate folder reference it

### File Inventory (19 files, ~310KB total)

| File | Size | Purpose |
|------|------|---------|
| `__init__.py` | 5.7 KB | Package exports |
| `config_types.py` | 3.6 KB | Configuration types |
| `correlation_analysis.py` | 10.2 KB | Signal correlation analysis |
| `data_overlap_analysis.py` | 9.6 KB | Dataset overlap visualization |
| `dataset.py` | 7.9 KB | Dataset selection UI |
| `experiment_config.py` | 23.0 KB | Experiment configuration forms |
| `experiment_validation.py` | 9.0 KB | Validation UI components |
| `heatmap_visualization.py` | 55.5 KB | Heatmap plotting (LARGE) |
| `hypothesis_validation.py` | 25.2 KB | Hypothesis testing UI |
| `model_selector.py` | 15.7 KB | Model selection UI |
| `per_sample_signals_viz.py` | 16.8 KB | Per-sample signal visualization |
| `results.py` | 16.7 KB | Results display |
| `signal_diagnostic_viz.py` | 27.3 KB | Signal diagnostics |
| `signal_visualization.py` | 50.6 KB | Signal visualization (LARGE) |
| `unified_builder.py` | 43.6 KB | Unified experiment builder |
| `legacy/` | - | Legacy components |

**Total:** ~310 KB of duplicate code

## Recommended Solution

### Option 1: Keep Root Level (RECOMMENDED) ✅

**Rationale:**
- Main app already uses root-level imports
- Simpler import paths: `from ui_components import ...`
- No package namespace pollution
- Follows Streamlit convention (app-level components)

**Actions:**
1. ✅ **Keep:** `/uqlab-streamlit/ui_components/`
2. ❌ **Delete:** `/uqlab-streamlit/src/uqlab/ui_components/`
3. 🔧 **Fix:** Update self-referencing imports in deleted folder (if any external references exist)

### Option 2: Keep Package Level (Alternative)

**Rationale:**
- Better for installable package
- Follows Python package conventions
- Cleaner namespace: `from uqlab.ui_components import ...`

**Actions:**
1. ❌ **Delete:** `/uqlab-streamlit/ui_components/`
2. ✅ **Keep:** `/uqlab-streamlit/src/uqlab/ui_components/`
3. 🔧 **Fix:** Update `streamlit_app.py` imports: `from uqlab.ui_components import ...`

## Implementation Plan (Option 1 - RECOMMENDED)

### Step 1: Verify No External Dependencies
```bash
# Search for any imports from src/uqlab/ui_components outside the folder
rg "from src\.uqlab\.ui_components|from uqlab\.ui_components" \
   --type py \
   --glob '!src/uqlab/ui_components/**'
```

### Step 2: Backup (Safety)
```bash
cd uqlab-streamlit
tar -czf ui_components_backup_$(date +%Y%m%d).tar.gz src/uqlab/ui_components/
```

### Step 3: Remove Duplicate
```bash
cd uqlab-streamlit
rm -rf src/uqlab/ui_components/
```

### Step 4: Verify Main App Still Works
```bash
cd uqlab-streamlit
python -c "from ui_components import build_base_experiment_config; print('✅ Imports work')"
```

### Step 5: Update Documentation
- Update any docs referencing `src/uqlab/ui_components/`
- Add note about consolidation in CHANGELOG

## Benefits of Consolidation

1. **Eliminate Duplication:** Remove ~310 KB of duplicate code
2. **Reduce Confusion:** Single source of truth for UI components
3. **Easier Maintenance:** Changes only need to be made once
4. **Clearer Architecture:** Streamlit components at app level, not in package
5. **Prevent Drift:** No risk of duplicates diverging over time

## Risk Assessment

**Risk Level:** 🟢 **LOW**

- Duplicates are 100% identical (verified with `diff`)
- Only self-referencing imports in duplicate folder
- Main app uses root-level version
- Easy rollback with backup

## Timeline

- **Verification:** 5 minutes
- **Backup:** 1 minute
- **Deletion:** 1 minute
- **Testing:** 5 minutes
- **Total:** ~15 minutes

## Success Criteria

✅ Main Streamlit app runs without import errors
✅ All UI components load correctly
✅ No broken imports in codebase
✅ Duplicate folder removed
✅ Documentation updated

## Rollback Plan

If issues arise:
```bash
cd uqlab-streamlit
tar -xzf ui_components_backup_YYYYMMDD.tar.gz
```

## Next Steps

1. Get approval for Option 1 (recommended)
2. Execute implementation plan
3. Test main app functionality
4. Update documentation
5. Commit changes with clear message

---

**Status:** 📋 **PLAN READY** - Awaiting approval to execute
**Recommendation:** ✅ **Option 1** (Keep root level, delete package level)
**Estimated Time:** 15 minutes
**Risk:** 🟢 Low