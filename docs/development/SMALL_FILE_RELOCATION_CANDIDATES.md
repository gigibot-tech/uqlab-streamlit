# Small Root-Folder Relocation Candidates

**Date:** 2026-08-08  
**Branch:** `cursor/small-file-relocation-candidates-5e7f`  
**Scope:** Root-level folders whose *immediate* files are below 200–300 lines of code.

## Executive Summary

The following root-level folders have *every* immediate file below the configured LoC thresholds. They are the best candidates for relocation if their dependencies and in-tree references can be updated safely.

### Under 200 LoC

- `configs/` — root max 44 LoC, recursive max 64 LoC; candidate: all root-level YAML presets are small. Could fold into ``src/uqlab_core/configs/`` so presets ship with the package, but ``runtime_paths.configs_dir()``, README, and every CLI/notebook reference must be updated.
- `data/` — root max 0 LoC, recursive max 0 LoC; candidate, but keep at root: ``runtime_paths.data_root()`` defaults to ``<repo>/data``; relocating requires an env override or code change
- `src/` — root max 0 LoC, recursive max 923 LoC; not a candidate: primary package folder, conventionally at root
- `uqlab-flask/` — root max 37 LoC, recursive max 652 LoC; candidate: root-level files are small, but the package underneath is substantial; could move into ``backend/``, ``frontend/``, or a new ``ui/`` folder

### Under 300 LoC

- `configs/` — root max 44 LoC, recursive max 64 LoC; candidate: all root-level YAML presets are small. Could fold into ``src/uqlab_core/configs/`` so presets ship with the package, but ``runtime_paths.configs_dir()``, README, and every CLI/notebook reference must be updated.
- `data/` — root max 0 LoC, recursive max 0 LoC; candidate, but keep at root: ``runtime_paths.data_root()`` defaults to ``<repo>/data``; relocating requires an env override or code change
- `src/` — root max 0 LoC, recursive max 923 LoC; not a candidate: primary package folder, conventionally at root
- `uqlab-flask/` — root max 37 LoC, recursive max 652 LoC; candidate: root-level files are small, but the package underneath is substantial; could move into ``backend/``, ``frontend/``, or a new ``ui/`` folder

## Methodology

For each folder directly under the repository root we count two things:

1. **Root-level files** — files placed immediately inside the folder.
2. **Recursive files** — all files in the folder and its subdirectories.

A folder is flagged as a *candidate* when every root-level file is smaller than the threshold. Recursive totals are shown separately so large nested packages are not hidden.

Thresholds tested: 200, 300 LoC.

## Results

| Folder | Root files | Root max | <200 LoC | <300 LoC | Recursive max | Relocation note |
|--------|-----------:|---------:|:-:|:-:|:-:|:----------------|
| `backend/` | 24 | 1482 | ❌ | ❌ | 1482 | not a candidate: primary package folder, conventionally at root |
| `configs/` | 3 | 44 | ✅ | ✅ | 64 | candidate: all root-level YAML presets are small. Could fold into ``src/uqlab_core/configs/`` so presets ship with the package, but ``runtime_paths.configs_dir()``, README, and every CLI/notebook reference must be updated. |
| `data/` | 1 | 0 | ✅ | ✅ | 0 | candidate, but keep at root: ``runtime_paths.data_root()`` defaults to ``<repo>/data``; relocating requires an env override or code change |
| `docs/` | 3 | 663 | ❌ | ❌ | 1224 | not a candidate: content category folder, conventionally at root |
| `notebooks/` | 9 | 987 | ❌ | ❌ | 1257 | not a candidate: content category folder, conventionally at root |
| `scripts/` | 4 | 636 | ❌ | ❌ | 652 | not a candidate: content category folder, conventionally at root |
| `src/` | 1 | 0 | ✅ | ✅ | 923 | not a candidate: primary package folder, conventionally at root |
| `tests/` | 52 | 473 | ❌ | ❌ | 473 | not a candidate: primary package folder, conventionally at root |
| `uqlab-flask/` | 3 | 37 | ✅ | ✅ | 652 | candidate: root-level files are small, but the package underneath is substantial; could move into ``backend/``, ``frontend/``, or a new ``ui/`` folder |

## Per-Folder Breakdown

### `backend/`

- **Root-level files:** 24 (4349 LoC total, max 1482 LoC)
- **Recursive files:** 113 (13726 LoC total, max 1482 LoC)
- **Relocation note:** not a candidate: primary package folder, conventionally at root

Root-level file breakdown:

