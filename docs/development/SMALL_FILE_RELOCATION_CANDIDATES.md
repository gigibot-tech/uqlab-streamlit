# Small File Relocation Candidates — `scripts/` Root Folder

**Branch**: `cursor/small-file-relocation-candidates-6beb`  
**Date**: 2026-07-24  
**Scope**: Top-level `scripts/` directory and its immediate sub-folders.

## TL;DR

- **36 files** in `scripts/` are under **300 LoC** (≈76% of all tracked script files).
- **27 files** are under **200 LoC**.
- Most small files are already in well-named sub-folders (`runners/`, `setup/`, `analysis/`, `examples/`, `lib/`, `deployment/`, `maintenance/`).
- A few files are **empty, broken, or one-time migration helpers** and were relocated during this pass.

## Method

Line counts were collected for all non-`__pycache__` files under `scripts/`:

```bash
cd /workspace
find scripts -type f \( -name '*.py' -o -name '*.sh' \) -exec wc -l {} + | sort -n
```

Thresholds used: **< 200 LoC** and **< 300 LoC**. Files over 300 LoC are treated as large enough to keep where they are unless there is a strong structural reason to move them.

## Summary of `scripts/` structure

| Sub-folder | Files | Under 300 LoC | Notes |
|------------|-------|---------------|-------|
| `analysis/` | 5 | 4 | Post-hoc experiment analysis; correctly grouped. |
| `deployment/` | 6 → 4 | 3 → 2 | Deployment & launch scripts; two broken ones archived. |
| `examples/` | 5 | 5 | Example experiment scripts; correctly grouped. |
| `lib/` | 10 | 8 | Shared shell library; correctly grouped. |
| `maintenance/` | 15 → 14 | 13 | Maintenance, migration, cleanup; one empty file removed. |
| `runners/` | 3 | 2 | Experiment entry points; small but canonical. |
| `setup/` | 7 | 7 | Setup & report generation; correctly grouped. |
| `archive/` | 0 → 2 | 2 | New: holds broken/legacy scripts. |

## Files under 200 LoC

| File | LoC | Current role | Relocation verdict |
|------|-----|--------------|-------------------|
| `scripts/deployment/generate-client.sh` | 13 | Generate frontend API client | **Archived** — references `frontend/` which does not exist in this repo. |
| `scripts/maintenance/run_pipeline_tests.sh` | 14 | Run a subset of campaign tests | Keep — actively used by CI/tests. |
| `scripts/runners/run_fast.py` | 17 | Thin wrapper around `run_fast_uncertainty_classification.py` | Keep for now — wrapper is referenced in docs; could be merged later. |
| `scripts/maintenance/cleanup.sh` | 25 | Remove `__pycache__` and empty legacy dirs | Keep — ongoing maintenance. |
| `scripts/maintenance/run_dependency_analysis.sh` | 35 | Kick off dependency analysis | Keep — pairs with `analyze_dependencies.py` / `dependency_visualizer.py`. |
| `scripts/maintenance/reorganize_folders.sh` | 38 | One-time legacy folder reorg | **Candidate** — migration helper; could be archived. |
| `scripts/setup/download_cifar10n.py` | 40 | Download noisy CIFAR-10 dataset | Keep — setup task. |
| `scripts/deployment/run_streamlit.sh` | 41 | Start the main Streamlit app | Keep — active deployment script. |
| `scripts/regenerate_shims.py` | 48 | Regenerate `uqlab` → `uqlab_core` import shims | Keep — migration helper still relevant. |
| `scripts/runners/run_fast_uncertainty_classification.py` | 57 | Canonical CLI runner | Keep — primary entry point. |
| `scripts/deployment/test_api.sh` | 58 | Health-check backend API | Keep — active deployment script. |
| `scripts/setup/validate_architectures.py` | 60 | Validate model architecture configs | Keep — setup task. |
| `scripts/setup/report_unified.py` | 76 | Generate unified report | Keep — setup task. |
| `scripts/maintenance/diagnose_rerun.py` | 80 | Streamlit rerun diagnostic | Keep — could later merge with `diagnose_startup.py`. |
| `scripts/maintenance/remove_walaris_references.py` | 80 | Remove old `walaris` strings | Keep — cleanup utility. |
| `scripts/maintenance/fix_validation_system.sh` | 85 | Fix validation setup | Keep — maintenance utility. |
| `scripts/maintenance/quick_test.sh` | 85 | Quick smoke test | Keep — maintenance utility. |
| `scripts/maintenance/diagnose_startup.py` | 86 | Streamlit startup diagnostic | Keep — could later merge with `diagnose_rerun.py`. |
| `scripts/maintenance/cleanup_root_level.sh` | 88 | Root-level cleanup helper | Keep — one-time but still useful; references existing cleanup plan. |
| `scripts/analysis/four_region_validation.py` | 90 | Validate four-region experiment | Keep — belongs in `analysis/`. |
| `scripts/maintenance/remove_ui_debug.py` | 93 | Remove UI debug blocks | Keep — maintenance utility. |
| `scripts/lib/10-validation.sh` | 102 | Shell lib: validation helpers | Keep — library script. |
| `scripts/examples/example_dinov2.py` | 103 | DINOv2 example | Keep — belongs in `examples/`. |
| `scripts/analysis/paper_benchmarks.py` | 105 | Paper benchmark CSV builder | Keep — belongs in `analysis/`. |
| `scripts/analysis/plot_run_region_means.py` | 114 | Plot region means | Keep — belongs in `analysis/`. |
| `scripts/lib/30-openshift.sh` | 115 | Shell lib: OpenShift helpers | Keep — library script. |
| `scripts/setup/generate_campaign_report.py` | 117 | Build campaign PDF report | Keep — setup task. |
| `scripts/examples/example_cnn.py` | 118 | CNN example | Keep — belongs in `examples/`. |
| `scripts/setup/generate_campaign_config_timeline.py` | 124 | Build campaign timeline | Keep — setup task. |
| `scripts/examples/example_resnet.py` | 130 | ResNet example | Keep — belongs in `examples/`. |
| `scripts/migrate_to_uqlab_core.py` | 134 | Migrate experiments to `uqlab_core` | Keep — migration helper still relevant. |
| `scripts/setup/generate_thesis_diagram.py` | 140 | Generate thesis diagram | Keep — setup task. |
| `scripts/lib/50-secrets.sh` | 171 | Shell lib: secret handling | Keep — library script. |

