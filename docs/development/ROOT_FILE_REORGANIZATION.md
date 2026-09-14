# Root File Reorganization Plan

This document inventories root-level files that are under **300 lines of code**
and identifies where they can be relocated. It updates the older
[`ROOT_LEVEL_CLEANUP_ANALYSIS.md`](./ROOT_LEVEL_CLEANUP_ANALYSIS.md) to reflect
the current repository state.

## Current root file sizes

| File | Lines | Category | Recommendation |
|------|-------|----------|----------------|
| `.python-version` | 1 | Python version pin | **Keep in root** |
| `.gitmodules` | 3 | Git config | **Keep in root** |
| `package-lock.json` | 6 | npm lockfile (empty project) | **Keep in root** or remove if unused |
| `streamlit_requirements.txt` | 10 | Python requirements | Move to `scripts/deployment/` or merge into `requirements.txt` |
| `.DS_Store` | 13 | macOS metadata | **Delete** |
| `.bobignore` | 14 | Bob tool config | **Keep in root** |
| `.ruffignore` | 17 | Ruff config | **Keep in root** |
| `.env.example` | 29 | Env template | **Keep in root** |
| `docker-compose.yml` | 44 | Docker orchestration | **Keep in root** |
| `pytest.ini` | 46 | Test config | **Keep in root** (also exists in `tests/`) |
| `organize_root_scripts.sh` | 57 | Maintenance script | ✅ Moved to `scripts/maintenance/organize_root_files.sh` |
| `start.sh` | 61 | Startup script | **Keep in root** (referenced by Docker/deployment) |
| `analyze_md_files.py` | 63 | Analysis helper | ✅ Moved to `scripts/analysis/analyze_md_files.py` |
| `.env.production.example` | 68 | Env template | **Keep in root** |
| `mypy.ini` | 80 | Type-checker config | **Keep in root** |
| `start-with-minio.sh` | 88 | Startup script | **Keep in root** (referenced by Docker/deployment) |
| `START_HERE.md` | 97 | Entry guide | **Keep in root** |
| `pyproject.toml` | 116 | Project config | **Keep in root** |
| `.gitignore_parent` | 118 | Git ignore | **Keep in root** or merge into `.gitignore` |
| `Makefile` | 119 | Build tasks | **Keep in root** |
| `analysis_results.txt` | 132 | Validation results | ✅ Moved to `docs/validation/analysis_results.txt` |
| `.gitignore` | 150 | Git ignore | **Keep in root** |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | Architecture doc | Move to `docs/architecture/` |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | Architecture/flow doc | Move to `docs/architecture/` |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | Architecture doc | Move to `docs/architecture/` |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | Architecture doc | Move to `docs/architecture/` |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | Architecture proposal | Move to `docs/architecture/` |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | Architecture decision | Move to `docs/architecture/` |
| `README.md` | 366 | Main README | **Keep in root** |
| `streamlit_app_progressive.py` | 370 | UI entry point | **Keep in root** |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | Architecture proposal | Move to `docs/architecture/` |
| `IMPORT_GUIDE.md` | 491 | Development guide | Move to `docs/development/` |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | Architecture/flow doc | Move to `docs/architecture/` |

## Actions already taken

- `analysis_results.txt` → `docs/validation/analysis_results.txt`
  - Reference in `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` is
    still valid (same directory).
- `analyze_md_files.py` → `scripts/analysis/analyze_md_files.py`
- `organize_root_scripts.sh` → `scripts/maintenance/organize_root_files.sh`
  - Updated to operate on the current root state and to support `--dry-run`.

## Remaining candidates

### Safe to move now (low risk)

- `streamlit_requirements.txt` → `scripts/deployment/streamlit_requirements.txt`
  - Verify no CI/Dockerfile references it before moving.
- `.DS_Store` → **delete** (it is a macOS metadata file).

### Requires reference updates before moving

These Markdown files are linked from `README.md` and from each other. Move them
in a single pass and update all relative links:

```text
ARCHITECTURE_CLARIFICATION.md                → docs/architecture/
ARCHITECTURE_IMPROVEMENT_PROPOSAL.md         → docs/architecture/
COMPLETE_SYSTEM_FLOW.md                      → docs/architecture/
DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md → docs/architecture/
EXECUTION_FLOW_AND_CONFIG_GUIDE.md           → docs/architecture/
FINAL_ARCHITECTURE_DECISION.md               → docs/architecture/
IMPORT_GUIDE.md                              → docs/development/
PACKAGE_REORGANIZATION_PROPOSAL.md           → docs/architecture/
TERMINOLOGY_CLARIFICATION.md                 → docs/architecture/
```

After moving, update `README.md` links such as:

```markdown
Full flow diagram and FAQ: [EXECUTION_FLOW_AND_CONFIG_GUIDE.md](docs/architecture/EXECUTION_FLOW_AND_CONFIG_GUIDE.md).
Package boundaries: [ARCHITECTURE_CLARIFICATION.md](docs/architecture/ARCHITECTURE_CLARIFICATION.md).
```

### Must stay in root

- `README.md`, `START_HERE.md` — entry points.
- `pyproject.toml`, `Makefile`, `pytest.ini`, `mypy.ini`, `.gitignore`,
  `.gitmodules`, `.bobignore`, `.ruffignore`, `.python-version` — tooling
  configuration.
- `.env.example`, `.env.production.example` — environment templates.
- `docker-compose.yml` — Docker orchestration.
- `start.sh`, `start-with-minio.sh` — referenced by backend Docker and
  deployment scripts.
- `streamlit_app_progressive.py` — primary UI entry point.
- `package-lock.json` — only keep if the project still uses npm; otherwise
  remove.

## Automation

Run the maintenance script to apply the safe moves:

```bash
bash scripts/maintenance/organize_root_files.sh
```

Preview changes without applying:

```bash
bash scripts/maintenance/organize_root_files.sh --dry-run
```

## Notes

- Files larger than 300 lines (`ARCHITECTURE_IMPROVEMENT_PROPOSAL.md`,
  `IMPORT_GUIDE.md`, `COMPLETE_SYSTEM_FLOW.md`) are still candidates for
  relocation because they are documentation, not code or configuration.
- The older [`ROOT_LEVEL_CLEANUP_ANALYSIS.md`](./ROOT_LEVEL_CLEANUP_ANALYSIS.md)
  is preserved for historical context but references many files that no longer
  exist at the root.
