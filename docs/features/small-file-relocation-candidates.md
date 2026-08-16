# Root-Level Small-File Relocation Candidates

**Branch:** `cursor/small-file-relocation-candidates-3e54`  
**Date:** 2026-08-16  
**Scope:** Identify files in the repository root that are under 300 lines and could be relocated to existing folders (`scripts/`, `configs/`, `docs/`, `data/`, etc.).

This document is the input for a cleanup pass. It does **not** perform the moves itself; it lists candidates, proposed destinations, and any caveats.

---

## Methodology

- Line counts are `wc -l` totals for the root-level files (non-recursive).
- Thresholds: **< 200 LoC** and **< 300 LoC** as requested.
- A file is a candidate if it is not a hard root requirement (e.g., `.gitmodules`, `.gitignore`, `pyproject.toml`, `Makefile`, `docker-compose.yml`).
- Existing organization patterns were reused from:
  - `organize_root_scripts.sh` (root-script cleanup pattern)
  - `PACKAGE_REORGANIZATION_PROPOSAL.md` (package separation rationale)
  - Current `scripts/`, `configs/`, `docs/`, `data/` layouts

---

## Summary

| Bucket | Count | Action |
|--------|-------|--------|
| Root files < 300 LoC | 28 | reviewed |
| Safe to relocate | 13 | move to existing folders |
| Should stay in root | 8 | required by tooling or convention |
| Delete / merge | 4 | orphaned, redundant, or generated |
| Needs adjustment before move | 3 | references must be updated |

---

## Candidates (< 200 LoC)

| File | LoC | Category | Proposed Destination | Rationale | Notes |
|------|-----|----------|----------------------|-----------|-------|
| `.python-version` | 1 | Tool config | **keep root** | Standard Python-version marker for `pyenv`/`uv` | Must stay in root to be found |
| `.gitmodules` | 3 | Git config | **keep root** | Git submodule configuration | Git requires it in root |
| `package-lock.json` | 6 | Orphaned artifact | **delete** | No `package.json` exists; already ignored by `.gitignore` | Generated file, not needed |
| `streamlit_requirements.txt` | 10 | Deprecated deps | `docs/archive/` or **delete** | Marked deprecated; superseded by `uv sync` | 6 docs/scripts still reference it (see below) |
| `.DS_Store` | 13 | OS junk | **delete** | macOS metadata file | Should be added to `.gitignore` if not already present |
| `.bobignore` | 14 | Tool config | **keep root** or `.bob/` | Bob-specific ignore rules | Verify Bob reads it from `.bob/` before moving |
| `.ruffignore` | 17 | Linter config | **merge into `pyproject.toml`** | Small enough to inline as `[tool.ruff]` exclude | Reduces root clutter |
| `.env.example` | 29 | Env template | `configs/` or `docs/setup/` | Example configuration, not runtime-required | Update any setup docs that reference it |
| `docker-compose.yml` | 44 | Orchestration | **keep root** | Standard Docker Compose entry point | Conventionally root-located |
| `pytest.ini` | 46 | Test config | **merge into `pyproject.toml`** | pytest settings can live under `[tool.pytest.ini_options]` | Reduces root clutter |
| `organize_root_scripts.sh` | 57 | Maintenance script | `scripts/maintenance/` | It is literally a root-organization script | Matches `cleanup_root_level.sh`, `reorganize_folders.sh` already there |
| `start.sh` | 61 | Entry-point script | `scripts/deployment/` or **keep root** | Launcher for the Streamlit app | Uses `SCRIPT_DIR` for venv discovery; moving requires path fix |
| `analyze_md_files.py` | 63 | Diagnostic/util | `scripts/analysis/` or `scripts/maintenance/` | Categorizes root markdown files | Self-contained; safe to move |
| `.env.production.example` | 68 | Env template | `configs/` or `docs/setup/` | Production example configuration | Pair with `.env.example` in same folder |
| `mypy.ini` | 80 | Type config | **merge into `pyproject.toml`** | Mypy settings can live under `[tool.mypy]` | Reduces root clutter |
| `start-with-minio.sh` | 88 | Deployment script | `scripts/deployment/` | Starts MinIO + backend stack | Uses `docker-compose.yml` from root; moving requires `cd ..` adjustment |
| `START_HERE.md` | 97 | Onboarding doc | `docs/` or `docs/user-guides/` | High-level getting-started guide | README already links to it? Verify before moving |
| `pyproject.toml` | 116 | Project metadata | **keep root** | Core Python project config | Required by `uv`, `pip`, `ruff`, `mypy` |
| `.gitignore_parent` | 118 | Git template | **delete** or `docs/archive/` | Looks like a backup/template gitignore; current `.gitignore` is authoritative | Verify not referenced by any tooling |
| `Makefile` | 119 | Build automation | **keep root** | Standard `make` entry point | Conventionally root-located |
| `analysis_results.txt` | 132 | Generated output | `docs/validation/` or `data/` | Referenced from `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` | Move with reference update |
| `.gitignore` | 150 | Git config | **keep root** | Git ignore rules | Must stay in root |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | Architecture doc | `docs/architecture/` | Architecture clarification | Pair with other architecture docs |