## Files between 200 and 300 LoC

| File | LoC | Current role | Relocation verdict |
|------|-----|--------------|-------------------|
| `scripts/maintenance/archive_dead_code.sh` | 202 | Archive dead code | Keep — active maintenance. |
| `scripts/maintenance/consolidate_uq_classification.py` | 206 | Consolidate UQ classification code | Keep — active maintenance. |
| `scripts/examples/minimal_experiment.py` | 220 | Minimal experiment example | Keep — belongs in `examples/`. |
| `scripts/examples/example_batch_sweep.py` | 233 | Batch sweep example | Keep — belongs in `examples/`. |
| `scripts/lib/60-database.sh` | 240 | Shell lib: database helpers | Keep — library script. |
| `scripts/lib/70-deployment.sh` | 243 | Shell lib: deployment helpers | Keep — library script. |
| `scripts/lib/40-ssh.sh` | 246 | Shell lib: SSH helpers | Keep — library script. |
| `scripts/deployment/oc-deploy.sh` | 253 | OpenShift deployment | Keep — active deployment script. |
| `scripts/analysis/disentanglement_error.py` | 274 | Disentanglement error metric | Keep — belongs in `analysis/`. |

## Files over 300 LoC (not candidates)

These files are large enough that they are not considered small-file relocation candidates:

- `scripts/lib/00-common.sh` (305)
- `scripts/setup/calculate_ude_scores.py` (309)
- `scripts/lib/75-oauth.sh` (333)
- `scripts/maintenance/rename_to_uqlab.sh` (375)
- `scripts/analysis/analyze_my_run.py` (397)
- `scripts/lib/20-environment.sh` (447)
- `scripts/maintenance/analyze_dependencies.py` (532)
- `scripts/validate_per_class_campaign.py` (596)
- `scripts/deployment/ce-deploy.sh` (633)
- `scripts/runners/run_validation_experiments.py` (643)
- `scripts/maintenance/dependency_visualizer.py` (652)

## Actions taken on this branch

1. **Deleted** `scripts/maintenance/visualize_7x2_structure.py` — it was empty (0 LoC) and not imported anywhere.
2. **Created** `scripts/archive/` and moved two broken deployment scripts there:
   - `scripts/deployment/generate-client.sh` → `scripts/archive/generate-client.sh`
   - `scripts/deployment/run_streamlit_modular.sh` → `scripts/archive/run_streamlit_modular.sh`
   
   Both scripts reference directories (`frontend/`, `streamlit_frontend/`) that no longer exist in the repository, so they cannot run in the current layout. Archiving preserves history while removing them from the active deployment path.

## Remaining relocation candidates (recommendations)

| File | Suggested action | Rationale |
|------|------------------|-----------|
| `scripts/maintenance/reorganize_folders.sh` | Move to `scripts/archive/` | One-time migration script; references legacy `src/uqlab/` paths that are already migrated. |
| `scripts/maintenance/diagnose_rerun.py` + `scripts/maintenance/diagnose_startup.py` | Merge into `scripts/maintenance/diagnostics.py` | Both are Streamlit diagnostics; merging reduces 1-4-file-folder risk and keeps related logic together. |
| `scripts/runners/run_fast.py` | Merge into `scripts/runners/run_fast_uncertainty_classification.py` or replace with a `console_scripts` entry point | It is only a 17-line wrapper that calls the canonical runner. |

## What should NOT be moved

- **Files in `scripts/runners/`, `scripts/setup/`, `scripts/analysis/`, `scripts/examples/`, `scripts/lib/`** are already correctly grouped by purpose.
- **`scripts/maintenance/cleanup.sh`, `fix_validation_system.sh`, `quick_test.sh`, `remove_ui_debug.py`, `remove_walaris_references.py`, `archive_dead_code.sh`, `consolidate_uq_classification.py`** are active maintenance utilities and should stay in `maintenance/`.
- **Large deployment scripts (`oc-deploy.sh`, `ce-deploy.sh`)** are substantive enough to remain in `deployment/`.

## Next steps

1. Decide whether to archive `scripts/maintenance/reorganize_folders.sh` and `scripts/maintenance/cleanup_root_level.sh` (both are one-time cleanup helpers).
2. Decide whether to merge the two small diagnostic scripts into a single module.
3. Update `docs/archive/SCRIPTS_REORGANIZATION_PLAN.md` and `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` once final relocations are complete.
