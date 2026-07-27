# Small File Relocation Candidates — Root Folder

## Actions already taken on this branch

The following low-risk moves were completed after the initial analysis:

- `package-lock.json` deleted (no `package.json`, already ignored by git).
- `organize_root_scripts.sh` moved to `scripts/maintenance/organize_root_scripts.sh`.
- `analyze_md_files.py` moved to `scripts/utils/analyze_md_files.py`.
- `analysis_results.txt` moved to `docs/validation/analysis_results.txt`.
- Reference in `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` updated to point to the new location.

The table below documents the state **before** these moves, so the rationale and risk assessment remain readable.

## Scope

- **Folder analyzed:** repository root (`/workspace` / `uqlab-streamlit/`)
- **Threshold:** files with ≤ 300 lines of code/content
- **Goal:** identify small files that are logically misplaced and could be relocated to a more appropriate folder, or removed if they are orphaned.

## Method

1. List all files directly in the repository root.
2. Count non-empty lines (via `wc -l`).
3. Ignore standard project files that conventionally live at the root (e.g., `README.md`, `pyproject.toml`, `Makefile`, `.env` examples, lockfiles).
4. Search the codebase for references to each candidate to assess relocation risk.
5. Propose a target folder and a risk level for each candidate.

## Root files ≤ 300 LoC

| File | LoC | Category | Current role | References found | Proposed target | Risk | Notes |
|------|-----|----------|--------------|------------------|-----------------|------|-------|
| `package-lock.json` | 6 | orphaned | No corresponding `package.json` exists anywhere in the repo. | Only in `.gitignore` / `.gitignore_parent` | **Delete** | Low | ✅ Completed — deleted. |
| `streamlit_requirements.txt` | 10 | config | Streamlit-specific pip requirements. | Referenced by `scripts/deployment/run_streamlit.sh`, `scripts/deployment/run_streamlit_modular.sh`, `docs/user-guides/README_PARENT.md`, `docs/streamlit/STREAMLIT_README.md`, `docs/development/UV_PYTHON_FIX.md`, `docs/development/GITHUB_ISSUES.md` | Keep at root **or** move to `scripts/deployment/` | Medium | Many docs and scripts reference the root path. Moving it would require updating all of them. Keeping it is reasonable because it is a top-level deployment dependency. |
| `.python-version` | 1 | config | Python version pin for pyenv/uv. | None | Keep at root | Low | Standard pyenv/uv convention. |
| `.gitmodules` | 3 | config | Git submodule configuration. | None | Keep at root | Low | Required at the repository root by Git. |
| `.bobignore` | 14 | config | Bob agent ignore rules. | None | Keep at root | Low | Bob-specific configuration convention. |
| `.ruffignore` | 17 | config | Ruff linter ignore rules. | None | Keep at root | Low | Standard ruff convention. |
| `.env.example` | 29 | config | Environment variable template. | None | Keep at root | Low | Standard convention for env templates. |
| `docker-compose.yml` | 44 | config | Docker Compose stack definition. | None | Keep at root | Low | Standard convention. |
| `pytest.ini` | 46 | config | pytest configuration. | None | Keep at root | Low | Standard convention. |
| `organize_root_scripts.sh` | 57 | utility | One-off maintenance script that moves files from root into `scripts/` and `tests/`. | None | `scripts/maintenance/` | Low | ✅ Completed — moved to `scripts/maintenance/organize_root_scripts.sh`. |
| `start.sh` | 61 | entry point | Starts the progressive Streamlit app via `uv`. | Referenced in `streamlit_requirements.txt` | Keep at root **or** `scripts/deployment/` | Medium | Documented entry point; moving it would break the convention of a root-level start script. |
| `analyze_md_files.py` | 63 | utility | Categorizes root-level `.md` files by keyword. | None | `scripts/utils/` | Low | ✅ Completed — moved to `scripts/utils/analyze_md_files.py`. |
| `.env.production.example` | 68 | config | Production env template. | None | Keep at root | Low | Standard convention. |
| `mypy.ini` | 80 | config | mypy type-checker configuration. | None | Keep at root | Low | Standard convention. |
| `start-with-minio.sh` | 88 | entry point | Starts MinIO + uvicorn backend. | Referenced in `docs/setup/minio.md`, `docs/architecture/minio-storage.md` | Keep at root **or** `scripts/deployment/` | Medium | Docs reference the root path; moving it would require doc updates. |
| `START_HERE.md` | 97 | documentation | Onboarding guide. | None | Keep at root **or** `docs/user-guides/` | Low | Intentionally at root for visibility; moving it would reduce discoverability. |
| `pyproject.toml` | 116 | config | Python project metadata and tool config. | None | Keep at root | Low | Standard convention. |
| `.gitignore_parent` | 118 | config | Parent-level ignore rules. | None | Keep at root | Low | Appears intentional for nested repo setups. |
| `Makefile` | 119 | config | Build/task automation. | None | Keep at root | Low | Standard convention. |
| `analysis_results.txt` | 132 | artifact | Output of `analyze_md_files.py`. | Referenced in `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` line 279 | `docs/validation/` or `archive/` | Low | ✅ Completed — moved to `docs/validation/analysis_results.txt`; doc reference updated. |
| `.gitignore` | 150 | config | Git ignore rules. | None | Keep at root | Low | Standard convention. |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | documentation | Architecture clarification doc. | None | `docs/architecture/` | Low | Does not need to be at root. |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | documentation | Execution flow guide. | None | `docs/execution/` or `docs/user-guides/` | Low | Root placement is not required. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | documentation | Dependency analysis report. | None | `docs/development/` or `docs/analysis/` | Low | Better suited under docs. |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | documentation | Terminology glossary. | None | `docs/` or `docs/user-guides/` | Low | Could be moved under docs for consistency. |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | documentation | Package reorganization proposal. | None | `docs/development/` | Low | Already have `docs/development/`; fits there. |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | documentation | Architecture decision record. | None | `docs/architecture/` or `docs/development/` | Low | Standard ADR location would be under docs. |

