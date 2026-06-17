# Renaming `uqlab` → `uqlab` (Uncertainty Quantification Lab)

## Overview
Rename the main package from `uqlab` to `uqlab` for better clarity and branding.

## Changes Required

### 1. Directory Rename
```bash
mv src/uqlab src/uqlab
```

### 2. Symlink Updates
```bash
# Update symlinks
rm uq_classification uq_benchmarks
ln -s src/uqlab/classification uq_classification
ln -s src/uqlab/benchmarks uq_benchmarks
```

### 3. Import Updates
Replace all occurrences of:
- `from uqlab.` → `from uqlab.`
- `import uqlab.` → `import uqlab.`
- `uqlab/` → `uqlab/` (in paths)

### 4. Config Consolidation
Move `src/uqlab/shared/config.py` → `src/uqlab/shared/config/global_config.py`

## Files to Update

### Python Files
- All `.py` files in `src/`
- All `.py` files in `backend/`
- All `.py` files in `scripts/`
- All `.py` files in `ui_components/`
- `streamlit_app.py`
- `streamlit_app_progressive.py`
- `run_fast.py`

### Configuration Files
- `setup.py` (if exists)
- `pyproject.toml` (if exists)
- `.env` files
- Docker files

### Documentation
- All `.md` files
- README files

## Execution Plan

1. **Backup** - Create backup before changes
2. **Rename directory** - `src/uqlab` → `src/uqlab`
3. **Update imports** - Find/replace in all files
4. **Update symlinks** - Recreate with new paths
5. **Consolidate config** - Move to shared/config/
6. **Test** - Verify all imports work
7. **Update docs** - Update all documentation

## Benefits

✅ **Clearer branding** - "UQ Lab" is self-explanatory  
✅ **Better SEO** - Easier to find and reference  
✅ **Professional** - Sounds like a research lab  
✅ **Memorable** - Short and catchy  