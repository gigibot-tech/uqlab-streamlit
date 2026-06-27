# Comprehensive Folder Reorganization Plan

> **Superseded (2026-06):** Numbered `1_data`…`7_orchestration` layout was never implemented. Current layout: [`docs/architecture/PACKAGE_REDESIGN.md`](../architecture/PACKAGE_REDESIGN.md).

**Date**: 2026-06-17  
**Goal**: Clean up and consolidate scattered folders in `src/uqlab/`

---

## 🎯 Overview

**Current Issues**:
1. Legacy code scattered in 3 top-level folders
2. `__pycache__` folders tracked in git (should be ignored)
3. Several folders that could be better organized
4. Unclear separation between core and auxiliary code

**Solution**: Consolidate into logical groups

---

## 📊 Current Structure Analysis

```
src/uqlab/
├── 1_data/                    ✅ KEEP (numbered pipeline stage)
├── 2_models/                  ✅ KEEP (numbered pipeline stage)
├── 3_training/                ✅ KEEP (numbered pipeline stage)
├── 4_evaluation/              ✅ KEEP (numbered pipeline stage)
├── 5_api/                     ✅ KEEP (numbered pipeline stage)
├── 7_orchestration/           ✅ KEEP (numbered pipeline stage)
├── ui_components/             ✅ KEEP (UI layer)
├── tests/                     ✅ KEEP (testing)
│
├── triage/                    ❌ MOVE → 4_evaluation/legacy/triage/
├── legacy_metrics/            ❌ MOVE → 4_evaluation/legacy/metrics/
├── legacy_experiments/        ❌ MOVE → 4_evaluation/legacy/experiments/
│
├── backbones/                 🤔 CONSOLIDATE → 2_models/backbones/
├── classification/            🤔 CONSOLIDATE → 4_evaluation/classification/
├── data_loaders/              🤔 CONSOLIDATE → 1_data/loaders/
│
├── benchmarks/                ✅ KEEP (cross-cutting concern)
├── notebook_support/          ✅ KEEP (auxiliary tools)
├── shared/                    ✅ KEEP (shared utilities)
│
└── __pycache__/               ❌ REMOVE (should be gitignored)
    └── (multiple nested)
```

---

## 🗂️ Proposed Reorganization

### Phase 1: Legacy Code Consolidation

**Move to `4_evaluation/legacy/`**:
```
4_evaluation/legacy/
├── __init__.py
├── README.md                  # This document moves here
├── triage/
│   ├── __init__.py
│   └── dualxda_axioms.py
├── metrics/
│   ├── __init__.py
│   ├── acquisition_functions.py
│   ├── integrity_score.py
│   ├── standard_uq_metrics.py
│   ├── surgical_score.py
│   └── uncertainty_suite.py
└── experiments/
    ├── __init__.py
    ├── dualxda_stream.py
    └── risk_coverage_report.py
```

**Files to move**: 8 files + 1 doc
**Import updates**: 4 files

### Phase 2: Core Module Consolidation

#### A. Backbones → 2_models/backbones/
```bash
mv src/uqlab/backbones/ src/uqlab/2_models/backbones/
```
**Rationale**: Backbones are model architectures, belong with models

**Files**: 5 files
- `baseline_models.py`
- `dinov2_backbone.py`
- `heteroscedastic_mc_dropout.py`
- `imagenet_baselines.py`

#### B. Data Loaders → 1_data/loaders/
```bash
mv src/uqlab/data_loaders/ src/uqlab/1_data/loaders/
```
**Rationale**: Data loaders belong with data pipeline

**Files**: 4 files
- `cifar10_loader.py`
- `cifar10n_loader.py`
- `dinov2_transforms.py`

#### C. Classification → 4_evaluation/classification/
```bash
mv src/uqlab/classification/ src/uqlab/4_evaluation/classification/
```
**Rationale**: Classification evaluation belongs with evaluation

**Files**: ~15 files (has subdirectories)

### Phase 3: Clean Up __pycache__

