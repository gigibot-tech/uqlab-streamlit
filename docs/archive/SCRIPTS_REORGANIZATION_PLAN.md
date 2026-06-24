# Scripts Folder Reorganization Plan

**Date**: 2026-06-21  
**Principle**: Folders shouldn't have 1-4 files, they should be grouped

## Current Structure Analysis

```
scripts/
├── Root level (11 Python files + 7 shell scripts)
├── diagnostics/ (subfolder - need to check)
├── examples/ (subfolder - need to check)
├── fixes/ (7 files - migration/fix scripts)
├── legacy/ (6 files - old analysis scripts)
├── maintenance/ (subfolder - need to check)
├── shell/ (3 files - shell scripts)
└── utils/ (4 files - analysis/visualization)
```

## File Categorization

### 1. **Experiment Runners** (Active, frequently used)
These are the main entry points for running experiments:
- `run_fast_uncertainty_classification.py` ⭐ (1,460 lines - main runner)
- `run_experiment_facade.py` (new facade-based runner)
- `run_fast.py` (alternative runner)
- `train.py` (training script)
- `run_paper_benchmarks.py` (benchmark runner)
- `run_validation_experiments.py` (validation runner)

**Recommendation**: Create `runners/` folder

### 2. **Setup/Download Scripts** (Infrastructure)
- `download_cifar10n.py` (dataset download)
- `calculate_ude_scores.py` (metric calculation)
- `generate_thesis_diagram.py` (visualization generation)
- `validate_architectures.py` (architecture validation)
- `report_unified.py` (reporting)

**Recommendation**: Keep at root or move to `setup/`

### 3. **Deployment Scripts** (DevOps)
- `ce-deploy.sh` (Code Engine deployment)
- `oc-deploy.sh` (OpenShift deployment)
- `generate-client.sh` (client generation)

**Recommendation**: Create `deployment/` folder

### 4. **Shell Scripts** (Currently in `shell/`)
- `test_api.sh`
- `run_streamlit.sh`
- `run_streamlit_modular.sh`

**Recommendation**: Merge into `deployment/` or keep as `shell/`

### 5. **Maintenance Scripts**
- `archive_dead_code.sh` (archiving)
- `fix_validation_system.sh` (system fixes)
- `quick_test.sh` (testing)

**Recommendation**: Move to `maintenance/` folder

### 6. **Fix Scripts** (Currently in `fixes/` - 7 files)
Migration and import fix scripts - likely one-time use
- `fix_numbered_imports.py`
- `update_imports.py`
- `fix_imports.py`
- `fix_shim_imports.py`
- `fix_missing_returns.sh`
- `fix_python314_complete.sh`
- `fix_all_reruns.py`

**Recommendation**: Archive to `dead_code/scripts_fixes/` (one-time migration scripts)

### 7. **Legacy Scripts** (Currently in `legacy/` - 6 files)
Old analysis scripts no longer used
- `check_batch_data.py`
- `analyze_results.py`
- `validate_config_changes.py`
- `analyze_validation_results.py`
- `export_to_watsonx.py`
- `add_method_comparison_plots.py`

**Recommendation**: Archive to `dead_code/scripts_legacy/`

### 8. **Utility Scripts** (Currently in `utils/` - 4 files)
Analysis and visualization utilities
- `dependency_visualizer.py`
- `visualize_7x2_structure.py`
- `analyze_dependencies.py`
- `run_dependency_analysis.sh`

**Recommendation**: Keep as `utils/` or merge into `maintenance/`

## Proposed New Structure

```
scripts/
├── README.md (updated with new structure)
│
├── runners/ (6 files - main experiment runners)
│   ├── run_fast_uncertainty_classification.py ⭐
│   ├── run_experiment_facade.py
│   ├── run_fast.py
│   ├── train.py
│   ├── run_paper_benchmarks.py
│   └── run_validation_experiments.py
│
├── setup/ (5 files - setup and infrastructure)
│   ├── download_cifar10n.py
│   ├── calculate_ude_scores.py
│   ├── generate_thesis_diagram.py
│   ├── validate_architectures.py
│   └── report_unified.py
│
├── deployment/ (6 files - deployment and shell scripts)
│   ├── ce-deploy.sh
│   ├── oc-deploy.sh
│   ├── generate-client.sh
│   ├── test_api.sh
│   ├── run_streamlit.sh
│   └── run_streamlit_modular.sh
│
├── maintenance/ (7 files - maintenance and utilities)
│   ├── archive_dead_code.sh
│   ├── fix_validation_system.sh
│   ├── quick_test.sh
│   ├── dependency_visualizer.py
│   ├── visualize_7x2_structure.py
│   ├── analyze_dependencies.py
│   └── run_dependency_analysis.sh
│
├── diagnostics/ (keep if has 5+ files)
├── examples/ (keep if has 5+ files)
└── [other subfolders to be checked]
```

## Archive to dead_code/

```
dead_code/
├── scripts_fixes/ (7 files - one-time migration scripts)
│   ├── fix_numbered_imports.py
│   ├── update_imports.py
│   ├── fix_imports.py
│   ├── fix_shim_imports.py
│   ├── fix_missing_returns.sh
│   ├── fix_python314_complete.sh
│   └── fix_all_reruns.py
│
└── scripts_legacy/ (6 files - old analysis scripts)
    ├── check_batch_data.py
    ├── analyze_results.py
    ├── validate_config_changes.py
    ├── analyze_validation_results.py
    ├── export_to_watsonx.py
    └── add_method_comparison_plots.py
```

## Benefits

1. **Clear Purpose**: Each folder has a clear, single purpose
2. **Easy Discovery**: Users can quickly find the right script
3. **Reduced Clutter**: Archive old/one-time scripts
4. **Better Organization**: Group related scripts together
5. **Follows Principle**: No folders with 1-4 files (except well-justified ones)

## Metrics

### Before
- **Root level files**: 18 files (too many!)
- **Small folders**: `shell/` (3 files), `utils/` (4 files)
- **Archive candidates**: `fixes/` (7 files), `legacy/` (6 files)

### After
- **Root level files**: 1 (README.md only)
- **Organized folders**: 4 main folders (runners, setup, deployment, maintenance)
- **Archived**: 13 files moved to dead_code
- **Average files per folder**: 6 files (healthy size)

## Implementation Steps

1. ✅ Create this plan
2. ⏳ Check `diagnostics/`, `examples/`, `maintenance/` subfolders
3. ⏳ Create new folder structure
4. ⏳ Move files to appropriate folders
5. ⏳ Archive fixes/ and legacy/ to dead_code
6. ⏳ Update README.md with new structure
7. ⏳ Test that scripts still work from new locations
8. ⏳ Commit and push changes

## Questions to Answer

1. What's in `diagnostics/` folder?
2. What's in `examples/` folder?
3. What's in `maintenance/` folder?
4. Are there any scripts that import from each other? (need to update imports)
5. Are there any documentation references to script paths? (need to update)