Under 200 LoC:
  - uv.lock: 1482 LoC ❌
  - RUN_LABEL_NOISE_SWEEP_FLOW.md: 912 LoC ❌
  - STORAGE_ARCHITECTURE.md: 415 LoC ❌
  - API_ENDPOINTS_EXPLAINED.md: 233 LoC ❌
  - BACKEND_MODES.md: 187 LoC ✅
  - README.md: 181 LoC ✅
  - BACKFILL_README.md: 170 LoC ✅
  - backfill_signals.py: 109 LoC ✅
  - run_method_type_migration.py: 103 LoC ✅
  - pyproject.toml: 86 LoC ✅
  - run_benchmark_migration.py: 75 LoC ✅
  - alembic.ini: 71 LoC ✅
  - run_migration.py: 58 LoC ✅
  - Dockerfile: 50 LoC ✅
  - run_prod.py: 43 LoC ✅
  - run_dev.py: 39 LoC ✅
  - fix_python314.sh: 38 LoC ✅
  - _python.sh: 28 LoC ✅
  - start_backend.sh: 21 LoC ✅
  - start_backend_prod.sh: 19 LoC ✅
  - .gitignore: 13 LoC ✅
  - .dockerignore: 8 LoC ✅
  - .pre-commit-config.yaml: 7 LoC ✅
  - .python-version: 1 LoC ✅

Under 300 LoC:
  - uv.lock: 1482 LoC ❌
  - RUN_LABEL_NOISE_SWEEP_FLOW.md: 912 LoC ❌
  - STORAGE_ARCHITECTURE.md: 415 LoC ❌
  - API_ENDPOINTS_EXPLAINED.md: 233 LoC ✅
  - BACKEND_MODES.md: 187 LoC ✅
  - README.md: 181 LoC ✅
  - BACKFILL_README.md: 170 LoC ✅
  - backfill_signals.py: 109 LoC ✅
  - run_method_type_migration.py: 103 LoC ✅
  - pyproject.toml: 86 LoC ✅
  - run_benchmark_migration.py: 75 LoC ✅
  - alembic.ini: 71 LoC ✅
  - run_migration.py: 58 LoC ✅
  - Dockerfile: 50 LoC ✅
  - run_prod.py: 43 LoC ✅
  - run_dev.py: 39 LoC ✅
  - fix_python314.sh: 38 LoC ✅
  - _python.sh: 28 LoC ✅
  - start_backend.sh: 21 LoC ✅
  - start_backend_prod.sh: 19 LoC ✅
  - .gitignore: 13 LoC ✅
  - .dockerignore: 8 LoC ✅
  - .pre-commit-config.yaml: 7 LoC ✅
  - .python-version: 1 LoC ✅

### `configs/`

- **Root-level files:** 3 (110 LoC total, max 44 LoC)
- **Recursive files:** 11 (428 LoC total, max 64 LoC)
- **Relocation note:** candidate: all root-level YAML presets are small. Could fold into ``src/uqlab_core/configs/`` so presets ship with the package, but ``runtime_paths.configs_dir()``, README, and every CLI/notebook reference must be updated.

Root-level file breakdown:

Under 200 LoC:
  - example_cnn_mcdropout.yaml: 44 LoC ✅
  - example_resnet18_mcdropout.yaml: 40 LoC ✅
  - README.md: 26 LoC ✅

Under 300 LoC:
  - example_cnn_mcdropout.yaml: 44 LoC ✅
  - example_resnet18_mcdropout.yaml: 40 LoC ✅
  - README.md: 26 LoC ✅

### `data/`

- **Root-level files:** 1 (0 LoC total, max 0 LoC)
- **Recursive files:** 1 (0 LoC total, max 0 LoC)
- **Relocation note:** candidate, but keep at root: ``runtime_paths.data_root()`` defaults to ``<repo>/data``; relocating requires an env override or code change

Root-level file breakdown:

Under 200 LoC:
  - .gitkeep: 0 LoC ✅

Under 300 LoC:
  - .gitkeep: 0 LoC ✅

### `docs/`

- **Root-level files:** 3 (1098 LoC total, max 663 LoC)
- **Recursive files:** 348 (59504 LoC total, max 1224 LoC)
- **Relocation note:** not a candidate: content category folder, conventionally at root

Root-level file breakdown:

Under 200 LoC:
  - LAUNCH_TO_VISUALIZATION_FLOW.md: 663 LoC ❌
  - UQLAB_FLOW.md: 310 LoC ❌
  - README.md: 125 LoC ✅

Under 300 LoC:
  - LAUNCH_TO_VISUALIZATION_FLOW.md: 663 LoC ❌
  - UQLAB_FLOW.md: 310 LoC ❌
  - README.md: 125 LoC ✅

### `notebooks/`

- **Root-level files:** 9 (4902 LoC total, max 987 LoC)
- **Recursive files:** 23 (9080 LoC total, max 1257 LoC)
- **Relocation note:** not a candidate: content category folder, conventionally at root

Root-level file breakdown:

