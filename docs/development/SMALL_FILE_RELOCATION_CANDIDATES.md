# Small File Relocation Candidates — Root Directory

> **Scope:** Examine the project root (`/`) for files under 200/300 lines of code and identify whether they can be relocated to a more appropriate folder. This is a focused follow-up to the broader cleanup documented in [`ROOT_LEVEL_CLEANUP_ANALYSIS.md`](ROOT_LEVEL_CLEANUP_ANALYSIS.md).

---

## TL;DR

The project root currently has **13 files under 200 LoC** and **6 additional files between 200–300 LoC**. Most config files and entry points should stay, but several misplaced scripts and generated artifacts can be relocated immediately:

| File | LoC | Current | Recommended | Action |
|------|-----|---------|-------------|--------|
| `organize_root_scripts.sh` | 57 | root | `scripts/maintenance/` | Move |
| `analyze_md_files.py` | 63 | root | `scripts/analysis/` | Move |
| `analysis_results.txt` | 132 | root | `docs/validation/` | Move + update doc reference |
| `package-lock.json` | 6 | root | — | Delete (empty artifact) |
| `streamlit_requirements.txt` | 10 | root | `scripts/deployment/` or delete | Move + update refs / delete (deprecated) |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | root | `docs/architecture/` | Move (optional) |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | root | `docs/architecture/` or `docs/user-guides/` | Move (optional) |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | root | `docs/architecture/` | Move (optional) |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | root | `docs/architecture/` | Move (optional) |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | root | `docs/architecture/` | Move (optional) |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | root | `docs/architecture/` or `docs/development/` | Move (optional) |

Files that should **remain at root**: `pyproject.toml`, `docker-compose.yml`, `pytest.ini`, `mypy.ini`, `Makefile`, `.env.example`, `.env.production.example`, `.gitignore`, `.gitignore_parent`, `.bobignore`, `.ruffignore`, `.gitmodules`, `.python-version`, `README.md`, `START_HERE.md`, `streamlit_app_progressive.py`, `start.sh`, `start-with-minio.sh`.

---

## Methodology

Line counts were measured with `wc -l` on the current branch (`cursor/small-file-relocation-candidates-f2f8`). Only non-directory, non-binary (except `.pdf`/`.png`) files at the repository root were considered. Dotfiles and lockfiles are included because they contribute to root clutter.

---

## Root Files Under 200 LoC

```
  LoC  File
  ---  ----
    1  .python-version
    3  .gitmodules
    6  package-lock.json
   10  streamlit_requirements.txt
   14  .bobignore
   17  .ruffignore
   29  .env.example
   44  docker-compose.yml
   46  pytest.ini
   57  organize_root_scripts.sh
   61  start.sh
   63  analyze_md_files.py
   68  .env.production.example
   80  mypy.ini
   88  start-with-minio.sh
   97  START_HERE.md
  116  pyproject.toml
  118  .gitignore_parent
  119  Makefile
  132  analysis_results.txt
  150  .gitignore
  171  ARCHITECTURE_CLARIFICATION.md
```

## Root Files Between 200–300 LoC

```
  LoC  File
  ---  ----
  229  EXECUTION_FLOW_AND_CONFIG_GUIDE.md
  234  DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md
  274  TERMINOLOGY_CLARIFICATION.md
  295  PACKAGE_REORGANIZATION_PROPOSAL.md
  299  FINAL_ARCHITECTURE_DECISION.md
```

Files above 300 LoC at root (`README.md`, `streamlit_app_progressive.py`, `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md`, `COMPLETE_SYSTEM_FLOW.md`, `IMPORT_GUIDE.md`, `dependencies.json`, `uv.lock`, etc.) are outside this scan but are documented in other cleanup proposals.

---

## Categorized Recommendations

### 1. Keep at Root — Required Config / Entry Points

These are either required by tooling to live at the project root or are primary entry points referenced by documentation.

| File | LoC | Reason to keep |
|------|-----|----------------|
| `pyproject.toml` | 116 | Python packaging metadata must be at root. |
| `docker-compose.yml` | 44 | `start-with-minio.sh` runs `docker-compose up` from root; expected by Docker users. |
| `pytest.ini` | 46 | Pytest configuration is conventionally at root. |
| `mypy.ini` | 80 | MyPy configuration is conventionally at root. |
| `Makefile` | 119 | Primary task runner; conventionally at root. |
| `.env.example` / `.env.production.example` | 29 / 68 | Template env files are conventionally at root. |
| `.gitignore` / `.gitignore_parent` / `.bobignore` / `.ruffignore` | 150 / 118 / 14 / 17 | VCS/tooling ignore files must be at root. |
| `.gitmodules` / `.python-version` | 3 / 1 | Git / pyenv metadata at root. |
| `README.md` | 366 | Main project README must stay at root. |
| `START_HERE.md` | 97 | Entry-point doc; referenced by README and docs. |
| `start.sh` | 61 | Primary Streamlit launch script; `./start.sh` is the documented command. |
| `start-with-minio.sh` | 88 | Documented as `./start-with-minio.sh` in several docs. |
| `streamlit_app_progressive.py` | 370 | Main Streamlit entry point; referenced by `start.sh` and Makefile. |

### 2. Move to `scripts/` — Misplaced Utility / Maintenance Scripts

These are executable or utility scripts that already have a natural home under the existing `scripts/` hierarchy.

#### `organize_root_scripts.sh` → `scripts/maintenance/`
- **What it does:** Organizes root-level scripts into `tests/`, `scripts/maintenance/`, `scripts/fixes/`, `scripts/diagnostics/`.
- **Why move:** It is itself a maintenance/orchestration script. `scripts/maintenance/` already contains `cleanup_root_level.sh`, `cleanup.sh`, `reorganize_folders.sh`, `rename_to_uqlab.sh`, etc.
- **Risk:** Low. No other files reference it.

