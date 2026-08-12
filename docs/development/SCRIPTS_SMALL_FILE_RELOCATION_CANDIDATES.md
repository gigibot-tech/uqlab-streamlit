# Scripts Folder: Small-File Relocation Candidates

**Scope**: `scripts/` root folder and its immediate subdirectories.  
**Goal**: Identify files below 200/300 lines of code (LoC) and determine whether they can be consolidated, relocated, or removed.  
**Date**: 2026-08-12  
**Branch**: `cursor/small-file-relocation-candidates-d265`

---

## Methodology

- LoC measured as physical lines (`wc -l`) including comments and blanks, because small files are often wrappers or placeholders where every line matters for readability.
- Thresholds:
  - **< 200 LoC**: small files that are easy relocation candidates.
  - **200–300 LoC**: borderline files that may still be candidates if they share a theme with smaller neighbours.
- Excluded `__pycache__` contents except where a compiled byte-code file is accidentally tracked by git.

## Current `scripts/` Structure

```
scripts/
├── README.md                              (636 LoC — deployment guide, not a folder index)
├── migrate_to_uqlab_core.py               (134 LoC — maintenance/migration)
├── regenerate_shims.py                    (48 LoC — maintenance/shim utility)
├── __pycache__/
│   └── run_fast_uncertainty_classification.cpython-314.pyc   (189 LoC tracked — should not be in git)
├── analysis/
│   ├── analyze_my_run.py                  (397 LoC)
│   ├── disentanglement_error.py           (274 LoC)
│   ├── four_region_validation.py          (90 LoC)
│   ├── paper_benchmarks.py                (105 LoC)
│   ├── plot_run_region_means.py           (114 LoC)
│   └── README.md                          (144 LoC)
├── deployment/
│   ├── ce-deploy.sh                       (633 LoC)
│   ├── generate-client.sh                 (13 LoC)
│   ├── oc-deploy.sh                       (253 LoC)
│   ├── run_streamlit_modular.sh           (16 LoC)
│   ├── run_streamlit.sh                   (41 LoC)
│   └── test_api.sh                        (58 LoC)
├── examples/
│   ├── example_batch_sweep.py             (233 LoC)
│   ├── example_cnn.py                     (118 LoC)
│   ├── example_dinov2.py                  (103 LoC)
│   ├── example_resnet.py                  (130 LoC)
│   ├── minimal_experiment.py              (220 LoC)
│   └── README.md                          (270 LoC)
├── lib/
│   ├── 00-common.sh                       (305 LoC)
│   ├── 10-validation.sh                   (102 LoC)
│   ├── 20-environment.sh                  (447 LoC)
│   ├── 30-openshift.sh                    (115 LoC)
│   ├── 40-ssh.sh                          (246 LoC)
│   ├── 50-secrets.sh                      (171 LoC)
│   ├── 60-database.sh                     (240 LoC)
│   ├── 70-deployment.sh                   (243 LoC)
│   ├── 75-oauth.sh                        (333 LoC)
│   └── 80-webhooks.sh                     (195 LoC)
├── maintenance/
│   ├── analyze_dependencies.py            (532 LoC)
│   ├── archive_dead_code.sh               (202 LoC)
│   ├── cleanup_root_level.sh              (88 LoC)
│   ├── cleanup.sh                         (25 LoC)
│   ├── consolidate_uq_classification.py   (206 LoC)
│   ├── dependency_visualizer.py           (652 LoC)
│   ├── diagnose_rerun.py                  (80 LoC)
│   ├── diagnose_startup.py                (86 LoC)
│   ├── fix_validation_system.sh           (85 LoC)
│   ├── quick_test.sh                      (85 LoC)
│   ├── remove_ui_debug.py                 (80 LoC)
│   ├── remove_walaris_references.py       (80 LoC)
│   ├── rename_to_uqlab.sh                 (375 LoC)
│   ├── reorganize_folders.sh              (38 LoC)
│   ├── run_dependency_analysis.sh         (35 LoC)
│   ├── run_pipeline_tests.sh              (14 LoC)
│   └── visualize_7x2_structure.py       (0 LoC)
├── runners/
│   ├── run_fast.py                        (17 LoC)
│   ├── run_fast_uncertainty_classification.py (57 LoC)
│   └── run_validation_experiments.py      (643 LoC)
├── setup/
│   ├── calculate_ude_scores.py            (309 LoC)
│   ├── download_cifar10n.py                 (40 LoC)
│   ├── generate_campaign_config_timeline.py (124 LoC)
│   ├── generate_campaign_report.py          (117 LoC)
│   ├── generate_thesis_diagram.py           (140 LoC)
│   ├── report_unified.py                    (76 LoC)
│   └── validate_architectures.py            (60 LoC)
└── validate_per_class_campaign.py         (596 LoC)   ← also at root level
```

