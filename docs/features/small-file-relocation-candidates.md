# Small File Relocation Candidates

This report scans each top-level root folder and the project root for files at or under **300 lines of code (LoC)**.
Files under **200 LoC** are marked as `small`; files between 200 and 300 LoC (inclusive) are marked as `medium`.
The `Action` column recommends whether a file can be moved, suggests a destination, and explains why it should stay if not.

Generated: 2026-08-06

## Summary

- **Total files ≤300 LoC**: 106
- **Small files (<200 LoC)**: 97
- **Medium files (200–300 LoC)**: 9
- **Move candidates**: 18
- **Consider moving**: 5
- **Keep as-is**: 83

## Project Root

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 1 | small | `.python-version` | KEEP | standard project file that should stay in place |
| 3 | small | `.gitmodules` | KEEP | standard project file that should stay in place |
| 6 | small | `package-lock.json` | KEEP | standard project file that should stay in place |
| 10 | small | `streamlit_requirements.txt` | KEEP | standard root file |
| 15 | small | `.bobignore` | KEEP | standard project file that should stay in place |
| 18 | small | `.ruffignore` | KEEP | standard project file that should stay in place |
| 30 | small | `.env.example` | KEEP | standard project file that should stay in place |
| 44 | small | `docker-compose.yml` | CONSIDER → `backend/docker-compose.yml` | group with backend tooling |
| 46 | small | `pytest.ini` | KEEP | standard project file that should stay in place |
| 57 | small | `organize_root_scripts.sh` | MOVE → `scripts/maintenance/` | small maintenance script |
| 61 | small | `start.sh` | MOVE → `scripts/deployment/` | small standalone launcher |
| 63 | small | `analyze_md_files.py` | MOVE → `scripts/analysis/` | Markdown analysis helper |
| 69 | small | `.env.production.example` | KEEP | standard project file that should stay in place |
| 80 | small | `mypy.ini` | KEEP | standard project file that should stay in place |
| 88 | small | `start-with-minio.sh` | MOVE → `scripts/deployment/` | small standalone launcher |
| 97 | small | `START_HERE.md` | KEEP | primary project documentation |
| 116 | small | `pyproject.toml` | KEEP | standard project file that should stay in place |
| 119 | small | `.gitignore_parent` | KEEP | standard root file |
| 119 | small | `Makefile` | KEEP | standard project file that should stay in place |
| 132 | small | `analysis_results.txt` | KEEP | standard root file |
| 150 | small | `.gitignore` | KEEP | standard project file that should stay in place |
| 171 | small | `ARCHITECTURE_CLARIFICATION.md` | MOVE → `docs/` | architecture/design documentation |
| 229 | medium | `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | MOVE → `docs/` | architecture/design documentation |
| 235 | medium | `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | MOVE → `docs/` | architecture/design documentation |
| 275 | medium | `TERMINOLOGY_CLARIFICATION.md` | MOVE → `docs/` | architecture/design documentation |
| 296 | medium | `PACKAGE_REORGANIZATION_PROPOSAL.md` | MOVE → `docs/` | architecture/design documentation |
| 300 | medium | `FINAL_ARCHITECTURE_DECISION.md` | MOVE → `docs/` | architecture/design documentation |

## src

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 0 | small | `src/__init__.py` | KEEP | standard project file that should stay in place |

