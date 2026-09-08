# Root Files Reorganization — 2026-09-08

## Goal

Reduce clutter in the repository root by moving small files (≤300 lines) that already belong in an existing subdirectory.

## What was moved

### Utility / maintenance files

| File | Lines | Old location | New location |
|------|-------|--------------|--------------|
| `analyze_md_files.py` | 63 | `/workspace/analyze_md_files.py` | `scripts/utils/analyze_md_files.py` |
| `organize_root_scripts.sh` | 57 | `/workspace/organize_root_scripts.sh` | `scripts/maintenance/organize_root_scripts.sh` |
| `analysis_results.txt` | 132 | `/workspace/analysis_results.txt` | `docs/development/analysis_results.txt` |

### Architecture & design docs

| File | Lines | Old location | New location |
|------|-------|--------------|--------------|
| `ARCHITECTURE_CLARIFICATION.md` | 171 | `/workspace/ARCHITECTURE_CLARIFICATION.md` | `docs/architecture/ARCHITECTURE_CLARIFICATION.md` |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | `/workspace/ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | `docs/architecture/ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | `/workspace/FINAL_ARCHITECTURE_DECISION.md` | `docs/architecture/FINAL_ARCHITECTURE_DECISION.md` |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | `/workspace/TERMINOLOGY_CLARIFICATION.md` | `docs/architecture/TERMINOLOGY_CLARIFICATION.md` |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | `/workspace/PACKAGE_REORGANIZATION_PROPOSAL.md` | `docs/architecture/PACKAGE_REORGANIZATION_PROPOSAL.md` |

### Execution, dependency, and flow docs

| File | Lines | Old location | New location |
|------|-------|--------------|--------------|
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | `/workspace/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | `docs/development/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | `/workspace/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` |
| `IMPORT_GUIDE.md` | 491 | `/workspace/IMPORT_GUIDE.md` | `docs/development/IMPORT_GUIDE.md` |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | `/workspace/COMPLETE_SYSTEM_FLOW.md` | `docs/development/COMPLETE_SYSTEM_FLOW.md` |

## What stayed at root

Files that remain in `/workspace` because they are entry points, heavily referenced by existing docs/scripts, or standard project metadata:

- `README.md` (366) — main project README
- `START_HERE.md` (97) — root pointer to `docs/UQLAB_FLOW.md`
- `streamlit_app_progressive.py` (370) — primary Streamlit app; referenced by Makefile, docs, scripts
- `start.sh` (61) — convenience startup script; referenced by docs
- `start-with-minio.sh` (88) — convenience startup script; referenced by docs
- `pyproject.toml`, `Makefile`, `docker-compose.yml`, `pytest.ini`, `mypy.ini`, `.env.example`, `.env.production.example`, `.gitignore`, `.gitignore_parent`, `.bobignore`, `.ruffignore`, `.gitmodules`, `.python-version`, `streamlit_requirements.txt`, `package-lock.json`, `uv.lock`, `dependencies.json` — project config / lock files
- `2408.12175v3.pdf` and `three_axioms_demonstration.png` — reference artifacts

## Cross-references updated

- `README.md` — updated links to `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` and `ARCHITECTURE_CLARIFICATION.md`
- `docs/development/COMPLETE_SYSTEM_FLOW.md` — updated link to `ARCHITECTURE_CLARIFICATION.md`
- `docs/development/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` — updated link to `ARCHITECTURE_CLARIFICATION.md`
- `docs/architecture/classification-package-redirect.md` — updated link to `IMPORT_GUIDE.md`
- `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` — updated link to `PACKAGE_REORGANIZATION_PROPOSAL.md`
- `docs/architecture/TERMINOLOGY_CLARIFICATION.md` — updated link to `FINAL_ARCHITECTURE_DECISION.md`

## Remaining candidates

The following root files are also ≤300 lines and could be considered in a future pass, but were left in place because they are entry-point scripts or widely referenced:

- `start.sh` (61)
- `start-with-minio.sh` (88)
- `START_HERE.md` (97)

If these are ever relocated, `Makefile`, `README.md`, and the docs in `docs/setup/` and `docs/development/` will need link updates.