Under 200 LoC:
  - cifar10_paper_flow.ipynb: 987 LoC ❌
  - resnet_baseline_experiment.ipynb: 876 LoC ❌
  - watsonx_deployment_experiment.ipynb: 867 LoC ❌
  - attribution_distribution_uncertainty.ipynb: 787 LoC ❌
  - uncertainty_viz_3class.ipynb: 521 LoC ❌
  - uncertainty_visualization_demo.ipynb: 498 LoC ❌
  - four_region_benchmark.ipynb: 303 LoC ❌
  - bootstrap_uqlab.py: 63 LoC ✅
  - __init__.py: 0 LoC ✅

Under 300 LoC:
  - cifar10_paper_flow.ipynb: 987 LoC ❌
  - resnet_baseline_experiment.ipynb: 876 LoC ❌
  - watsonx_deployment_experiment.ipynb: 867 LoC ❌
  - attribution_distribution_uncertainty.ipynb: 787 LoC ❌
  - uncertainty_viz_3class.ipynb: 521 LoC ❌
  - uncertainty_visualization_demo.ipynb: 498 LoC ❌
  - four_region_benchmark.ipynb: 303 LoC ❌
  - bootstrap_uqlab.py: 63 LoC ✅
  - __init__.py: 0 LoC ✅

### `scripts/`

- **Root-level files:** 4 (1414 LoC total, max 636 LoC)
- **Recursive files:** 60 (11600 LoC total, max 652 LoC)
- **Relocation note:** not a candidate: content category folder, conventionally at root

Root-level file breakdown:

Under 200 LoC:
  - README.md: 636 LoC ❌
  - validate_per_class_campaign.py: 596 LoC ❌
  - migrate_to_uqlab_core.py: 134 LoC ✅
  - regenerate_shims.py: 48 LoC ✅

Under 300 LoC:
  - README.md: 636 LoC ❌
  - validate_per_class_campaign.py: 596 LoC ❌
  - migrate_to_uqlab_core.py: 134 LoC ✅
  - regenerate_shims.py: 48 LoC ✅

### `src/`

- **Root-level files:** 1 (0 LoC total, max 0 LoC)
- **Recursive files:** 68 (14685 LoC total, max 923 LoC)
- **Relocation note:** not a candidate: primary package folder, conventionally at root

Root-level file breakdown:

Under 200 LoC:
  - __init__.py: 0 LoC ✅

Under 300 LoC:
  - __init__.py: 0 LoC ✅

### `tests/`

- **Root-level files:** 52 (7179 LoC total, max 473 LoC)
- **Recursive files:** 63 (8305 LoC total, max 473 LoC)
- **Relocation note:** not a candidate: primary package folder, conventionally at root

Root-level file breakdown:

Under 200 LoC:
  - test_uncertainty_metrics.py: 473 LoC ❌
  - test_resnet_modes_standalone.py: 469 LoC ❌
  - test_workflow_validation.py: 458 LoC ❌
  - test_runner_signals.py: 455 LoC ❌
  - test_resnet_modes.py: 389 LoC ❌
  - test_campaign_report.py: 353 LoC ❌
  - test_resnet_training_modes.py: 323 LoC ❌
  - test_sweep_line_plot.py: 299 LoC ❌
  - test_paper_benchmark_plot.py: 268 LoC ❌
  - test_checkpoint_arsenal.py: 252 LoC ❌
  - test_evaluation.py: 197 LoC ✅
  - test_config_schema.py: 195 LoC ✅
  - test_plot_probe.py: 175 LoC ✅
  - test_four_region_synthesis_profile.py: 155 LoC ✅
  - test_four_region_validation.py: 139 LoC ✅
  - test_disentangling_model.py: 130 LoC ✅
  - test_per_class_plumbing.py: 130 LoC ✅
  - README.md: 126 LoC ✅
  - test_four_region_split.py: 126 LoC ✅
  - test_campaign_config_timeline.py: 118 LoC ✅
  - test_facade_data_pipeline.py: 108 LoC ✅
  - test_training_data_inspection.py: 108 LoC ✅
  - test_run_recovery.py: 104 LoC ✅
  - test_uncertainty_registry.py: 96 LoC ✅
  - test_disentanglement_launcher.py: 95 LoC ✅
  - test_inverse_coherence.py: 86 LoC ✅
  - test_attribution_distribution.py: 76 LoC ✅
  - test_thesis_diagram.py: 74 LoC ✅
  - test_experiment_setup.py: 71 LoC ✅
  - test_pairwise_signal_contrasts.py: 68 LoC ✅
  - test_eval_artifacts.py: 65 LoC ✅
  - test_eval_signal_config.py: 65 LoC ✅
  - test_four_region_reporting.py: 64 LoC ✅
  - test_ui_import_is_light.py: 64 LoC ✅
  - test_dataloader_workers.py: 60 LoC ✅
  - test_sweep_plot_pools.py: 60 LoC ✅
  - test_build_results_markdown.py: 58 LoC ✅
  - test_campaign_paper_score.py: 58 LoC ✅
  - test_experiment_log.py: 57 LoC ✅
  - test_plot_export.py: 57 LoC ✅
  - test_run_spec_checkpoint.py: 56 LoC ✅
  - test_runner_pipeline.py: 54 LoC ✅
  - test_run_artifacts.py: 49 LoC ✅
  - test_campaign_sections.py: 46 LoC ✅
  - test_dataset_factory.py: 42 LoC ✅
  - test_four_region_eval.py: 42 LoC ✅
  - test_result_writers.py: 41 LoC ✅
  - test_aleatoric_split.py: 38 LoC ✅
  - test_dead_code_imports.py: 32 LoC ✅
  - test_minimal.py: 24 LoC ✅
  - test_parse_under_supported_classes.py: 19 LoC ✅
  - __init__.py: 12 LoC ✅