## backend

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 1 | small | `backend/.python-version` | KEEP | standard project file that should stay in place |
| 7 | small | `backend/.pre-commit-config.yaml` | KEEP | standard project file that should stay in place |
| 8 | small | `backend/.dockerignore` | KEEP | standard project file that should stay in place |
| 13 | small | `backend/.gitignore` | KEEP | standard project file that should stay in place |
| 19 | small | `backend/start_backend_prod.sh` | CONSIDER → `backend/scripts/` | backend startup helper |
| 21 | small | `backend/start_backend.sh` | CONSIDER → `backend/scripts/` | backend startup helper |
| 28 | small | `backend/_python.sh` | MOVE → `backend/scripts/` | backend utility shell script |
| 38 | small | `backend/fix_python314.sh` | MOVE → `backend/scripts/` | backend utility shell script |
| 39 | small | `backend/run_dev.py` | MOVE → `backend/scripts/` | backend runner script |
| 43 | small | `backend/run_prod.py` | MOVE → `backend/scripts/` | backend runner script |
| 50 | small | `backend/Dockerfile` | KEEP | standard project file that should stay in place |
| 58 | small | `backend/run_migration.py` | MOVE → `backend/scripts/` | backend runner script |
| 71 | small | `backend/alembic.ini` | KEEP | backend config |
| 75 | small | `backend/run_benchmark_migration.py` | MOVE → `backend/scripts/` | backend runner script |
| 86 | small | `backend/pyproject.toml` | KEEP | standard project file that should stay in place |
| 103 | small | `backend/run_method_type_migration.py` | MOVE → `backend/scripts/` | backend runner script |
| 109 | small | `backend/backfill_signals.py` | MOVE → `backend/scripts/` | backend backfill script |
| 170 | small | `backend/BACKFILL_README.md` | KEEP | backend documentation |
| 181 | small | `backend/README.md` | KEEP | standard project file that should stay in place |
| 187 | small | `backend/BACKEND_MODES.md` | KEEP | backend documentation |
| 233 | medium | `backend/API_ENDPOINTS_EXPLAINED.md` | KEEP | backend documentation |

## uqlab-flask

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 2 | small | `uqlab-flask/requirements.txt` | KEEP | dependency list |
| 33 | small | `uqlab-flask/README.md` | KEEP | standard project file that should stay in place |
| 37 | small | `uqlab-flask/app.py` | KEEP | Flask application entry point |

## scripts

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 48 | small | `scripts/regenerate_shims.py` | CONSIDER → `scripts/maintenance/` | migration/shim helper |
| 134 | small | `scripts/migrate_to_uqlab_core.py` | CONSIDER → `scripts/maintenance/` | migration/shim helper |

## tests

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 12 | small | `tests/__init__.py` | KEEP | standard project file that should stay in place |
| 19 | small | `tests/test_parse_under_supported_classes.py` | KEEP | test file |
| 24 | small | `tests/test_minimal.py` | KEEP | test file |
| 32 | small | `tests/test_dead_code_imports.py` | KEEP | test file |
| 38 | small | `tests/test_aleatoric_split.py` | KEEP | test file |
| 41 | small | `tests/test_result_writers.py` | KEEP | test file |
| 42 | small | `tests/test_dataset_factory.py` | KEEP | test file |
| 42 | small | `tests/test_four_region_eval.py` | KEEP | test file |
| 46 | small | `tests/test_campaign_sections.py` | KEEP | test file |
| 49 | small | `tests/test_run_artifacts.py` | KEEP | test file |
| 54 | small | `tests/test_runner_pipeline.py` | KEEP | test file |
| 56 | small | `tests/test_run_spec_checkpoint.py` | KEEP | test file |
| 57 | small | `tests/test_experiment_log.py` | KEEP | test file |
| 57 | small | `tests/test_plot_export.py` | KEEP | test file |
| 58 | small | `tests/test_build_results_markdown.py` | KEEP | test file |
| 58 | small | `tests/test_campaign_paper_score.py` | KEEP | test file |
| 60 | small | `tests/test_dataloader_workers.py` | KEEP | test file |
| 60 | small | `tests/test_sweep_plot_pools.py` | KEEP | test file |
| 64 | small | `tests/test_four_region_reporting.py` | KEEP | test file |
| 64 | small | `tests/test_ui_import_is_light.py` | KEEP | test file |
| 65 | small | `tests/test_eval_artifacts.py` | KEEP | test file |
| 65 | small | `tests/test_eval_signal_config.py` | KEEP | test file |
| 68 | small | `tests/test_pairwise_signal_contrasts.py` | KEEP | test file |
| 71 | small | `tests/test_experiment_setup.py` | KEEP | test file |
| 74 | small | `tests/test_thesis_diagram.py` | KEEP | test file |
| 76 | small | `tests/test_attribution_distribution.py` | KEEP | test file |
| 86 | small | `tests/test_inverse_coherence.py` | KEEP | test file |
| 95 | small | `tests/test_disentanglement_launcher.py` | KEEP | test file |
| 96 | small | `tests/test_uncertainty_registry.py` | KEEP | test file |
| 104 | small | `tests/test_run_recovery.py` | KEEP | test file |
| 108 | small | `tests/test_facade_data_pipeline.py` | KEEP | test file |
| 108 | small | `tests/test_training_data_inspection.py` | KEEP | test file |
| 118 | small | `tests/test_campaign_config_timeline.py` | KEEP | test file |
| 126 | small | `tests/README.md` | KEEP | standard project file that should stay in place |
| 126 | small | `tests/test_four_region_split.py` | KEEP | test file |
| 130 | small | `tests/test_disentangling_model.py` | KEEP | test file |
| 130 | small | `tests/test_per_class_plumbing.py` | KEEP | test file |
| 139 | small | `tests/test_four_region_validation.py` | KEEP | test file |
| 155 | small | `tests/test_four_region_synthesis_profile.py` | KEEP | test file |
| 175 | small | `tests/test_plot_probe.py` | KEEP | test file |
| 195 | small | `tests/test_config_schema.py` | KEEP | test file |
| 197 | small | `tests/test_evaluation.py` | KEEP | test file |
| 252 | medium | `tests/test_checkpoint_arsenal.py` | KEEP | test file |
| 268 | medium | `tests/test_paper_benchmark_plot.py` | KEEP | test file |
| 299 | medium | `tests/test_sweep_line_plot.py` | KEEP | test file |