#### `analyze_md_files.py` → `scripts/analysis/`
- **What it does:** Categorizes root `.md` files by keyword (architecture, UI, fixes, etc.).
- **Why move:** It is a diagnostic/analysis script. `scripts/analysis/` already contains `analyze_my_run.py`, `disentanglement_error.py`, `four_region_validation.py`, `paper_benchmarks.py`, `plot_run_region_means.py`.
- **Risk:** Low. No other files reference it.

### 3. Move or Delete — Generated Artifacts

#### `analysis_results.txt` → `docs/validation/` (or delete)
- **What it is:** Generated report from a hypothesis verification run (references `/tmp/walaris_experiments`).
- **Why move:** It is not source code; it is a result artifact. Keeping generated output at the root is confusing. Since it is referenced by a validation doc, placing it under `docs/validation/` keeps the reference working and the artifact accessible.
- **Reference to update:** `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` line 279 mentions `analysis_results.txt`.
- **Risk:** Low if the reference is updated; otherwise delete it and remove the reference.

#### `package-lock.json` → Delete
- **What it is:** Empty npm lockfile (`{ "name": "walaris-cen", "lockfileVersion": 3, "requires": true, "packages": {} }`).
- **Why delete:** The project does not use npm/Node.js at the root; this is a stale artifact from an earlier iteration. No references exist.
- **Risk:** None.

### 4. Move or Consolidate — Deprecated Requirements File

#### `streamlit_requirements.txt` → `scripts/deployment/` or delete
- **What it is:** A pip requirements file that is explicitly marked as deprecated in its own header (`# Deprecated — use uv from the repo root instead`).
- **Why move/delete:** It is still referenced by `scripts/deployment/run_streamlit.sh` and `scripts/deployment/run_streamlit_modular.sh`, and by several docs. If kept, it belongs next to the deployment scripts that consume it. If the project has fully switched to `uv`, it should be deleted and the deployment scripts/docs updated.
- **Risk:** Medium because of existing references.

### 5. Optional — Move Architecture Docs to `docs/architecture/`

The project already has `docs/architecture/` and `docs/architecture-design/` directories containing similar architecture documents. These root-level architecture docs are candidates for consolidation, but moving them requires checking/updating internal links.

| File | LoC | Suggested destination |
|------|-----|----------------------|
| `ARCHITECTURE_CLARIFICATION.md` | 171 | `docs/architecture/` |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | `docs/architecture/` or `docs/user-guides/` |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | `docs/architecture/` |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | `docs/architecture/` |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | `docs/architecture/` |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | `docs/architecture/` or `docs/development/` |

**Risk:** Medium — requires link/reference checks, but no functional code depends on them.

---

## Additional Candidate: `backend/` Root Files

As a secondary example of a “root folder” with small files, the `backend/` directory also contains several files under 300 LoC that could be consolidated into `backend/scripts/`:

| File | LoC | Suggested destination |
|------|-----|----------------------|
| `backfill_signals.py` | ~104 | `backend/scripts/` |
| `fix_python314.sh` | ~30 | `backend/scripts/` |
| `_python.sh` | ~30 | `backend/scripts/` |
| `run_dev.py` | ~32 | `backend/scripts/` |
| `run_prod.py` | ~35 | `backend/scripts/` |
| `run_migration.py` | ~45 | `backend/scripts/` |
| `run_benchmark_migration.py` | ~60 | `backend/scripts/` |
| `run_method_type_migration.py` | ~90 | `backend/scripts/` |
| `start_backend.sh` | ~22 | `backend/scripts/` |
| `start_backend_prod.sh` | ~20 | `backend/scripts/` |
| `Dockerfile` | ~38 | keep (must be at package root for context) |
| `pyproject.toml` | ~80 | keep (backend package metadata) |
| `alembic.ini` | ~70 | keep (config) |
| `README.md` | ~200 | keep (backend entry doc) |

This is listed as a follow-up candidate and is **not** part of the immediate root-cleanup actions below.

---

## Immediate Safe Actions

These four moves can be done without changing any functional code or user-facing entry points:

```bash
# 1. Move maintenance script to its natural home
mv organize_root_scripts.sh scripts/maintenance/

# 2. Move MD analysis script to analysis scripts
mv analyze_md_files.py scripts/analysis/

# 3. Move generated report next to the validation doc that references it
mv analysis_results.txt docs/validation/

# 4. Remove stale empty npm lockfile
rm package-lock.json
```

After moving `analysis_results.txt`, update the reference in `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` from:

```markdown
**Full Results:** `analysis_results.txt`
```

to:

```markdown
**Full Results:** `docs/validation/analysis_results.txt`
```

---

## Next Steps (Optional)

1. **Decide on `streamlit_requirements.txt`**: Either move it to `scripts/deployment/` and update the two deployment scripts, or delete it and update the deployment scripts + docs to use `uv sync`.
2. **Move architecture docs** to `docs/architecture/` if the team agrees on consolidating documentation.
3. **Revisit `backend/` root** for a follow-up small-file cleanup.

---

## Related Documents

- [`ROOT_LEVEL_CLEANUP_ANALYSIS.md`](ROOT_LEVEL_CLEANUP_ANALYSIS.md) — Broader root-cleanup proposal from earlier in the project.
- [`PACKAGE_REORGANIZATION_PROPOSAL.md`](../PACKAGE_REORGANIZATION_PROPOSAL.md) — Proposed `src/` package separation (`uqlab`, `uqlab_orchestrator`, `streamlit_ui`).
- [`docs/features/README.md`](../features/README.md) — Feature documentation index.