```bash
# Remove from git tracking
find src/uqlab -type d -name "__pycache__" -exec git rm -r --cached {} \; 2>/dev/null

# Delete from filesystem
find src/uqlab -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null
```

**Note**: Already in `.gitignore` (line 2), just need to untrack

---

## 📋 Detailed Migration Plan

### Step 1: Create New Directories
```bash
cd /Users/andrearachetta/Documents/old_pilots/uqlab-streamlit

# Legacy folders
mkdir -p src/uqlab/4_evaluation/legacy/{triage,metrics,experiments}

# Consolidated folders
mkdir -p src/uqlab/2_models/backbones
mkdir -p src/uqlab/1_data/loaders
mkdir -p src/uqlab/4_evaluation/classification
```

### Step 2: Move Legacy Code
```bash
# Move triage
mv src/uqlab/triage/dualxda_axioms.py src/uqlab/4_evaluation/legacy/triage/

# Move legacy_metrics
mv src/uqlab/legacy_metrics/*.py src/uqlab/4_evaluation/legacy/metrics/

# Move legacy_experiments  
mv src/uqlab/legacy_experiments/*.py src/uqlab/4_evaluation/legacy/experiments/

# Move this documentation
mv LEGACY_FOLDER_REORGANIZATION.md src/uqlab/4_evaluation/legacy/README.md
```

### Step 3: Move Core Modules
```bash
# Move backbones
mv src/uqlab/backbones/* src/uqlab/2_models/backbones/

# Move data_loaders
mv src/uqlab/data_loaders/* src/uqlab/1_data/loaders/

# Move classification
mv src/uqlab/classification/* src/uqlab/4_evaluation/classification/
```

### Step 4: Create __init__.py Files
```bash
# Legacy
touch src/uqlab/4_evaluation/legacy/__init__.py
touch src/uqlab/4_evaluation/legacy/triage/__init__.py
touch src/uqlab/4_evaluation/legacy/metrics/__init__.py
touch src/uqlab/4_evaluation/legacy/experiments/__init__.py

# Consolidated (if not exist)
touch src/uqlab/2_models/backbones/__init__.py
touch src/uqlab/1_data/loaders/__init__.py
touch src/uqlab/4_evaluation/classification/__init__.py
```

### Step 5: Update Imports

**Files needing updates** (estimated 10-15 files):

1. **Legacy imports** (4 files):
   - `4_evaluation/signals/attribution.py`
   - `4_evaluation/legacy/metrics/acquisition_functions.py`
   - `4_evaluation/legacy/metrics/uncertainty_suite.py`
   - `4_evaluation/legacy/experiments/risk_coverage_report.py`

2. **Backbones imports** (search for `from uqlab.backbones`):
   - Update to `from uqlab.2_models.backbones`

3. **Data loaders imports** (search for `from uqlab.data_loaders`):
   - Update to `from uqlab.1_data.loaders`

4. **Classification imports** (search for `from uqlab.classification`):
   - Update to `from uqlab.4_evaluation.classification`

### Step 6: Clean __pycache__
```bash
# Remove from git
find src/uqlab -type d -name "__pycache__" | while read dir; do
    git rm -r --cached "$dir" 2>/dev/null || true
done

# Delete from filesystem
find src/uqlab -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true
```

### Step 7: Remove Empty Directories
```bash
rmdir src/uqlab/triage 2>/dev/null || true
rmdir src/uqlab/legacy_metrics 2>/dev/null || true
rmdir src/uqlab/legacy_experiments 2>/dev/null || true
rmdir src/uqlab/backbones 2>/dev/null || true
rmdir src/uqlab/data_loaders 2>/dev/null || true
rmdir src/uqlab/classification 2>/dev/null || true
```

---

## 🔍 Import Search Commands

