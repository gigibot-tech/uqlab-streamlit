# Root-Level Small-File Relocation Candidates

This analysis reviews files in the repository **root folder** (`/workspace`, i.e. `uqlab-streamlit/`) that are **≤ 300 lines of code** and assesses whether they can be moved to a more appropriate sub-directory.

## Method

1. Count lines with `wc -l` for every file at repository root.
2. Search for in-repo references to each candidate with `rg <filename>`.
3. Decide whether the file **must stay at root**, can be **moved safely**, or can be **moved after updating references**.

> Line counts include blanks and comments, so they are a rough size metric, not pure LoC.

---

## Summary

| Category | Count | Notes |
|----------|-------|-------|
| Keep at root (config/entry points) | ~15 | Essential project files such as `pyproject.toml`, `Makefile`, `.env` examples, Docker Compose, etc. |
| Safe to move now (no references) | 2 | `analyze_md_files.py`, `organize_root_scripts.sh` |
| Movable with reference updates | ~7 | Docs and artifacts that are linked from README or other docs |
| Candidates for deletion | 2 | `.DS_Store`, `package-lock.json` (no `package.json`) |

---

## Files ≤ 200 lines

| File | Lines | References found | Proposed action | Proposed destination | Notes |
|------|-------|------------------|-----------------|----------------------|-------|
| `.python-version` | 1 | pyenv config | **Keep** | root | Required by pyenv/uv for version pinning |
| `.gitmodules` | 3 | Git submodules | **Keep** | root | Git requires this at repo root |
| `package-lock.json` | 3 | `.gitignore` only | **Delete** | — | No `package.json` exists; stale artifact |
| `streamlit_requirements.txt` | 10 | `scripts/deployment/run_streamlit.sh`, `scripts/deployment/run_streamlit_modular.sh`, several docs | Keep or **move + update refs** | `scripts/deployment/` | Used by deployment scripts; could live next to them |
| `.DS_Store` | 13 | None (already `.gitignore`d) | **Delete** | — | macOS metadata file |
| `.bobignore` | 14 | Bob config | **Keep** | root | Tool-specific ignore file |
| `.ruffignore` | 17 | Ruff config | **Keep** | root | Could be merged into `pyproject.toml` later |
| `.env.example` | 29 | README, docs | **Keep** | root | Standard env template location |
| `docker-compose.yml` | 44 | README, backend README, several docs | **Keep** | root | Docker entry point |
| `pytest.ini` | 46 | `pyproject.toml`, docs | **Keep** | root | Test runner config |
| `start.sh` | 61 | `backend/scripts/entrypoint.sh`, `backend/README.md`, `backend/Dockerfile`, `streamlit_requirements.txt` | **Keep** | root | Main launcher for the progressive Streamlit app |
| `organize_root_scripts.sh` | 57 | None | **Move** | `scripts/maintenance/` | One-off cleanup script; not referenced anywhere |
| `analyze_md_files.py` | 63 | None | **Move** | `scripts/analysis/` (create if needed) | Small markdown cataloguer; no callers |
| `.env.production.example` | 68 | `scripts/README.md`, docs | **Keep** | root | Production env template |
| `mypy.ini` | 80 | Docs | **Keep** | root | Type-checker config |
| `start-with-minio.sh` | 88 | `docs/architecture/minio-storage.md` | **Move + update refs** | `scripts/deployment/` | MinIO + backend launcher; logically a deployment script |
| `START_HERE.md` | 97 | `README.md`, `TERMINOLOGY_CLARIFICATION.md`, `streamlit_app_progressive.py`, `docs/features/workflow-config.md` | **Move + update refs** | `docs/setup/` | Onboarding doc; could live under `docs/` |
| `pyproject.toml` | 116 | Many | **Keep** | root | Python project metadata |
| `.gitignore_parent` | 118 | None | Review / merge | root or delete | Looks like a leftover parent `.gitignore`; consider merging into `.gitignore` |
| `Makefile` | 119 | `README.md`, `START_HERE.md` | **Keep** | root | Standard task runner |
| `.gitignore` | 150 | Many | **Keep** | root | Git ignore rules |
| `analysis_results.txt` | 132 | `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` | **Move + update refs** | `docs/validation/` | Hypothesis-verification artifact; logically lives with validation docs |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | `README.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `COMPLETE_SYSTEM_FLOW.md` | **Move + update refs** | `docs/architecture/` | Architecture doc; belongs with other architecture docs |

## Files 201–300 lines

| File | Lines | References found | Proposed action | Proposed destination | Notes |
|------|-------|------------------|-----------------|----------------------|-------|
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | `README.md` | **Move + update refs** | `docs/development/` | Development/execution-flow guide |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | None | **Move** | `docs/development/` | No in-repo references; safe to move |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | None | **Move** | `docs/development/` | No in-repo references; safe to move |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | **Move + update refs** | `docs/development/` | Historical proposal |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | `TERMINOLOGY_CLARIFICATION.md` | **Move + update refs** | `docs/development/` | Architecture decision record |

## Files > 300 lines (shown for context only)

These are not small-file candidates, but are included to complete the root inventory:

| File | Lines | Notes |
|------|-------|-------|
| `README.md` | 366 | Keep at root |
| `streamlit_app_progressive.py` | 370 | Main app; keep at root |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | Could move to `docs/development/` |
| `IMPORT_GUIDE.md` | 491 | Could move to `docs/development/` |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | Referenced; could move to `docs/architecture/` |
| `uv.lock` | 4,626 | Keep at root (uv lockfile) |
| `dependencies.json` | 21,419 | Keep at root (dependency graph artifact) |
| `three_axioms_demonstration.png` | — | Keep at root (diagram asset) |
| `2408.12175v3.pdf` | — | Keep at root (reference paper) |

---

## Recommended immediate actions

1. **Delete stale artifacts**
   - `package-lock.json` (no `package.json`)
   - `.DS_Store` (metadata, already ignored)

2. **Move unreferenced utility scripts**
   - `analyze_md_files.py` → `scripts/analysis/`
   - `organize_root_scripts.sh` → `scripts/maintenance/`

3. **Move docs that have references, then update those references**
   - `ARCHITECTURE_CLARIFICATION.md` → `docs/architecture/`
   - `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` → `docs/development/`
   - `FINAL_ARCHITECTURE_DECISION.md` → `docs/development/`
   - `PACKAGE_REORGANIZATION_PROPOSAL.md` → `docs/development/`
   - `TERMINOLOGY_CLARIFICATION.md` → `docs/development/`
   - `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` → `docs/development/`
   - `START_HERE.md` → `docs/setup/`
   - `analysis_results.txt` → `docs/validation/`

4. **Optional / lower priority**
   - Merge `.gitignore_parent` into `.gitignore` and remove it.
   - Move `streamlit_requirements.txt` → `scripts/deployment/` and update deployment scripts/docs.
   - Move `start-with-minio.sh` → `scripts/deployment/` and update `docs/architecture/minio-storage.md`.

---

## Files that should stay at root

- `.python-version`, `.gitmodules`, `.gitignore`, `.bobignore`, `.ruffignore`
- `.env.example`, `.env.production.example`
- `pyproject.toml`, `pytest.ini`, `mypy.ini`
- `docker-compose.yml`
- `Makefile`
- `README.md`
- `run_fast.py` (already absent from current root; referenced in older cleanup docs)
- `streamlit_app_progressive.py`
- `uv.lock`, `dependencies.json`

---

*Generated on 2026-09-18. Line counts produced with `wc -l` and references checked with `rg`.*