**Observations**:
- The folder reorganization described in `docs/archive/SCRIPTS_REORGANIZATION_COMPLETE.md` has drifted: a new `analysis/` subfolder exists, `runners/` only has 3 files instead of 6, and the root still holds loose files (`README.md`, `validate_per_class_campaign.py`).
- `scripts/README.md` is 636 lines but is actually an OpenShift deployment guide, not a scripts-folder index. It is misnamed/placed.

---

## Files < 200 LoC

| File | LoC | Current Folder | Recommendation | Rationale |
|------|-----|----------------|----------------|-----------|
| `maintenance/visualize_7x2_structure.py` | 0 | maintenance | **Delete** | Empty placeholder; referenced only in old reorganization plans. |
| `__pycache__/run_fast_uncertainty_classification.cpython-314.pyc` | 189 | `__pycache__` | **Delete from git** | Compiled Python cache; `.gitignore` already excludes `__pycache__/`. |
| `deployment/generate-client.sh` | 13 | deployment | Keep or merge | One-time client-generation task; too small to split further. Could merge into a `deployment/dev-tasks.sh` if more tiny tasks appear. |
| `deployment/run_streamlit_modular.sh` | 16 | deployment | Keep or merge | Thin launcher. Could be merged with `run_streamlit.sh` into a single entry script with a `--modular` flag. |
| `runners/run_fast.py` | 17 | runners | Keep | Documented wrapper around `run_fast_uncertainty_classification.py`; removing it would break docs. Could be moved to root as `run_fast.py` if it is the canonical CLI entry. |
| `maintenance/cleanup.sh` | 25 | maintenance | Keep or merge | Small focused cleanup script. Could be merged into `cleanup_root_level.sh` if their scopes overlap. |
| `maintenance/run_pipeline_tests.sh` | 14 | maintenance | Keep or merge | Tiny wrapper. Could become a `maintenance/quick-tasks.sh` subcommand. |
| `maintenance/run_dependency_analysis.sh` | 35 | maintenance | Keep or merge | Thin wrapper around `analyze_dependencies.py`. Could be merged into `maintenance/common-tasks.sh`. |
| `maintenance/reorganize_folders.sh` | 38 | maintenance | Keep or merge | One-time reorganization script; if already run, consider archiving. |
| `setup/download_cifar10n.py` | 40 | setup | Keep | Focused one-shot downloader; clear purpose. |
| `deployment/run_streamlit.sh` | 41 | deployment | Keep | Thin launcher; related to `run_streamlit_modular.sh`. |
| `regenerate_shims.py` | 48 | **scripts root** | **Move to `maintenance/`** | Shim-regeneration utility is a maintenance task; no external references by path. |
| `deployment/test_api.sh` | 58 | deployment | Keep | Focused smoke-test script. |
| `setup/validate_architectures.py` | 60 | setup | Keep | Focused validation utility. |
| `setup/report_unified.py` | 76 | setup | Keep or merge | Small report generator; could merge with `generate_campaign_report.py` if they share output format. |
| `maintenance/diagnose_rerun.py` | 80 | maintenance | Keep | Focused diagnostic script. |
| `maintenance/remove_ui_debug.py` | 80 | maintenance | Keep | Focused cleanup script. |
| `maintenance/remove_walaris_references.py` | 80 | maintenance | Keep | Focused cleanup script. |
| `maintenance/diagnose_startup.py` | 86 | maintenance | Keep | Focused diagnostic script. |
| `maintenance/cleanup_root_level.sh` | 88 | maintenance | Keep | Focused cleanup script. |
| `maintenance/fix_validation_system.sh` | 85 | maintenance | Keep | Focused fix script. |
| `maintenance/quick_test.sh` | 85 | maintenance | Keep | Focused quick-test wrapper. |
| `analysis/four_region_validation.py` | 90 | analysis | Keep | Focused analysis script. |
| `examples/example_dinov2.py` | 103 | examples | Keep | Clear example. |
| `examples/example_resnet.py` | 130 | examples | Keep | Clear example. |
| `examples/example_cnn.py` | 118 | examples | Keep | Clear example. |
| `analysis/paper_benchmarks.py` | 105 | analysis | Keep | Focused analysis script. |
| `analysis/plot_run_region_means.py` | 114 | analysis | Keep | Focused analysis script. |
| `lib/10-validation.sh` | 102 | lib | Keep | Library module with clear responsibility. |
| `lib/30-openshift.sh` | 115 | lib | Keep | Library module with clear responsibility. |
| `setup/generate_campaign_report.py` | 117 | setup | Keep | Clear report generator. |
| `setup/generate_campaign_config_timeline.py` | 124 | setup | Keep | Clear generator. |
| `setup/generate_thesis_diagram.py` | 140 | setup | Keep | Clear generator. |
| `analysis/README.md` | 144 | analysis | Keep | Subfolder documentation. |
| `lib/50-secrets.sh` | 171 | lib | Keep | Library module with clear responsibility. |
| `lib/80-webhooks.sh` | 195 | lib | Keep | Library module with clear responsibility. |
| `migrate_to_uqlab_core.py` | 134 | **scripts root** | **Move to `maintenance/`** (or archive) | One-shot migration; belongs with maintenance scripts. If already executed, archive to `dead_code/` when that folder is reintroduced. |
| `validate_per_class_campaign.py` | 596 | **scripts root** | **Move to `analysis/` or `runners/`** | Large root-level script; at minimum it should leave the root. Likely belongs in `analysis/` (campaign validation) or `runners/` (campaign runner). |

