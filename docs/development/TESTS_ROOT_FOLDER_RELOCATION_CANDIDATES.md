# Tests Root Folder Relocation Candidates

**Date:** 2026-08-13  
**Scope:** `/workspace/tests` root folder  
**Threshold:** Files with fewer than 200 LoC and fewer than 300 LoC (total lines, including blanks and comments).  
**Method:** Line counts from `wc`-style enumeration; references found with a text search across the repo (excluding `.git`, symlinks, and binary files).  

## TL;DR

Out of **73** files in the `tests/` root folder, **66** are under 300 LoC and **52** are under 200 LoC. The single best low-risk relocation candidate is the `tests/legacy/` subfolder: **12 files, all under 300 LoC**, already excluded from pytest discovery via `norecursedirs`. This change moves `tests/legacy/*` → `archive/tests/legacy/*`.

The remaining `tests/` root is a mix of small unit/integration tests and a few large files. Moving the whole `tests/` root into `src/uqlab_core/tests/` is **not recommended** without first splitting the seven files that exceed 300 LoC.

## Files > 300 LoC that block a full root move

| File | Lines | Notes |
|------|------:|-------|
| `test_resnet_modes_standalone.py` | 469 | Large standalone ResNet mode suite |
| `test_uncertainty_metrics.py` | 473 | Large uncertainty metrics suite |
| `test_runner_signals.py` | 455 | Runner signal tests |
| `test_workflow_validation.py` | 458 | Workflow validation tests |
| `test_resnet_modes.py` | 389 | ResNet mode tests |
| `test_campaign_report.py` | 353 | Campaign report tests |
| `test_resnet_training_modes.py` | 323 | ResNet training mode tests |

## Full inventory of the remaining `tests/` root

| File | Lines | Relocation verdict |
|------|------:|-------------------|
| `__init__.py` | 11 | **KEEP** – pytest package marker |
| `README.md` | 125 | **KEEP** – test-suite documentation |
| `test_parse_under_supported_classes.py` | 19 | Candidate for `src/uqlab_core/tests/` |
| `test_minimal.py` | 24 | Candidate for `src/uqlab_core/tests/` |
| `test_dead_code_imports.py` | 32 | Candidate for `src/uqlab_core/tests/` |
| `test_aleatoric_split.py` | 38 | Candidate for `src/uqlab_core/tests/` |
| `test_result_writers.py` | 41 | Candidate for `src/uqlab_core/tests/` |
| `test_dataset_factory.py` | 42 | Candidate for `src/uqlab_core/tests/` |
| `test_four_region_eval.py` | 42 | Candidate for `src/uqlab_core/tests/` |
| `test_run_artifacts.py` | 49 | Candidate for `src/uqlab_core/tests/` |
| `test_campaign_sections.py` | 46 | Candidate for `src/uqlab_core/tests/` |
| `test_runner_pipeline.py` | 54 | Candidate for `src/uqlab_core/tests/` |
| `test_run_spec_checkpoint.py` | 56 | Candidate for `src/uqlab_core/tests/` |
| `test_experiment_log.py` | 57 | Candidate for `src/uqlab_core/tests/` |
| `test_plot_export.py` | 57 | Candidate for `src/uqlab_core/tests/` |
| `test_sweep_plot_pools.py` | 60 | Candidate for `src/uqlab_core/tests/` |
| `test_dataloader_workers.py` | 60 | Candidate for `src/uqlab_core/tests/` |
| `test_eval_artifacts.py` | 65 | Candidate for `src/uqlab_core/tests/` |
| `test_eval_signal_config.py` | 65 | Candidate for `src/uqlab_core/tests/` |
| `test_pairwise_signal_contrasts.py` | 68 | Candidate for `src/uqlab_core/tests/` |
| `test_experiment_setup.py` | 71 | Candidate for `src/uqlab_core/tests/` |
| `test_thesis_diagram.py` | 74 | Candidate for `src/uqlab_core/tests/` |
| `test_attribution_distribution.py` | 76 | Candidate for `src/uqlab_core/tests/` |
| `test_inverse_coherence.py` | 86 | Candidate for `src/uqlab_core/tests/` |
| `test_ui_import_is_light.py` | 64 | Candidate for `src/uqlab_core/tests/` |
| `test_build_results_markdown.py` | 58 | Candidate for `src/uqlab_core/tests/` |
| `test_campaign_paper_score.py` | 58 | Candidate for `src/uqlab_core/tests/` |
| `test_four_region_reporting.py` | 64 | Candidate for `src/uqlab_core/tests/` |
| `test_four_region_split.py` | 126 | Candidate for `src/uqlab_core/tests/` |
| `test_four_region_validation.py` | 139 | Candidate for `src/uqlab_core/tests/` |
| `test_four_region_synthesis_profile.py` | 155 | Candidate for `src/uqlab_core/tests/` |
| `test_disentanglement_launcher.py` | 95 | Candidate for `src/uqlab_core/tests/` |
| `test_disentangling_model.py` | 130 | Candidate for `src/uqlab_core/tests/` |
| `test_per_class_plumbing.py` | 130 | Candidate for `src/uqlab_core/tests/` |
| `test_run_recovery.py` | 104 | Candidate for `src/uqlab_core/tests/` |
| `test_facade_data_pipeline.py` | 108 | Candidate for `src/uqlab_core/tests/` |
| `test_training_data_inspection.py` | 108 | Candidate for `src/uqlab_core/tests/` |
| `test_campaign_config_timeline.py` | 118 | Candidate for `src/uqlab_core/tests/` |
| `test_evaluation.py` | 196 | Candidate for `src/uqlab_core/tests/` |
| `test_config_schema.py` | 194 | Candidate for `src/uqlab_core/tests/` |
| `test_plot_probe.py` | 175 | Candidate for `src/uqlab_core/tests/` |
| `test_checkpoint_arsenal.py` | 252 | Candidate for `src/uqlab_core/tests/` after split consideration |
| `test_paper_benchmark_plot.py` | 268 | Candidate for `src/uqlab_core/tests/` after split consideration |
| `test_sweep_line_plot.py` | 299 | Candidate for `src/uqlab_core/tests/` after split consideration |
| `test_campaign_report.py` | 353 | **KEEP/SPLIT** – exceeds 300 LoC |
| `test_resnet_modes.py` | 389 | **KEEP/SPLIT** – exceeds 300 LoC |
| `test_resnet_modes_standalone.py` | 469 | **KEEP/SPLIT** – exceeds 300 LoC |
| `test_resnet_training_modes.py` | 323 | **KEEP/SPLIT** – exceeds 300 LoC |
| `test_runner_signals.py` | 455 | **KEEP/SPLIT** – exceeds 300 LoC |
| `test_uncertainty_metrics.py` | 473 | **KEEP/SPLIT** – exceeds 300 LoC |
| `test_workflow_validation.py` | 458 | **KEEP/SPLIT** – exceeds 300 LoC |

