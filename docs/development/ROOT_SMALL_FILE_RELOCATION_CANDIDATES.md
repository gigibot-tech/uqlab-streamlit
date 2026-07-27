# Root Small-File Relocation Candidates

**Branch**: `cursor/small-file-relocation-candidates-742a`  
**Date**: 2026-07-27  
**Scope**: Project root (`/workspace`) files with ≤ 300 lines of code (LoC) and whether they can be relocated to existing subdirectories.

---

## Summary

The project root contained **19 small files** (≤ 300 LoC) that were candidates for relocation. After analyzing their purpose, internal references, and the existing folder structure, **9 files were moved** to more appropriate locations and **all internal references were updated**. The remaining 10 files were kept at root because they are entry points, tool configuration files, or deprecated artifacts that require a separate decision (delete vs. archive).

---

## Methodology

- Counted total lines with `wc -l` for every non-binary, non-symlink file at the project root.
- Read each small file to determine its purpose and role.
- Searched the repository for references to each candidate file (using `rg -L --no-follow` to avoid broken symlinks such as `uq_benchmarks` and `uq_classification`).
- Chose relocation targets based on the existing folder conventions in `docs/`, `scripts/`, and `data/`.

---

## Root files ≤ 300 LoC (before changes)

### < 200 LoC

| Lines | File | Purpose | Decision |
|------:|------|---------|----------|
| 6 | `package-lock.json` | Empty npm lockfile from old project name (`walaris-cen`); no `package.json` exists. | **Keep at root** — recommend deleting or archiving separately. |
| 10 | `streamlit_requirements.txt` | Deprecated pip requirements; `uv`/`pyproject.toml` now handle deps. | **Keep at root** — referenced by deployment scripts; deprecate separately. |
| 44 | `docker-compose.yml` | MinIO services for local storage backend. | **Keep at root** — referenced by backend docs, `Makefile`, and deployment guides. |
| 46 | `pytest.ini` | Pytest configuration. | **Keep at root** — referenced by `pyproject.toml` and docs; could be merged into `pyproject.toml` later. |
| 57 | `organize_root_scripts.sh` | One-shot maintenance script that moves root scripts to `scripts/`. | **Moved** → `scripts/maintenance/organize_root_scripts.sh`. |
| 61 | `start.sh` | Main entry point to start the Streamlit frontend. | **Keep at root** — referenced by `README.md`, `backend/` entrypoint, and `Makefile`. |
| 63 | `analyze_md_files.py` | Diagnostic script that categorizes root markdown files. | **Moved** → `scripts/maintenance/analyze_md_files.py`. |
| 80 | `mypy.ini` | MyPy configuration. | **Keep at root** — referenced by docs; could be merged into `pyproject.toml` later. |
| 88 | `start-with-minio.sh` | Entry point to start MinIO + uvicorn backend. | **Keep at root** — referenced by MinIO docs. |
| 97 | `START_HERE.md` | Quick orientation guide for the repo. | **Keep at root** — acts as a landing doc; could be merged into `README.md` later. |
| 116 | `pyproject.toml` | Python workspace metadata and tool config. | **Keep at root** — required by `uv`/`setuptools`. |
| 119 | `Makefile` | Standard development commands. | **Keep at root** — required by workflow and docs. |
| 132 | `analysis_results.txt` | Generated disentanglement experiment results. | **Moved** → `data/analysis_results.txt`. |
| 171 | `ARCHITECTURE_CLARIFICATION.md` | Package-boundary clarification doc. | **Moved** → `docs/architecture/ARCHITECTURE_CLARIFICATION.md`. |

### 200–300 LoC

| Lines | File | Purpose | Decision |
|------:|------|---------|----------|
| 229 | `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | Execution flow diagram and FAQ. | **Moved** → `docs/EXECUTION_FLOW_AND_CONFIG_GUIDE.md`. |
| 234 | `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | Dependency audit and recommendation. | **Moved** → `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`. |
| 274 | `TERMINOLOGY_CLARIFICATION.md` | Terminology glossary / proposed CLI move. | **Moved** → `docs/TERMINOLOGY_CLARIFICATION.md`. |
| 295 | `PACKAGE_REORGANIZATION_PROPOSAL.md` | Proposal to move UI components out of ML core. | **Moved** → `docs/architecture/PACKAGE_REORGANIZATION_PROPOSAL.md`. |
| 299 | `FINAL_ARCHITECTURE_DECISION.md` | Final architecture decision record. | **Moved** → `docs/architecture/FINAL_ARCHITECTURE_DECISION.md`. |

---

## Files moved

