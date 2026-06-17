# 🚀 Startup Fixes Applied

## Issues Fixed

### 1. ✅ Import Error: `render_configuration_progress`
**Error:**
```
ImportError: cannot import name 'render_configuration_progress' from 'uqlab.ui_components.utils'
```

**Root Cause:**
- We renamed `utils/` directory to `grouping/` to avoid conflict with `utils.py` file
- But `__init__.py` was still trying to import from `.utils` (the directory)
- The functions `render_configuration_progress` and `render_roc_explanation` are in `utils.py` (the file), not `utils/` (the directory)

**Fix Applied:**
Updated `src/uqlab/ui_components/__init__.py` to:
- Import from `.utils` (the file) for configuration/ROC utilities
- Import from `.grouping` (the directory) for sweep grouping utilities

### 2. ✅ Database Error: `no such column: uncertaintyexperiment.sweep_group_id`
**Error:**
```
sqlite3.OperationalError: no such column: uncertaintyexperiment.sweep_group_id
```

**Root Cause:**
- We added new sweep metadata fields to the SQLModel (`tables.py`)
- But the actual database doesn't have these columns yet
- SQLAlchemy tries to SELECT these columns → database error

**Fix Applied:**
Commented out the new sweep metadata fields in `backend/app/tables.py`:
```python
# NOTE: Sweep metadata fields commented out until migration is run
# To enable Option 1 (explicit sweep grouping), run: alembic upgrade head
# sweep_group_id: str | None = Field(default=None, max_length=100, index=True)
# swept_parameter: str | None = Field(default=None, max_length=100)
# swept_value: str | None = Field(default=None, max_length=100)
# sweep_index: int | None = None
```

**Why This Works:**
- Option 2 (config-based sweep grouping) doesn't need database fields
- It analyzes YAML configs to detect sweeps automatically
- The app will work immediately without migration

## Current Status

### ✅ Working Now (Option 2)
- **Config-based sweep grouping** is fully functional
- Detects sweeps by analyzing experiment configs
- Groups experiments that differ by exactly one parameter
- No database changes required

### 🔄 Optional (Option 1)
To enable **explicit sweep metadata** (recommended for production):

1. **Run the migration:**
   ```bash
   cd uqlab-streamlit/backend
   alembic upgrade head
   ```

2. **Uncomment the fields in `tables.py`:**
   ```python
   # Sweep metadata (Option 1 - for explicit sweep grouping)
   sweep_group_id: str | None = Field(default=None, max_length=100, index=True)
   swept_parameter: str | None = Field(default=None, max_length=100)
   swept_value: str | None = Field(default=None, max_length=100)
   sweep_index: int | None = None
   ```

3. **Restart the backend:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Update the script** to set sweep metadata when creating experiments

## Testing

### Test the Progressive UI
```bash
cd uqlab-streamlit
streamlit run streamlit_app_progressive.py
```

**Expected Result:**
- ✅ No import errors
- ✅ No database errors
- ✅ Sweep groups detected automatically
- ✅ All expanders collapsed by default
- ✅ Clean, organized UI

### Verify Sweep Detection
Navigate to the "Experiments & Parameter Sweeps" section:
- Should show detected sweep groups (e.g., "Sweep: aleatoric_noise_percentage")
- Each group shows summary metrics
- Click to expand for full details
- Standalone experiments shown separately

## Architecture Notes

### Why Two Options?

**Option 2 (Config-Based) - ACTIVE NOW:**
- ✅ Works immediately, no migration needed
- ✅ Detects sweeps automatically from configs
- ✅ Backward compatible with existing experiments
- ❌ O(n²) complexity for large datasets
- ❌ Can't handle 1000s of experiments efficiently

**Option 1 (Database Metadata) - OPTIONAL:**
- ✅ O(1) lookup with database indexes
- ✅ Scales to 1000s of experiments
- ✅ Explicit, no ambiguity
- ❌ Requires migration
- ❌ Requires script updates

### Hybrid Approach (Recommended)
The `group_experiments_intelligently()` function uses both:
1. Try metadata first (if Option 1 is enabled)
2. Fall back to config-based detection (Option 2)
3. Best of both worlds!

## Files Modified

1. `src/uqlab/ui_components/__init__.py` - Fixed imports
2. `backend/app/tables.py` - Commented out new fields
3. `STARTUP_FIXES.md` - This document

## Next Steps

1. ✅ **Test the UI** - Refresh Streamlit app
2. ✅ **Verify grouping** - Check if sweeps are detected
3. 🔄 **Optional: Run migration** - Enable Option 1 for production
4. 🔄 **Update script** - Add sweep metadata when creating experiments

---

**Made with Bob** 🤖