## Files 200–300 LoC (Borderline)

| File | LoC | Current Folder | Recommendation | Rationale |
|------|-----|----------------|----------------|-----------|
| `maintenance/archive_dead_code.sh` | 202 | maintenance | Keep | Just above threshold; clear purpose. |
| `maintenance/consolidate_uq_classification.py` | 206 | maintenance | Keep | Migration script; could be archived once uqlab classification consolidation is complete. |
| `examples/example_batch_sweep.py` | 233 | examples | Keep | Reasonable example size. |
| `examples/minimal_experiment.py` | 220 | examples | Keep | Reasonable example size. |
| `lib/40-ssh.sh` | 246 | lib | Keep | Library module. |
| `lib/60-database.sh` | 240 | lib | Keep | Library module. |
| `lib/70-deployment.sh` | 243 | lib | Keep | Library module. |
| `analysis/disentanglement_error.py` | 274 | analysis | Keep | Analysis script. |
| `deployment/oc-deploy.sh` | 253 | deployment | Keep | Deployment script. |

---

## Immediate Safe Actions (Done on this Branch)

These changes are low-risk because the files are either clearly misplaced, empty, or tracked artifacts that should never have been committed.

1. ✅ **Moved `scripts/migrate_to_uqlab_core.py` → `scripts/maintenance/migrate_to_uqlab_core.py`**
   - One-shot migration utility; co-located with other maintenance scripts.
   - No path-based references found in the repo.

2. ✅ **Moved `scripts/regenerate_shims.py` → `scripts/maintenance/regenerate_shims.py`**
   - Shim-regeneration utility; co-located with migration/maintenance tools.
   - No path-based references found in the repo.

3. ✅ **Deleted `scripts/maintenance/visualize_7x2_structure.py`**
   - Empty file; only referenced in old reorganization plans.

4. ✅ **Deleted `scripts/__pycache__/run_fast_uncertainty_classification.cpython-314.pyc` from git**
   - `.gitignore` already excludes `__pycache__/`. Compiled artifacts should not be tracked.

5. **Move `scripts/validate_per_class_campaign.py` → `scripts/analysis/validate_per_class_campaign.py`** (recommended, not done)
   - Root-level campaign validator; `analysis/` is the most semantically appropriate existing folder.
   - Verify no external workflow references this path before moving.

## Riskier / Deferred Candidates

These require more validation before acting.

- **`scripts/README.md`**: rename to `scripts/deployment/README.md` or `scripts/lib/README.md` and create a real `scripts/README.md` that indexes the folder. Risk: external links may point to the current path.
- **`scripts/runners/run_fast.py`**: remove if the wrapper is redundant, or keep as the canonical CLI alias. Risk: documented in `docs/features/disentanglement-benchmark.md`.
- **`deployment/run_streamlit.sh` + `deployment/run_streamlit_modular.sh`**: merge into a single launcher with a flag. Risk: muscle memory / CI references.
- **`maintenance/cleanup.sh` + `maintenance/cleanup_root_level.sh`**: merge if scopes overlap. Risk: subtle differences in cleanup targets.
- **Tiny maintenance wrappers (`run_pipeline_tests.sh`, `run_dependency_analysis.sh`, `reorganize_folders.sh`)**: merge into a `maintenance/common-tasks.sh` menu. Risk: discoverability.

---

## Summary

- **38 files** in `scripts/` are under 200 LoC; **8 more** are in the 200–300 LoC borderline range.
- The most actionable low-risk moves are the **2 loose root-level maintenance scripts** (`migrate_to_uqlab_core.py`, `regenerate_shims.py`) and the **2 broken artifacts** (empty `visualize_7x2_structure.py` and tracked `.pyc`), which were performed on this branch. The remaining root-level script `validate_per_class_campaign.py` is a recommended next move.
- Most small files are *appropriately small* because they are focused launchers, diagnostics, or examples. They should generally stay where they are unless they can be merged with a sibling without losing clarity.
- The folder structure has drifted from the earlier `SCRIPTS_REORGANIZATION_COMPLETE.md` snapshot; this report provides a current baseline for the next round of consolidation.
