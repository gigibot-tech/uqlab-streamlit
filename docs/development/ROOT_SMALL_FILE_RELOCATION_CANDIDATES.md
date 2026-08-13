# Root Small-File Relocation Candidates

**Date:** 2026-08-13  
**Scope:** Top-level (`/workspace`) files only.  
**Threshold:** Files with fewer than 200 LoC and fewer than 300 LoC (total lines, including blanks and comments).  
**Method:** Line counts from `wc`-style enumeration; references found with a text search across the repo (excluding `.git`, symlinks, and binary files).

## TL;DR

Out of **27** non-binary, non-symlink root files, **14** are under 200 LoC and **18** are under 300 LoC. Most of the small files are **tooling/config files that must stay at the root** (`.gitignore`, `pyproject.toml`, `docker-compose.yml`, etc.). The real relocation candidates are:

- **Scripts:** `organize_root_scripts.sh`, `start.sh`, `start-with-minio.sh` → `scripts/` or `scripts/shell/`.
- **One-off utilities/artifacts:** `analyze_md_files.py`, `analysis_results.txt` → `scripts/utils/` or `docs/validation/`/`data/`.
- **Small docs:** `START_HERE.md`, `ARCHITECTURE_CLARIFICATION.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`, `TERMINOLOGY_CLARIFICATION.md`, `PACKAGE_REORGANIZATION_PROPOSAL.md`, `FINAL_ARCHITECTURE_DECISION.md` → `docs/development/` or `docs/archive/`.

No matching requirement was found in `docs/features/`; this is a fresh inventory.

---

## Full root inventory

| File | Lines | Category | Relocation verdict |
|------|------:|----------|-------------------|
| `.python-version` | 1 | Tool config | **KEEP** – `pyenv`/`uv` conventionally read this from root. |
| `.gitmodules` | 3 | Git config | **KEEP** – Git requires this at root. |
| `package-lock.json` | 6 | Tool config | **KEEP** (or delete if stale) – npm-style lockfile belongs at root. |
| `streamlit_requirements.txt` | 10 | Tool config | **KEEP** – deprecated, but still referenced by name in the repo. If removed, delete rather than move. |
| `.bobignore` | 15 | Tool config | **KEEP** – Bob reads ignore files from root. |
| `.ruffignore` | 18 | Tool config | **KEEP** – Ruff reads this from root. |
| `.env.example` | 30 | Env config | **KEEP** – example env files belong at root. |
| `docker-compose.yml` | 44 | Docker config | **KEEP** – Docker Compose conventionally uses the root file. |
| `pytest.ini` | 46 | Tool config | **KEEP** – pytest config at root. |
| `organize_root_scripts.sh` | 57 | Maintenance script | **MOVEABLE** → `scripts/maintenance/` (no references). |
| `start.sh` | 61 | Entrypoint script | **MOVEABLE** → `scripts/` or `scripts/shell/`, but update `streamlit_requirements.txt` (deprecated comment). Conventionally a root start script, so this is a judgment call. |
| `analyze_md_files.py` | 63 | Utility script | **MOVEABLE** → `scripts/utils/` (no references). |
| `.env.production.example` | 69 | Env config | **KEEP** – example env file at root. |
| `mypy.ini` | 80 | Tool config | **KEEP** – mypy config at root. |
| `start-with-minio.sh` | 88 | Entrypoint script | **MOVEABLE** → `scripts/` or `scripts/shell/`, but update `docs/architecture/minio-storage.md` and `docs/setup/minio.md`. |
| `START_HERE.md` | 97 | Documentation | **MOVEABLE** → `docs/development/` or `docs/README.md` replacement, but update references in `README.md`, `streamlit_app_progressive.py`, `docs/features/workflow-config.md`, and `TERMINOLOGY_CLARIFICATION.md`. |
| `pyproject.toml` | 116 | Project config | **KEEP** – UV/Python project config must be at root. |
| `.gitignore_parent` | 119 | Git config | **KEEP** – git ignore file for parent layout. |
| `Makefile` | 119 | Build config | **KEEP** – Makefile conventionally at root. |
| `analysis_results.txt` | 132 | Generated artifact | **MOVEABLE** → `docs/validation/` or `data/`, but update `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`. |
| `.gitignore` | 150 | Git config | **KEEP** – Git requires this at root. |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | Documentation | **MOVEABLE** → `docs/development/` or `docs/architecture/`, but update `README.md`, `COMPLETE_SYSTEM_FLOW.md`, and `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`. |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | Documentation | **MOVEABLE** → `docs/development/`, but update `README.md` and `ARCHITECTURE_CLARIFICATION.md`. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 235 | Documentation | **MOVEABLE** → `docs/development/` or `docs/archive/` (no current references). |
| `TERMINOLOGY_CLARIFICATION.md` | 275 | Documentation | **MOVEABLE** → `docs/development/` or `docs/archive/` (no current references outside itself). |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 296 | Documentation | **MOVEABLE** → `docs/development/` or `docs/archive/`; only referenced by `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`. |
| `FINAL_ARCHITECTURE_DECISION.md` | 300 | Documentation | **MOVEABLE** → `docs/development/` or `docs/architecture/`; only referenced by `TERMINOLOGY_CLARIFICATION.md`. |
| `README.md` | 366 | Documentation | **KEEP** – main project README. |
| `streamlit_app_progressive.py` | 370 | Entrypoint | **KEEP** – main Streamlit app. |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 417 | Documentation | **KEEP** (or archive) – over 300 LoC; not a small-file candidate. |
| `IMPORT_GUIDE.md` | 492 | Documentation | **KEEP** (or archive) – over 300 LoC. |
| `COMPLETE_SYSTEM_FLOW.md` | 499 | Documentation | **KEEP** (or archive) – over 300 LoC. |
| `dependencies.json` | 21,420 | Generated artifact | **REVIEW** – not a small file, but is large enough to be worth moving to `data/` or removing if stale. |
| `uv.lock` | 4,626 | Tool lockfile | **KEEP** – UV lockfile conventionally at root. |
| `2408.12175v3.pdf` | 73,730 (binary) | Reference paper | **KEEP** – binary reference. |
| `three_axioms_demonstration.png` | 3,831 (binary) | Image asset | **KEEP** – binary image. |
| `uq_benchmarks` | symlink | Reference | **KEEP** – points to `src/uqlab/4_evaluation/benchmarks`. |
| `uq_classification` | symlink | Reference | **KEEP** – points to `src/uqlab/classification`. |

