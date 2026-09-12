# Root-Level Small-File Relocation Report

**Scope:** Files sitting directly in the repository root (`/workspace`) that are below the 200/300 line thresholds, and whether they can be moved to a more specific home.

**Thresholds used:**
- **<200 LoC** — very small; strong relocation candidate unless it is a project-level config or entry point.
- **200–300 LoC** — small; relocate if a clear target folder exists and references can be updated cheaply.

## Relocations already applied (safe, no internal references broken)

| File | Lines | From | To | Rationale |
|------|-------|------|----|-----------|
| `analyze_md_files.py` | 63 | root | `scripts/maintenance/analyze_md_files.py` | Root-level markdown analyzer; belongs with other maintenance scripts. Updated to scan `REPO_ROOT` so it still works from its new location. |
| `organize_root_scripts.sh` | 57 | root | `scripts/maintenance/organize_root_scripts.sh` | Script whose only job is to organize root scripts; self-evidently belongs under `scripts/maintenance`. Added `cd` to repo root so it still runs correctly when invoked from anywhere. |
| `analysis_results.txt` | 132 | root | `docs/validation/analysis_results.txt` | Full validation results referenced only by `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`. Co-locating the artifact with the doc that consumes it removes root clutter and keeps the link relative. |

## Remaining candidates under 300 LoC

| File | LoC | Proposal | Rationale / Blocker |
|------|-----|----------|---------------------|
| `streamlit_requirements.txt` | 10 | `src/streamlit_ui/requirements.txt` or `requirements/streamlit.txt` | Tiny requirements file. Many docs reference it as `./streamlit_requirements.txt`; moving it requires updating those references. |
| `start.sh` | 61 | `scripts/deployment/start.sh` | Thin deployment/start script. Referenced in backend docs and MinIO docs; the `SCRIPT_DIR` logic must be updated to use repo root after the move. |
| `start-with-minio.sh` | 88 | `scripts/deployment/start-with-minio.sh` | Same as above. Starts Docker Compose and the backend; needs `cd` to repo root. |
| `START_HERE.md` | 97 | `docs/START_HERE.md` | Onboarding doc. Referenced from `README.md` and feature docs; moving it needs link updates. |
| `.gitignore_parent` | 118 | `.docs/` or delete if unused | Looks like a leftover parent-repo ignore file. Verify it is still needed before moving. |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | `docs/architecture/` | Architecture decision doc. Linked from `README.md` and `COMPLETE_SYSTEM_FLOW.md`. |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | `docs/user-guides/` or `docs/architecture/` | User-facing flow guide. Linked from `README.md`. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | `docs/proposals/` or `docs/decisions/` | Historical analysis / proposal. |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | `docs/architecture/` | Superseded terminology doc. Moving it would need to update the link in itself. |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | `docs/proposals/` | A proposal document. |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | `docs/decisions/` | Architecture decision record. |

## Files above 300 LoC that also do not belong at root

| File | LoC | Proposal | Rationale |
|------|-----|----------|-----------|
| `streamlit_app_progressive.py` | 370 | `src/streamlit_ui/pages/progressive_app.py` | Already identified in `PACKAGE_REORGANIZATION_PROPOSAL.md` as root-level UI code that should live in a dedicated `streamlit_ui` package. |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | `docs/proposals/` | Historical proposal. |
| `IMPORT_GUIDE.md` | 491 | `docs/` or `docs/development/` | Long reference doc. |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | `docs/architecture/` | System-flow reference. |

## Files that should stay at the root

| File | LoC | Reason |
|------|-----|--------|
| `.python-version` | 1 | pyenv version pinning. |
| `.gitmodules` | 3 | Git submodule configuration. |
| `package-lock.json` | 6 | If there is still an npm-based frontend, keep; otherwise delete. |
| `.DS_Store` | 13 | Should be removed and gitignored, not moved. |
| `.bobignore` | 14 | Tool-specific ignore file. |
| `.ruffignore` | 17 | Tool-specific ignore file. |
| `.env.example` | 29 | Environment template. |
| `docker-compose.yml` | 44 | Docker entry point. |
| `pytest.ini` | 46 | Test runner configuration. |
| `.env.production.example` | 68 | Environment template. |
| `mypy.ini` | 80 | Type-checker configuration. |
| `pyproject.toml` | 116 | Project metadata and tool config. |
| `Makefile` | 119 | Build/task runner entry point. |
| `.gitignore` | 150 | Git ignore rules. |
| `README.md` | 366 | Repository landing page. |
| `uv.lock` | 4626 | Dependency lockfile; root is correct. |
| `dependencies.json` | 21419 | Dependency inventory; root is acceptable. |
| `2408.12175v3.pdf` | binary | Reference paper. |
| `three_axioms_demonstration.png` | binary | Diagram asset. |

## Recommended next steps

1. **Low-risk moves** — relocate the remaining docs (`ARCHITECTURE_CLARIFICATION.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `TERMINOLOGY_CLARIFICATION.md`, etc.) into `docs/architecture/`, `docs/user-guides/`, or `docs/proposals/` and update the links in `README.md` and other docs.
2. **Start scripts** — move `start.sh` and `start-with-minio.sh` into `scripts/deployment/` and update their internal `cd`/`SCRIPT_DIR` assumptions plus the references in `backend/README.md`, `docs/architecture/minio-storage.md`, and `docs/setup/minio.md`.
3. **Streamlit entry point** — follow the existing `PACKAGE_REORGANIZATION_PROPOSAL.md` plan and move `streamlit_app_progressive.py` into a new `src/streamlit_ui/pages/` package, updating `pyproject.toml` scripts/entry points if necessary.
4. **Dot-file cleanup** — remove `.DS_Store` from version control and add it to `.gitignore`; review whether `.gitignore_parent` is still needed.

## Method

Line counts were generated with `wc -l` on the root-level files. References were checked with `rg --no-follow -l '<filename>'` so broken symlinks (`uq_benchmarks`, `uq_classification`) did not skew the search.