## Clear-cut relocation candidates

The following files are the strongest candidates for immediate relocation because they are either orphaned, generated artifacts, or maintenance utilities that do not need root-level visibility:

1. **`package-lock.json`** → delete (no `package.json`, already ignored).
2. **`organize_root_scripts.sh`** → `scripts/maintenance/organize_root_scripts.sh`.
3. **`analyze_md_files.py`** → `scripts/utils/analyze_md_files.py`.
4. **`analysis_results.txt`** → `docs/validation/analysis_results.txt` (update the reference in `HYPOTHESIS_VERIFICATION_RESULTS.md`).

## Keep at root

These files should remain at the root because they are standard project files, entry points, or heavily referenced:

- `README.md`
- `START_HERE.md` (onboarding discoverability)
- `pyproject.toml`, `pytest.ini`, `mypy.ini`, `Makefile`
- `.env.example`, `.env.production.example`, `.python-version`
- `.gitignore`, `.gitignore_parent`, `.gitmodules`, `.bobignore`, `.ruffignore`
- `docker-compose.yml`
- `streamlit_app_progressive.py`
- `start.sh`, `start-with-minio.sh`, `streamlit_requirements.txt`

## Documentation candidates (optional)

The following markdown files are small enough to move under `docs/` for a cleaner root, but they are low-risk moves that mainly improve aesthetics:

- `ARCHITECTURE_CLARIFICATION.md` → `docs/architecture/`
- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` → `docs/execution/` or `docs/user-guides/`
- `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` → `docs/development/`
- `TERMINOLOGY_CLARIFICATION.md` → `docs/user-guides/`
- `PACKAGE_REORGANIZATION_PROPOSAL.md` → `docs/development/`
- `FINAL_ARCHITECTURE_DECISION.md` → `docs/architecture/`

## Recommended next steps

1. **Low-risk cleanup:** delete `package-lock.json` and move `organize_root_scripts.sh` and `analyze_md_files.py` into the appropriate `scripts/` subdirectories.
2. **Artifact cleanup:** move `analysis_results.txt` into `docs/validation/` and update the single doc reference.
3. **Documentation consolidation:** move the six markdown docs listed above into `docs/` subfolders if a cleaner root is desired.
4. **Keep entry points:** leave `start.sh`, `start-with-minio.sh`, and `streamlit_requirements.txt` at the root because they are referenced by deployment scripts and user guides.