---

## Candidates grouped by target folder

### Move to `scripts/` (or subfolders)

| File | Lines | Notes |
|------|------:|-------|
| `organize_root_scripts.sh` | 57 | Already a maintenance script; move to `scripts/maintenance/`. |
| `start.sh` | 61 | Root convenience script; move to `scripts/` or `scripts/shell/` and update the deprecated note in `streamlit_requirements.txt`. |
| `start-with-minio.sh` | 88 | Docker/MinIO helper; move to `scripts/` or `scripts/shell/` and update `docs/architecture/minio-storage.md` and `docs/setup/minio.md`. |
| `analyze_md_files.py` | 63 | One-off categorization utility; move to `scripts/utils/`. |

### Move to `docs/development/` or `docs/archive/`

| File | Lines | Notes |
|------|------:|-------|
| `START_HERE.md` | 97 | Most referenced; keep if it is the onboarding landing page, or merge into `docs/README.md` and update links. |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | Move to `docs/development/` or `docs/architecture/`. |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | Move to `docs/development/`. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 235 | Move to `docs/development/` or `docs/archive/`. |
| `TERMINOLOGY_CLARIFICATION.md` | 275 | Move to `docs/development/` or `docs/archive/`. |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 296 | Move to `docs/development/` or `docs/archive/`. |
| `FINAL_ARCHITECTURE_DECISION.md` | 300 | Move to `docs/development/` or `docs/architecture/`. |

### Move to `data/` or `docs/validation/`

| File | Lines | Notes |
|------|------:|-------|
| `analysis_results.txt` | 132 | Generated validation summary; move to `docs/validation/` or `data/validation/` and update `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`. |

---

## References that would need updating if moved

| File | Referenced by |
|------|---------------|
| `start.sh` | `streamlit_requirements.txt` |
| `start-with-minio.sh` | `docs/architecture/minio-storage.md`, `docs/setup/minio.md` |
| `START_HERE.md` | `README.md`, `TERMINOLOGY_CLARIFICATION.md`, `streamlit_app_progressive.py`, `docs/features/workflow-config.md` |
| `ARCHITECTURE_CLARIFICATION.md` | `README.md`, `COMPLETE_SYSTEM_FLOW.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | `README.md` |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` |
| `FINAL_ARCHITECTURE_DECISION.md` | `TERMINOLOGY_CLARIFICATION.md` |
| `analysis_results.txt` | `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` |

---

## Existing cleanup artifacts

- `organize_root_scripts.sh` is already a cleanup script, but it references files that no longer exist at the root (e.g., `test_minimal.py`, `cleanup.sh`, `fix_missing_returns.sh`). If retained, it should be refreshed or moved to `scripts/maintenance/`.
- `PACKAGE_REORGANIZATION_PROPOSAL.md` discusses moving `src/uqlab/ui_components/` to `src/streamlit_ui/` and is unrelated to the current root-clutter check.
- `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md` is **outdated** (it assumes files like `run_fast.py`, `AGENTS.md`, `frontend/`, and `archive/` are at the root, which is not the current state). This inventory supersedes it for the current root layout.

---

## Recommended next steps

1. **Decide on a root-clutter policy:** Do you want only tooling/config/entrypoints at the root, or keep convenience scripts/docs too?
2. **Low-risk moves (no reference updates):**
   - `organize_root_scripts.sh` → `scripts/maintenance/`
   - `analyze_md_files.py` → `scripts/utils/`
   - `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` → `docs/development/`
   - `TERMINOLOGY_CLARIFICATION.md` → `docs/development/`
3. **Medium-risk moves (update docs):**
   - Move small docs (`ARCHITECTURE_CLARIFICATION.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `PACKAGE_REORGANIZATION_PROPOSAL.md`, `FINAL_ARCHITECTURE_DECISION.md`) into `docs/development/` and update the link references listed above.
   - Move `start.sh`/`start-with-minio.sh` to `scripts/shell/` and update docs/comments.
4. **Review large generated files:** `dependencies.json` and `uv.lock` are large; confirm they are still needed at root. `uv.lock` is standard; `dependencies.json` may be a stale analysis artifact and a deletion candidate.