```bash
# Find all imports that need updating
cd /Users/andrearachetta/Documents/old_pilots/uqlab-streamlit

# Legacy imports
grep -r "from uqlab\.triage" --include="*.py" src/uqlab/
grep -r "from uqlab\.legacy_metrics" --include="*.py" src/uqlab/
grep -r "from uqlab\.legacy_experiments" --include="*.py" src/uqlab/

# Core module imports
grep -r "from uqlab\.backbones" --include="*.py" src/uqlab/
grep -r "from uqlab\.data_loaders" --include="*.py" src/uqlab/
grep -r "from uqlab\.classification" --include="*.py" src/uqlab/
```

---

## ✅ Final Structure

```
src/uqlab/
├── 1_data/
│   ├── loaders/               # From: data_loaders/
│   │   ├── cifar10_loader.py
│   │   ├── cifar10n_loader.py
│   │   └── dinov2_transforms.py
│   └── ...
│
├── 2_models/
│   ├── backbones/             # From: backbones/
│   │   ├── baseline_models.py
│   │   ├── dinov2_backbone.py
│   │   ├── heteroscedastic_mc_dropout.py
│   │   └── imagenet_baselines.py
│   └── ...
│
├── 3_training/
│   └── ...
│
├── 4_evaluation/
│   ├── classification/        # From: classification/
│   │   ├── attribution_signals.py
│   │   ├── benchmark_axes.py
│   │   └── ...
│   ├── legacy/                # NEW: Consolidated legacy code
│   │   ├── README.md          # This document
│   │   ├── triage/            # From: triage/
│   │   ├── metrics/           # From: legacy_metrics/
│   │   └── experiments/       # From: legacy_experiments/
│   └── ...
│
├── 5_api/
├── 7_orchestration/
├── ui_components/
├── tests/
├── benchmarks/                # KEEP (cross-cutting)
├── notebook_support/          # KEEP (auxiliary)
└── shared/                    # KEEP (utilities)
```

---

## 📊 Impact Summary

### Files to Move
- **Legacy**: 8 files + 1 doc
- **Backbones**: 5 files
- **Data loaders**: 4 files
- **Classification**: ~15 files
- **Total**: ~33 files

### Folders to Remove
- `triage/`
- `legacy_metrics/`
- `legacy_experiments/`
- `backbones/`
- `data_loaders/`
- `classification/`
- All `__pycache__/` folders

### Import Updates Needed
- **Legacy**: 4 files (known)
- **Backbones**: TBD (search needed)
- **Data loaders**: TBD (search needed)
- **Classification**: TBD (search needed)
- **Estimated**: 10-15 files total

---

## ⚠️ Risks & Mitigation

### Risk 1: Breaking Imports
**Mitigation**: 
- Search all imports before moving
- Update systematically
- Test after each phase

### Risk 2: External Dependencies
**Mitigation**:
- Check if any external code imports these modules
- Consider deprecation warnings if needed

### Risk 3: Git History
**Mitigation**:
- Use `git mv` instead of `mv` to preserve history
- Commit each phase separately

---

## 🚀 Execution Strategy

### Option A: All at Once (Faster, Riskier)
1. Move all files
2. Update all imports
3. Clean __pycache__
4. Test
5. Commit

**Time**: 30-45 minutes  
**Risk**: High (many changes at once)

### Option B: Phased (Slower, Safer) ✅ RECOMMENDED
1. **Phase 1**: Legacy code only
   - Move, update imports, test, commit
2. **Phase 2**: Core modules
   - Move one at a time, update imports, test, commit
3. **Phase 3**: Clean __pycache__
   - Remove, commit

**Time**: 60-90 minutes  
**Risk**: Low (incremental, testable)

---

## ✨ Benefits

1. **Clearer Organization**: Related code grouped together
2. **Better Discoverability**: Logical folder structure
3. **Easier Maintenance**: Legacy code isolated
4. **Cleaner Git**: No __pycache__ tracking
5. **Follows Conventions**: Numbered pipeline stages contain related code

---

## 📝 Next Steps

1. Review this plan
2. Choose execution strategy (A or B)
3. Run import search commands
4. Execute migration
5. Test thoroughly
6. Commit and push

**Ready to execute when approved!**