| Original location | New location | Rationale |
|-------------------|--------------|-----------|
| `organize_root_scripts.sh` | `scripts/maintenance/organize_root_scripts.sh` | Maintenance script; matches existing `scripts/maintenance/` scripts. |
| `analyze_md_files.py` | `scripts/maintenance/analyze_md_files.py` | Diagnostic/maintenance utility; matches existing `scripts/maintenance/` scripts. |
| `analysis_results.txt` | `data/analysis_results.txt` | Generated data artifact; `data/` is the intended output directory. |
| `ARCHITECTURE_CLARIFICATION.md` | `docs/architecture/ARCHITECTURE_CLARIFICATION.md` | Architecture documentation; matches `docs/architecture/` convention. |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | `docs/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | Top-level guide; placed alongside other main docs like `docs/UQLAB_FLOW.md`. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | Development/analysis note; matches `docs/development/` convention. |
| `TERMINOLOGY_CLARIFICATION.md` | `docs/TERMINOLOGY_CLARIFICATION.md` | Top-level terminology guide; placed alongside other main docs. |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | `docs/architecture/PACKAGE_REORGANIZATION_PROPOSAL.md` | Architecture proposal; matches `docs/architecture/` convention. |
| `FINAL_ARCHITECTURE_DECISION.md` | `docs/architecture/FINAL_ARCHITECTURE_DECISION.md` | Architecture decision record; matches `docs/architecture/` convention. |

---

## Reference updates

The following files were updated to point to the new locations:

- `README.md` — links to `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` and `ARCHITECTURE_CLARIFICATION.md`.
- `COMPLETE_SYSTEM_FLOW.md` — link to `ARCHITECTURE_CLARIFICATION.md`.
- `docs/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` — link to `ARCHITECTURE_CLARIFICATION.md` (now relative to `docs/`).
- `docs/TERMINOLOGY_CLARIFICATION.md` — link to `FINAL_ARCHITECTURE_DECISION.md` (now relative to `docs/`).
- `docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` — link to `PACKAGE_REORGANIZATION_PROPOSAL.md` (now relative to `docs/development/`).
- `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` — link to `analysis_results.txt` (now relative to `docs/validation/`).

All moves were performed with `git mv` to preserve file history.

---

## Files kept at root (with rationale)

| File | Lines | Reason to keep at root |
|------|------:|------------------------|
| `package-lock.json` | 6 | No `package.json` exists; likely stale. Kept for now, but candidate for deletion or `archive/`. |
| `streamlit_requirements.txt` | 10 | Deprecated but still referenced by deployment scripts; needs separate deprecation PR. |
| `docker-compose.yml` | 44 | Docker entry point; expected at root by docs, `Makefile`, and backend setup. |
| `pytest.ini` | 46 | Tool config expected at root; could be merged into `pyproject.toml` later. |
| `start.sh` | 61 | Primary frontend entry point referenced by README and backend. |
| `mypy.ini` | 80 | Tool config expected at root; could be merged into `pyproject.toml` later. |
| `start-with-minio.sh` | 88 | Backend/MinIO entry point referenced by docs. |
| `START_HERE.md` | 97 | Landing doc; could be merged into `README.md` later. |
| `pyproject.toml` | 116 | Required project metadata file. |
| `Makefile` | 119 | Standard root build/development interface. |

---

## Root files > 300 LoC (not in scope)

| Lines | File | Note |
|------:|------|------|
| 366 | `README.md` | Must stay at root. |
| 370 | `streamlit_app_progressive.py` | Main Streamlit app; referenced by `Makefile` and `start.sh`. The `PACKAGE_REORGANIZATION_PROPOSAL.md` intentionally keeps it at root. |
| 416 | `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | Architecture doc; could be moved to `docs/architecture/` in a follow-up. |
| 491 | `IMPORT_GUIDE.md` | Guide doc; could be moved to `docs/user-guides/` in a follow-up. |
| 498 | `COMPLETE_SYSTEM_FLOW.md` | Main flow doc; referenced by `README.md`; could be moved to `docs/` in a follow-up. |
| 4,626 | `uv.lock` | Dependency lock file; must stay at root. |
| 21,419 | `dependencies.json` | Large generated dependency dump; candidate for `data/` or deletion. |

---

## Recommended next steps

1. **Archive or delete stale artifacts**: `package-lock.json`, `streamlit_requirements.txt`, and `dependencies.json` appear unused or redundant with the `uv`/`pyproject.toml` workflow. Decide whether to move them to an `archive/` folder or remove them entirely.
2. **Merge tool configs**: `pytest.ini` and `mypy.ini` could be consolidated into `pyproject.toml` to eliminate two more root files.
3. **Consolidate entry docs**: `START_HERE.md` and `README.md` overlap; consider merging `START_HERE.md` into `README.md`.
4. **Move remaining large docs**: `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md`, `IMPORT_GUIDE.md`, and `COMPLETE_SYSTEM_FLOW.md` are all documentation that could live under `docs/` once their references are updated.