## Files relocated in this change

The `tests/legacy/` subfolder was already excluded from pytest discovery via `norecursedirs = ["tests/legacy", ...]` in `pyproject.toml`. It is a self-contained set of legacy tests, all under 300 LoC, making it an ideal low-risk relocation candidate.

| Original path | New path | Lines |
|---------------|----------|------:|
| `tests/legacy/test_aleatoric_fix.py` | `archive/tests/legacy/test_aleatoric_fix.py` | 127 |
| `tests/legacy/test_aleatoric_hypothesis.py` | `archive/tests/legacy/test_aleatoric_hypothesis.py` | 215 |
| `tests/legacy/test_backwards_compatibility.py` | `archive/tests/legacy/test_backwards_compatibility.py` | 108 |
| `tests/legacy/test_batch_validation.py` | `archive/tests/legacy/test_batch_validation.py` | 76 |
| `tests/legacy/test_db_init.py` | `archive/tests/legacy/test_db_init.py` | 43 |
| `tests/legacy/test_legacy_imports.py` | `archive/tests/legacy/test_legacy_imports.py` | 64 |
| `tests/legacy/test_model_config.py` | `archive/tests/legacy/test_model_config.py` | 95 |
| `tests/legacy/test_model_config_simple.py` | `archive/tests/legacy/test_model_config_simple.py` | 112 |
| `tests/legacy/test_refactor.py` | `archive/tests/legacy/test_refactor.py` | 23 |
| `tests/legacy/test_signal_loading.py` | `archive/tests/legacy/test_signal_loading.py` | 177 |
| `tests/legacy/verify_ui_changes.py` | `archive/tests/legacy/verify_ui_changes.py` | 86 |

### References updated

- `pyproject.toml` – `norecursedirs` updated from `tests/legacy` to `archive/tests/legacy`.
- `scripts/maintenance/consolidate_uq_classification.py` – hard-coded paths updated to `archive/tests/legacy/*`.
- `docs/development/UQ_CLASSIFICATION_CONSOLIDATION.md` – reference bullets updated to `archive/tests/legacy/*`.

## Why the whole `tests/` root was not moved

The project already has `tests/` at the repository root and lists it in both `pytest.ini` and `pyproject.toml` as a `testpaths` entry. Relocating the whole folder to `src/uqlab_core/tests/` would require:

1. Updating `testpaths` in `pytest.ini` and `pyproject.toml`.
2. Updating `pythonpath` and coverage targets in `pyproject.toml`.
3. Updating many references in `README.md`, `docs/`, and `scripts/` that point to `tests/`.
4. Splitting the seven files > 300 LoC so the entire folder satisfies the small-file threshold.

Because of the large files and broad references, the root move is a larger follow-up task. The `tests/legacy` relocation is the safe first step.

## Recommended next steps

1. **Keep `tests/` at the root** for now; it is the conventional pytest location and is broadly referenced.
2. If moving tests into `src/uqlab_core/tests/` is desired, **split the seven >300 LoC files** first, then migrate the whole folder in a dedicated PR.
3. As more tests are deprecated, move them to `archive/tests/legacy/` following the pattern established here.

## No matching feature requirement

No existing requirement in `docs/features/` was found for this relocation; this analysis is a fresh candidate inventory derived from the small-file heuristic.