Under 300 LoC:
  - test_uncertainty_metrics.py: 473 LoC ❌
  - test_resnet_modes_standalone.py: 469 LoC ❌
  - test_workflow_validation.py: 458 LoC ❌
  - test_runner_signals.py: 455 LoC ❌
  - test_resnet_modes.py: 389 LoC ❌
  - test_campaign_report.py: 353 LoC ❌
  - test_resnet_training_modes.py: 323 LoC ❌
  - test_sweep_line_plot.py: 299 LoC ✅
  - test_paper_benchmark_plot.py: 268 LoC ✅
  - test_checkpoint_arsenal.py: 252 LoC ✅
  - test_evaluation.py: 197 LoC ✅
  - test_config_schema.py: 195 LoC ✅
  - test_plot_probe.py: 175 LoC ✅
  - test_four_region_synthesis_profile.py: 155 LoC ✅
  - test_four_region_validation.py: 139 LoC ✅
  - test_disentangling_model.py: 130 LoC ✅
  - test_per_class_plumbing.py: 130 LoC ✅
  - README.md: 126 LoC ✅
  - test_four_region_split.py: 126 LoC ✅
  - test_campaign_config_timeline.py: 118 LoC ✅
  - test_facade_data_pipeline.py: 108 LoC ✅
  - test_training_data_inspection.py: 108 LoC ✅
  - test_run_recovery.py: 104 LoC ✅
  - test_uncertainty_registry.py: 96 LoC ✅
  - test_disentanglement_launcher.py: 95 LoC ✅
  - test_inverse_coherence.py: 86 LoC ✅
  - test_attribution_distribution.py: 76 LoC ✅
  - test_thesis_diagram.py: 74 LoC ✅
  - test_experiment_setup.py: 71 LoC ✅
  - test_pairwise_signal_contrasts.py: 68 LoC ✅
  - test_eval_artifacts.py: 65 LoC ✅
  - test_eval_signal_config.py: 65 LoC ✅
  - test_four_region_reporting.py: 64 LoC ✅
  - test_ui_import_is_light.py: 64 LoC ✅
  - test_dataloader_workers.py: 60 LoC ✅
  - test_sweep_plot_pools.py: 60 LoC ✅
  - test_build_results_markdown.py: 58 LoC ✅
  - test_campaign_paper_score.py: 58 LoC ✅
  - test_experiment_log.py: 57 LoC ✅
  - test_plot_export.py: 57 LoC ✅
  - test_run_spec_checkpoint.py: 56 LoC ✅
  - test_runner_pipeline.py: 54 LoC ✅
  - test_run_artifacts.py: 49 LoC ✅
  - test_campaign_sections.py: 46 LoC ✅
  - test_dataset_factory.py: 42 LoC ✅
  - test_four_region_eval.py: 42 LoC ✅
  - test_result_writers.py: 41 LoC ✅
  - test_aleatoric_split.py: 38 LoC ✅
  - test_dead_code_imports.py: 32 LoC ✅
  - test_minimal.py: 24 LoC ✅
  - test_parse_under_supported_classes.py: 19 LoC ✅
  - __init__.py: 12 LoC ✅

### `uqlab-flask/`

- **Root-level files:** 3 (72 LoC total, max 37 LoC)
- **Recursive files:** 18 (1768 LoC total, max 652 LoC)
- **Relocation note:** candidate: root-level files are small, but the package underneath is substantial; could move into ``backend/``, ``frontend/``, or a new ``ui/`` folder

Root-level file breakdown:

Under 200 LoC:
  - app.py: 37 LoC ✅
  - README.md: 33 LoC ✅
  - requirements.txt: 2 LoC ✅

Under 300 LoC:
  - app.py: 37 LoC ✅
  - README.md: 33 LoC ✅
  - requirements.txt: 2 LoC ✅
