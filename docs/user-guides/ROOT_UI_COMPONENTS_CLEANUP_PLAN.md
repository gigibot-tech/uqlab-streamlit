# Root-Level ui_components Cleanup Plan

## Issue

There are duplicate `ui_components` directories:
1. **`uqlab-streamlit/ui_components/`** - Root level (OLD/DUPLICATE)
2. **`uqlab-streamlit/src/uqlab/ui_components/`** - Proper location (CURRENT)

## Analysis

### Root-Level ui_components (uqlab-streamlit/ui_components/)
```
ui_components/
├── __init__.py
├── 6_UI_TO_LEGACY_MIGRATION_PLAN.md  # Documentation (should be in root)
├── UI_COMPONENTS_*.md                # Documentation files
├── utils.py
├── config/
├── legacy/
├── orchestration/
├── selectors/
└── visualization/
```

### Proper Location (uqlab-streamlit/src/uqlab/ui_components/)
```
src/uqlab/ui_components/
├── __init__.py
├── config/
├── legacy/
│   ├── 6_ui/  # Just migrated here
│   ├── batch_config.py
│   └── batch_2d_sweep.py
├── orchestration/
├── results/
├── selectors/
└── visualization/
```

## Search for Usage

Need to check if anything imports from root-level `ui_components`:

```bash
# Search for imports from root-level ui_components
grep -r "from ui_components" --include="*.py" uqlab-streamlit/
grep -r "import ui_components" --include="*.py" uqlab-streamlit/
```

## Recommended Actions

### Step 1: Verify No Active Usage
- Search codebase for imports from `ui_components` (without `uqlab.` prefix)
- Check if any scripts reference root-level `ui_components`

### Step 2: Move Documentation Files
Move documentation to proper locations:
```bash
# Move migration plan to root (already there as 6_UI_TO_LEGACY_MIGRATION_PLAN.md)
mv ui_components/6_UI_TO_LEGACY_MIGRATION_PLAN.md ./
mv ui_components/UI_COMPONENTS_*.md ./docs/ or ./
```

### Step 3: Compare Content
- Check if root-level `ui_components` has any unique code
- Verify `src/uqlab/ui_components` is the complete, up-to-date version

### Step 4: Remove Root-Level Directory
```bash
# After verification
rm -rf ui_components/
```

## Risk Assessment

**Low Risk** if:
- ✅ No imports found from root-level `ui_components`
- ✅ All code is duplicated in `src/uqlab/ui_components`
- ✅ Documentation files are moved/preserved

**High Risk** if:
- ❌ Active imports from root-level `ui_components`
- ❌ Unique code not in `src/uqlab/ui_components`
- ❌ Scripts depend on root-level location

## Implementation Checklist

- [ ] Search for imports from root-level `ui_components`
- [ ] Compare file contents between both locations
- [ ] Move documentation files to appropriate locations
- [ ] Verify `src/uqlab/ui_components` is complete
- [ ] Create backup of root-level `ui_components`
- [ ] Remove root-level `ui_components` directory
- [ ] Test that Streamlit app still works
- [ ] Update any documentation referencing old location

## Expected Outcome

After cleanup:
```
uqlab-streamlit/
├── src/
│   └── uqlab/
│       └── ui_components/  # Only location for UI components
├── 6_UI_TO_LEGACY_MIGRATION_PLAN.md
├── UI_COMPONENTS_*.md
└── (no ui_components/ at root level)
```

## Next Steps

1. Run import search to verify no usage
2. If clean, proceed with removal
3. If imports found, update them first