## configs

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 26 | small | `configs/README.md` | KEEP | standard project file that should stay in place |
| 40 | small | `configs/example_resnet18_mcdropout.yaml` | KEEP | experiment configuration |
| 44 | small | `configs/example_cnn_mcdropout.yaml` | KEEP | experiment configuration |

## docs

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 125 | small | `docs/README.md` | KEEP | standard project file that should stay in place |

## notebooks

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 0 | small | `notebooks/__init__.py` | KEEP | standard project file that should stay in place |
| 63 | small | `notebooks/bootstrap_uqlab.py` | KEEP | notebook |

## data

| LoC | Size | Path | Action | Reason |
|-----|------|------|--------|--------|
| 0 | small | `data/.gitkeep` | KEEP | standard project file that should stay in place |

## Top Recommendations

1. **Project Root shell scripts**: `start.sh`, `start-with-minio.sh`, and `organize_root_scripts.sh` are small and can move to `scripts/deployment/` or `scripts/maintenance/` to reduce root clutter.
2. **Project Root analysis script**: `analyze_md_files.py` (≈2 KB) fits naturally in `scripts/analysis/`.
3. **Backend top-level scripts**: `run_dev.py`, `run_prod.py`, `run_migration.py`, `run_benchmark_migration.py`, `run_method_type_migration.py`, and shell helpers (`start_backend.sh`, `start_backend_prod.sh`, `fix_python314.sh`, `_python.sh`) are good candidates for `backend/scripts/`.
4. **Root markdown guides**: Non-primary docs such as `ARCHITECTURE_CLARIFICATION.md`, `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md`, `COMPLETE_SYSTEM_FLOW.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `FINAL_ARCHITECTURE_DECISION.md`, `IMPORT_GUIDE.md`, `PACKAGE_REORGANIZATION_PROPOSAL.md`, and `TERMINOLOGY_CLARIFICATION.md` could be consolidated under `docs/`.
5. **Keep entry points and standard config**: `streamlit_app_progressive.py`, `Makefile`, `pyproject.toml`, `pytest.ini`, `mypy.ini`, `.gitignore`, `.env.example`, and `docker-compose.yml` should remain in the root.

## Notes

- `__init__.py`, `__main__.py`, symlinks, generated lock files, and binary assets are excluded from this scan because they are not relocation candidates.
- The existing `scripts/` directory already has `maintenance/`, `fixes/`, `diagnostics/`, `deployment/`, `analysis/`, `runners/`, and `setup/` subdirectories, which provides clear destinations for several root-level scripts.
- The `PACKAGE_REORGANIZATION_PROPOSAL.md` already identifies moving `src/uqlab/ui_components/` → `src/streamlit_ui/components/`; this report focuses on smaller, standalone files.
