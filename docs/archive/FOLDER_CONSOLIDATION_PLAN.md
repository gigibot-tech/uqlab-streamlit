# UI Components Folder Consolidation Plan

## Problem
Multiple small folders (1-4 files) create unnecessary nesting and complexity.

## Current Structure Analysis

### Small Folders (≤4 files) - CANDIDATES FOR CONSOLIDATION
- `visualization/thesis/` - 1 file
- `visualization/` (root) - 2 files  
- `orchestration/` - 3 files
- `legacy/` - 3 files
- `visualization/sweeps/` - 3 files
- `visualization/validation/` - 3 files
- `config/` - 4 files
- `grouping/` - 4 files
- `visualization/analysis/` - 4 files
- `visualization/signals/` - 4 files

### Larger Folders (≥5 files) - KEEP AS-IS
- `selectors/` - 6 files ✅
- `results/` - 7 files ✅
- `workflow/` - 7 files ✅
- `progressive/` - 10 files ✅

## Proposed Consolidation

### Option 1: Flatten visualization/ subfolder structure
```
BEFORE:
visualization/
├── plot_export.py (2 files at root)
├── analysis/ (4 files)
├── signals/ (4 files)
├── sweeps/ (3 files)
├── validation/ (3 files)
└── thesis/ (1 file)

AFTER:
visualization/
├── plot_export.py
├── correlation_analysis.py
├── data_overlap_analysis.py
├── uq_benchmarks.py
├── per_sample_signals_viz.py
├── signal_diagnostic_viz.py
├── signal_visualization.py
├── heatmap_visualization.py
├── sweep_line_plot_viz.py
├── thesis_diagram_viz.py
├── hypothesis_validation.py
└── validation_visualization.py
```
**Impact**: 17 files in one folder (manageable), removes 5 subfolders

### Option 2: Merge orchestration/ into workflow/
```
BEFORE:
orchestration/ (3 files)
workflow/ (7 files)

AFTER:
workflow/ (10 files total)
├── session.py
├── step1_dataset.py
├── step2_training.py
├── step3_uncertainty.py
├── step4_evaluation.py
├── step5_review.py
├── unified_builder.py (from orchestration/)
├── validation_runner.py (from orchestration/)
└── __init__.py
```
**Impact**: Removes 1 folder, creates logical grouping (workflow + orchestration)

### Option 3: Keep config/ and grouping/ separate
**Rationale**: 
- Both have 4 files (borderline)
- Both are heavily used (8+ import locations)
- Clear, distinct purposes
- **Decision**: KEEP AS-IS ✅

### Option 4: Move legacy/ to archive or delete
```
legacy/ (3 files)
├── batch_2d_sweep.py
├── batch_config.py
└── 6_ui/ (empty folder)
```
**Decision**: Move to `/dead_code` or delete entirely (already have dead_code folder)

## Recommended Actions

### Priority 1: Flatten visualization/ (High Impact)
- Consolidate 5 subfolders into 1
- Update 10+ import statements
- Simplifies navigation significantly

### Priority 2: Merge orchestration/ into workflow/ (Medium Impact)
- Logical grouping (both are about experiment workflow)
- Only 1 import to update
- Removes unnecessary nesting

### Priority 3: Archive legacy/ (Low Impact)
- Move to dead_code/ folder
- Already have archiving infrastructure
- Cleans up ui_components/

## Implementation Steps

1. **Create backup branch**
2. **Flatten visualization/**:
   - Move all files to visualization/ root
   - Update imports in affected files
   - Remove empty subfolders
3. **Merge orchestration/ into workflow/**:
   - Move files
   - Update 1 import in hypothesis_validation.py
4. **Archive legacy/**:
   - Move to dead_code/ui_components_legacy/
5. **Test imports**
6. **Commit and push**

## Files Requiring Import Updates

### For visualization/ flattening:
- `ui_components/visualization/validation/hypothesis_validation.py`
- `ui_components/progressive/sweep_analysis_section.py`
- Any other files importing from visualization subfolders

### For orchestration/ → workflow/:
- `ui_components/visualization/validation/hypothesis_validation.py`

## Expected Outcome

```
BEFORE: 15 folders in ui_components/
AFTER: 9 folders in ui_components/ (40% reduction)

Folder structure becomes:
ui_components/
├── config/ (4 files) ✅
├── grouping/ (4 files) ✅
├── progressive/ (10 files) ✅
├── results/ (7 files) ✅
├── selectors/ (6 files) ✅
├── visualization/ (17 files) ✅
├── workflow/ (10 files) ✅
└── (3 root files)
```

**Benefits**:
- Simpler navigation
- Fewer nested imports
- Clearer organization
- Easier to find files