---

## Candidates (200–300 LoC)

| File | LoC | Category | Proposed Destination | Rationale | Notes |
|------|-----|----------|----------------------|-----------|-------|
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | Process doc | `docs/development/` or `docs/user-guides/` | Execution flow + config guide | Relocatable documentation |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | Analysis doc | `docs/architecture-design/` | Dependency analysis and recommendations | Fits with architecture-design docs |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | Glossary doc | `docs/` or `docs/user-guides/` | Terminology/glossary | Useful as a top-level doc; could stay or move |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | Proposal | `docs/architecture-design/` or `docs/migration/` | Package reorganization proposal | Already referenced by this analysis |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | Decision record | `docs/architecture-design/` | Architecture decision record | Pair with other ADRs |

---

## Recommended Action Plan

### 1. Merge tool configs into `pyproject.toml` (low risk)
- `.ruffignore` → `[tool.ruff]` exclude patterns
- `pytest.ini` → `[tool.pytest.ini_options]`
- `mypy.ini` → `[tool.mypy]`

This removes 3 files from the root without changing behavior.

### 2. Move scripts to `scripts/` (low/medium risk)
- `organize_root_scripts.sh` → `scripts/maintenance/`
- `analyze_md_files.py` → `scripts/analysis/`
- `start-with-minio.sh` → `scripts/deployment/` (update relative paths)
- `start.sh` → `scripts/deployment/` or keep root (update `SCRIPT_DIR` logic if moved)

### 3. Move environment examples to `configs/` (low risk)
- `.env.example` → `configs/`
- `.env.production.example` → `configs/`
- Update `.gitignore` and setup docs to point to new location

### 4. Move documentation to `docs/` (low risk)
- `ARCHITECTURE_CLARIFICATION.md` → `docs/architecture/`
- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` → `docs/development/`
- `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` → `docs/architecture-design/`
- `TERMINOLOGY_CLARIFICATION.md` → `docs/user-guides/` or keep as top-level doc
- `PACKAGE_REORGANIZATION_PROPOSAL.md` → `docs/architecture-design/` or `docs/migration/`
- `FINAL_ARCHITECTURE_DECISION.md` → `docs/architecture-design/`
- `START_HERE.md` → `docs/user-guides/`
- `analysis_results.txt` → `docs/validation/` (update `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` link)

### 5. Delete or archive (low risk)
- `package-lock.json` (orphaned)
- `.DS_Store` (OS artifact, ensure ignored)
- `.gitignore_parent` (verify unused, then delete or archive)
- `streamlit_requirements.txt` (deprecated; if deleted, update 6 references in docs/scripts)

### 6. Keep in root (required)
- `.python-version`
- `.gitmodules`
- `.gitignore`
- `pyproject.toml`
- `Makefile`
- `docker-compose.yml`
- `.bobignore` (unless verified to work under `.bob/`)
- `README.md` (larger, but root anchor)
- `streamlit_app_progressive.py` (larger, root anchor; or move to `src/streamlit_ui/pages/` per `PACKAGE_REORGANIZATION_PROPOSAL.md`)

---

## Cross-References to Update

If `streamlit_requirements.txt` is moved/deleted, update these references:
- `docs/user-guides/README_PARENT.md:103`
- `scripts/deployment/run_streamlit_modular.sh:11`
- `scripts/deployment/run_streamlit.sh:27`
- `docs/streamlit/STREAMLIT_README.md:45`
- `docs/development/UV_PYTHON_FIX.md:37,78,117,148`
- `docs/development/GITHUB_ISSUES.md:172`

If `analysis_results.txt` is moved, update:
- `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md:279`

If `start.sh` or `start-with-minio.sh` are moved, update `Makefile` and any README/runner docs that invoke them from the root.

---

## Related Documents

- `PACKAGE_REORGANIZATION_PROPOSAL.md` — broader package separation (UI → `streamlit_ui/`)
- `organize_root_scripts.sh` — prior root-script cleanup that moved many files into `scripts/`
- `docs/README.md` — documentation index
- `scripts/README.md` — script inventory and conventions

---

## Next Step

Pick the lowest-risk items first (config merges into `pyproject.toml`, doc moves, and deletions), then handle the scripts that require path adjustments. This candidate list can be turned into a single migration script if desired.
