# Small File Relocation Candidates

This document tracks root-level files and root folders whose files are under 200–300 lines of code and could be relocated to reduce clutter at the repository root.

## Completed relocations

The following files were small enough and safe to move without breaking core entry points.

| File | Old path | New path | Lines | Notes |
|------|----------|----------|-------|-------|
| `analyze_md_files.py` | `/workspace/analyze_md_files.py` | `scripts/maintenance/analyze_md_files.py` | ~63 | Updated to resolve project root from its new script location. |
| `organize_root_scripts.sh` | `/workspace/organize_root_scripts.sh` | `scripts/maintenance/organize_root_scripts.sh` | ~57 | Updated to run from project root regardless of invocation path. |
| `streamlit_requirements.txt` | `/workspace/streamlit_requirements.txt` | `scripts/deployment/streamlit_requirements.txt` | ~10 | Updated references in deployment scripts and docs. |

### References updated

- `scripts/deployment/run_streamlit.sh`
- `scripts/deployment/run_streamlit_modular.sh`
- `docs/user-guides/README_PARENT.md`
- `docs/streamlit/STREAMLIT_README.md`
- `docs/development/UV_PYTHON_FIX.md`
- `docs/development/GITHUB_ISSUES.md`

## Remaining root-level candidates

These files are still at the repository root and are small enough to consider moving, but they are entry points or heavily referenced.

| File | Lines | Current role | Relocation considerations |
|------|-------|--------------|---------------------------|
| `start.sh` | ~61 | Streamlit frontend entry point | The `Makefile` already exposes `make run-frontend`. Could move to `scripts/deployment/` and update `Makefile` + docs, but many users likely run it directly. |
| `start-with-minio.sh` | ~88 | MinIO + backend entry point | Heavily referenced in `docs/setup/minio.md` and `docs/architecture/minio-storage.md`. Moving requires updating several documentation files. |
| `streamlit_app_progressive.py` | ~370 | Main Streamlit application | Above the 200/300 threshold. Should stay at root as the primary UI entry point. |

## Root folders with small files

### `uqlab-flask/`

A small Flask wizard UI that lives at the repository root. Most files are under 300 lines, but the executor is larger.

| File | Lines | Notes |
|------|-------|-------|
| `uqlab-flask/app.py` | ~37 | Application factory. |
| `uqlab-flask/uqlab_flask/routes/runs.py` | ~139 | Run status API. |
| `uqlab-flask/uqlab_flask/routes/wizard.py` | ~282 | 5-step workflow wizard. |
| `uqlab-flask/uqlab_flask/executor.py` | ~652 | Background job execution — exceeds the small-file threshold. |

**Assessment:** The whole folder could be relocated into `src/uqlab_flask/` (as a proper package) or `scripts/`/`archive/` (if it is deprecated). However, it is a standalone UI entry point referenced in `START_HERE.md` and `docs/UQLAB_FLOW.md`, so relocation would require updating imports, `sys.path` setup, READMEs, and the run command. Keep at root unless the Flask wizard is being phased out.

### `backend/scripts/`

All six backend helper shell scripts are under 20 lines.

| File | Lines | Notes |
|------|-------|-------|
| `backend/scripts/entrypoint.sh` | ~10 | Docker entrypoint. |
| `backend/scripts/format.sh` | ~5 | Formatter wrapper. |
| `backend/scripts/lint.sh` | ~8 | Linter wrapper. |
| `backend/scripts/prestart.sh` | ~13 | Prestart checks. |
| `backend/scripts/test.sh` | ~8 | Test wrapper. |
| `backend/scripts/tests-start.sh` | ~7 | Test startup wrapper. |

**Assessment:** Could move to `scripts/backend/` for consistency with the root `scripts/` layout. However, they are tightly coupled to the `backend/` Docker image and referenced in `backend/Dockerfile` and `backend/README.md`. Moving them would require updating those files and ensuring Docker paths still work. Leave in `backend/` unless a broader scripts consolidation is planned.

### `configs/`

All YAML files are under 100 lines. This is a standard configuration folder and should remain at the repository root.

## Recommendation

- Keep `configs/` and `data/` at root — they are standard locations.
- Keep `start.sh`, `start-with-minio.sh`, and `uqlab-flask/` at root for now unless the project wants to deprecate or consolidate entry points.
- Consider moving `backend/scripts/` to `scripts/backend/` only if the Docker and backend README references are updated together.
- The three completed relocations above remove non-essential clutter from the root without breaking core workflows.
