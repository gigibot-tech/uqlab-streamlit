# Root Level Cleanup Analysis

This document records the current state of root-level files and the cleanup performed to keep the repository root focused on essential entry points and configuration.

## Current Root Files

After cleanup, the root contains only files that must live at the repository root:

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `Makefile` | Development tasks |
| `pyproject.toml` | Python project configuration |
| `pytest.ini` | Pytest configuration |
| `mypy.ini` | Mypy configuration |
| `docker-compose.yml` | Docker services |
| `.env.example` / `.env.production.example` | Environment templates |
| `.gitignore` / `.gitignore_parent` | Git ignore rules |
| `.bobignore` / `.ruffignore` | Tool ignore rules |
| `.python-version` | Python version pin |
| `.gitmodules` | Git submodule configuration |
| `streamlit_requirements.txt` | Legacy Streamlit requirements note |
| `COMPLETE_SYSTEM_FLOW.md` | Top-level end-to-end system flow overview |
| `IMPORT_GUIDE.md` | Top-level import/shim guide |
| `streamlit_app_progressive.py` | Primary Streamlit application entry point |
| `2408.12175v3.pdf` | Reference paper |
| `three_axioms_demonstration.png` | Reference diagram |
| `uv.lock` | Locked dependency snapshot |
| `dependencies.json` | Dependency analysis output |

## Files Moved (≤300 lines)

### Documentation moved to `docs/`

| File | Old Location | New Location |
|------|--------------|--------------|
| `START_HERE.md` | root | `docs/START_HERE.md` |
| `ARCHITECTURE_CLARIFICATION.md` | root | `docs/architecture/ARCHITECTURE_CLARIFICATION.md` |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | root | `docs/architecture/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` |
| `TERMINOLOGY_CLARIFICATION.md` | root | `docs/architecture/TERMINOLOGY_CLARIFICATION.md` |
| `FINAL_ARCHITECTURE_DECISION.md` | root | `docs/architecture/FINAL_ARCHITECTURE_DECISION.md` |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | root | `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | root | `docs/development/PACKAGE_REORGANIZATION_PROPOSAL.md` |

### Scripts and utilities moved to `scripts/`

| File | Old Location | New Location | Notes |
|------|--------------|--------------|-------|
| `start.sh` | root | `scripts/runners/start.sh` | Updated `SCRIPT_DIR` to resolve project root from new location |
| `start-with-minio.sh` | root | `scripts/deployment/start-with-minio.sh` | Updated to `cd` to project root first; backend path remains relative |
| `analyze_md_files.py` | root | `scripts/analysis/analyze_md_files.py` | Markdown categorization utility |
| `organize_root_scripts.sh` | root | `scripts/maintenance/organize_root_scripts.sh` | Historical cleanup script |

### Data/validation artifacts moved to `docs/validation/`

| File | Old Location | New Location |
|------|--------------|--------------|
| `analysis_results.txt` | root | `docs/validation/analysis_results.txt` |

### Removed items

| Item | Action | Reason |
|------|--------|--------|
| `uq_benchmarks` | `git rm` | Broken symlink to removed `src/uqlab/4_evaluation/benchmarks` |
| `uq_classification` | `git rm` | Broken symlink to removed `src/uqlab/classification` |
| `notebooks/validation/notebook_support` | `git rm` | Broken symlink to removed `src/walaris/notebook_support` |
| `.DS_Store` | `git rm` | macOS metadata file, already listed in `.gitignore` |
| `package-lock.json` | `git rm` | Generated lockfile, already listed in `.gitignore` |

## References Updated

The following files were updated to point to the new locations:

- `README.md` — links to `START_HERE.md`, `ARCHITECTURE_CLARIFICATION.md`, and `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`.
- `streamlit_app_progressive.py` — docstring and UI caption references to `START_HERE.md`.
- `COMPLETE_SYSTEM_FLOW.md` — link to `ARCHITECTURE_CLARIFICATION.md`.
- `docs/features/workflow-config.md` — link to `START_HERE.md`.
- `docs/architecture/TERMINOLOGY_CLARIFICATION.md` — links to `START_HERE.md` and `FINAL_ARCHITECTURE_DECISION.md`.
- `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` — link to `PACKAGE_REORGANIZATION_PROPOSAL.md`.
- `docs/architecture/minio-storage.md` — references to `start-with-minio.sh`.
- `docs/setup/minio.md` — command references to `start-with-minio.sh`.
- `streamlit_requirements.txt` — comment reference to `start.sh`.
- `scripts/runners/start.sh` — `SCRIPT_DIR` resolution.
- `scripts/deployment/start-with-minio.sh` — added `SCRIPT_DIR` and `cd` to project root.

## Verification

After the moves, run these checks to confirm the root is clean and links are intact:

```bash
# List remaining root files with line counts
find . -maxdepth 1 -type f | xargs wc -l | sort -n

# Confirm no broken symlinks in root
find . -maxdepth 1 -xtype l

# Confirm tracked files that are also gitignored are gone
git ls-files | xargs git check-ignore --stdin
```

## Remaining Root-Level Files Over 300 Lines

These were intentionally kept in the root because they are top-level guides or primary entry points:

- `COMPLETE_SYSTEM_FLOW.md` (~498 lines)
- `IMPORT_GUIDE.md` (~491 lines)
- `README.md` (~366 lines)
- `streamlit_app_progressive.py` (~370 lines)
- `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` (~416 lines)

If the root needs to become even smaller, consider archiving the historical proposal documents and moving the top-level flow guides under `docs/` while updating `README.md` links.
