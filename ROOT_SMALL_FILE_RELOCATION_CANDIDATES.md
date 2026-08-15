# Root Small-File Relocation Candidates

**Target folder:** project root (`/workspace`)  
**Threshold:** files under 200/300 LoC  
**Principle reused from prior work:** `docs/archive/SCRIPTS_REORGANIZATION_PLAN.md` — folders shouldn't have 1-4 loose files, they should be grouped; utility scripts belong under `scripts/`.

## Small files at project root (< 300 LoC)

| File | LoC | Type | References elsewhere | Relocation candidate | Risk |
|------|-----|------|----------------------|----------------------|------|
| `streamlit_requirements.txt` | 10 | config | `scripts/deployment/run_streamlit*.sh`, docs | `scripts/deployment/` or merge into `pyproject.toml` | low (needs reference updates) |
| `analyze_md_files.py` | 63 | maintenance script | none | `scripts/maintenance/` | **none** |
| `organize_root_scripts.sh` | 57 | maintenance script | none | `scripts/maintenance/` | **none** |
| `start.sh` | 61 | startup script | `backend/README.md`, `docs/setup/minio.md`, `docs/architecture/minio-storage.md` | `scripts/deployment/` or `scripts/maintenance/` | low (needs reference updates) |
| `start-with-minio.sh` | 88 | startup script | same as `start.sh` | `scripts/deployment/` or `scripts/maintenance/` | low (needs reference updates) |
| `docker-compose.yml` | 44 | deployment config | none visible | keep at root (standard convention) | low |
| `pytest.ini` | 46 | config | none visible | keep at root (standard convention) | none |
| `mypy.ini` | 80 | config | none visible | keep at root (standard convention) | none |
| `Makefile` | 119 | build orchestration | none visible | keep at root (standard convention) | none |
| `pyproject.toml` | 116 | project config | none visible | keep at root (required) | none |
| `START_HERE.md` | 97 | documentation | none visible | keep at root or move to `docs/` | low |
| `analysis_results.txt` | 132 | generated output | none visible | `data/` or `results/` | low |

Files above 300 LoC at root were excluded from the move list (e.g. `streamlit_app_progressive.py` at 370 LoC, `README.md`, `FINAL_ARCHITECTURE_DECISION.md`, etc.).

## Immediate safe moves

Two root-level scripts have **zero references** anywhere in the repo, so they can be moved without breaking anything:

- `analyze_md_files.py` → `scripts/maintenance/analyze_md_files.py`
- `organize_root_scripts.sh` → `scripts/maintenance/organize_root_scripts.sh`

`scripts/maintenance/` already contains similar housekeeping utilities (`cleanup_root_level.sh`, `reorganize_folders.sh`, `remove_ui_debug.py`, `remove_walaris_references.py`, etc.), so this is the natural home.

## Candidates that need reference updates

- `start.sh` and `start-with-minio.sh` are referenced by backend docs and `minio-storage.md`. They should probably move to `scripts/deployment/` alongside `run_streamlit.sh` and `ce-deploy.sh`, but the docs must be updated.
- `streamlit_requirements.txt` is referenced by `scripts/deployment/run_streamlit*.sh` and several docs. It should move into `scripts/deployment/` or be merged into `pyproject.toml`/`backend/pyproject.toml` extras, with all references updated.

## Files that should stay at root

- `docker-compose.yml`, `pyproject.toml`, `pytest.ini`, `mypy.ini`, `Makefile` — these are conventional top-level project files.
- `README.md`, `START_HERE.md`, `FINAL_ARCHITECTURE_DECISION.md`, etc. — top-level documentation and entry points.
- `streamlit_app_progressive.py` — main application entry point; moving it would break launch workflows and is not justified by its size (370 LoC).

## Next steps

1. Move `analyze_md_files.py` and `organize_root_scripts.sh` to `scripts/maintenance/` (safe, no references).
2. If desired, relocate `start.sh`, `start-with-minio.sh`, and `streamlit_requirements.txt` to `scripts/deployment/` and update the docs/scripts that reference them.
3. Consider deleting or archiving `analysis_results.txt` if it is a stale generated artifact.

## Notes

- Checked `docs/features/` first per project rule; no existing feature doc directly covered root-level file relocation, but the scripts-reorganization principle (`docs/archive/SCRIPTS_REORGANIZATION_PLAN.md`) was reused here.
- Reference search used `rg` and excluded broken symlinks (`uq_benchmarks`, `uq_classification`, etc.).
