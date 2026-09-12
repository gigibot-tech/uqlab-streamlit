# Root Level Cleanup Analysis

This document tracks the state of the repository root. The goal is to keep only files that **must** live at the root (entry points, tooling configs, top-level orchestration) and move everything else to the appropriate `docs/`, `scripts/`, or `data/` subtree.

## Current root inventory (post cleanup)

| File | LoC | Category | Verdict |
|------|-----|----------|---------|
| `README.md` | 366 | Entry-point docs | **KEEP** — project landing page |
| `START_HERE.md` | 97 | Entry-point docs | **KEEP** — quick-start index referenced by README and feature docs |
| `pyproject.toml` | 116 | Python project config | **KEEP** — required by `uv`/`pip` |
| `pytest.ini` | 46 | Test config | **KEEP** — pytest looks at root |
| `mypy.ini` | 80 | Type-checking config | **KEEP** — mypy looks at root |
| `.ruffignore` | 17 | Linter ignore | **KEEP** — ruff looks at root |
| `.python-version` | 1 | Python version pin | **KEEP** — uv/pyenv look at root |
| `.gitignore` | 150 | Git ignore | **KEEP** — git looks at root |
| `.gitignore_parent` | 118 | Git ignore | **KEEP** — parent-project ignore rules |
| `.gitmodules` | 3 | Git submodule config | **KEEP** — git looks at root |
| `.bobignore` | 252 | Bob ignore | **KEEP** — Bob looks at root |
| `.env.example` | 29 | Environment template | **KEEP** — expected at root |
| `.env.production.example` | 68 | Environment template | **KEEP** — expected at root |
| `docker-compose.yml` | 44 | Docker orchestration | **KEEP** — docker compose expects it at root |
| `Makefile` | 119 | Task runner | **KEEP** — conventionally at root |
| `start.sh` | 61 | App launcher | **KEEP** — top-level entry script for Streamlit |
| `start-with-minio.sh` | 88 | Backend launcher | **KEEP** — top-level entry script for MinIO + backend |
| `streamlit_app_progressive.py` | 370 | Streamlit app | **KEEP** — main app, referenced by Makefile and start.sh |
| `streamlit_requirements.txt` | 10 | Streamlit deps | **KEEP** — keep next to the Streamlit app |
| `2408.12175v3.pdf` | — | Reference paper | **KEEP** — top-level reference artifact |
| `three_axioms_demonstration.png` | — | Reference diagram | **KEEP** — top-level reference artifact |
| `.DS_Store` | — | macOS metadata | **IGNORE** — do not commit |

Files that were **relocated** in this cleanup:

| Original root file | New location |
|--------------------|--------------|
| `ARCHITECTURE_CLARIFICATION.md` | `docs/architecture-design/ARCHITECTURE_CLARIFICATION.md` |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | `docs/architecture-design/ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` |
| `COMPLETE_SYSTEM_FLOW.md` | `docs/user-guides/COMPLETE_SYSTEM_FLOW.md` |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | `docs/user-guides/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` |
| `FINAL_ARCHITECTURE_DECISION.md` | `docs/architecture-design/FINAL_ARCHITECTURE_DECISION.md` |
| `IMPORT_GUIDE.md` | `docs/setup/IMPORT_GUIDE.md` |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | `docs/architecture-design/PACKAGE_REORGANIZATION_PROPOSAL.md` |
| `TERMINOLOGY_CLARIFICATION.md` | `docs/user-guides/TERMINOLOGY_CLARIFICATION.md` |
| `analysis_results.txt` | `docs/validation/analysis_results.txt` |
| `analyze_md_files.py` | `scripts/maintenance/analyze_md_files.py` |
| `dependencies.json` | `docs/development/dependencies.json` |
| `organize_root_scripts.sh` | `scripts/maintenance/organize_root_scripts.sh` |

## Why these files were moved

Most of them are **under ~300 lines** and are not required by standard tooling to be at the repository root:

- **Architecture/design documents** → `docs/architecture-design/`
- **Execution/setup/user-guide documents** → `docs/user-guides/` and `docs/setup/`
- **Development analysis artifacts** (`dependencies.json`, `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`) → `docs/development/`
- **Validation results** (`analysis_results.txt`) → `docs/validation/`
- **Maintenance utilities** (`organize_root_scripts.sh`, `analyze_md_files.py`) → `scripts/maintenance/`

## Reference updates performed

The following files had links updated to point to the new locations:

- `README.md`: `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` and `ARCHITECTURE_CLARIFICATION.md` links.
- `docs/architecture/classification-package-redirect.md`: `IMPORT_GUIDE.md` link.
- `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`: `analysis_results.txt` link.

## Remaining cleanup opportunities

The following are still at root but could be reconsidered in a future pass:

- `streamlit_app_progressive.py` + `streamlit_requirements.txt` — could move into a `src/streamlit_ui/pages/` or `frontend/streamlit/` package per `docs/architecture-design/PACKAGE_REORGANIZATION_PROPOSAL.md`, but that requires import and Makefile updates.
- `start.sh` / `start-with-minio.sh` — could move to `scripts/deployment/` and be replaced by thin root wrappers, but several docs reference them directly.
- `2408.12175v3.pdf` / `three_axioms_demonstration.png` — could move to `docs/reference/` or `assets/` if a dedicated asset folder is introduced.
- Broken symlinks `uq_benchmarks` and `uq_classification` should be repaired or removed.

## Benefits

- **Cleaner root** — only tooling configs and true entry points remain.
- **Predictable locations** — docs live under `docs/`, utilities under `scripts/`.
- **Preserved history** — all moves were done with `git mv`.
