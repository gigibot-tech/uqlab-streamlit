# Root Level Cleanup Analysis

**Updated**: 2026-10-28  
**Goal**: Identify root-level files under 200–300 LoC that can be relocated.

## Current Root-Level Files (after recent moves)

```text
 1   .python-version
 3   .gitmodules
 6   package-lock.json
10   streamlit_requirements.txt
13   .DS_Store
14   .bobignore
17   .ruffignore
29   .env.example
34   streamlit_app_prefsum.py
44   docker-compose.yml
46   pytest.ini
61   start.sh
68   .env.production.example
80   mypy.ini
88   start-with-minio.sh
97   START_HERE.md
116  pyproject.toml
118  .gitignore_parent
124  Makefile
132  analysis_results.txt
150  .gitignore
171  ARCHITECTURE_CLARIFICATION.md
229  EXECUTION_FLOW_AND_CONFIG_GUIDE.md
234  DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md
274  TERMINOLOGY_CLARIFICATION.md
295  PACKAGE_REORGANIZATION_PROPOSAL.md
299  FINAL_ARCHITECTURE_DECISION.md
366  README.md
372  streamlit_app_progressive.py
416  ARCHITECTURE_IMPROVEMENT_PROPOSAL.md
491  IMPORT_GUIDE.md
498  COMPLETE_SYSTEM_FLOW.md
```

## ✅ KEEP — Essential at Root

| File | LoC | Why keep |
|------|-----|----------|
| `pyproject.toml` | 116 | Python project metadata |
| `Makefile` | 124 | Standard task runner |
| `docker-compose.yml` | 44 | Docker orchestration |
| `.env.example` / `.env.production.example` | 29 / 68 | Environment templates |
| `.gitignore` / `.gitignore_parent` / `.bobignore` / `.ruffignore` | 150 / 118 / 14 / 17 | VCS/Tool config |
| `.python-version` | 1 | Python version pin |
| `.gitmodules` | 3 | Submodule config |
| `package-lock.json` | 6 | npm lockfile |
| `pytest.ini` / `mypy.ini` | 46 / 80 | Test/type config |
| `uv.lock` | 4626 | Dependency lockfile |
| `streamlit_app_progressive.py` | 372 | Main entry point (referenced by Makefile, README) |
| `streamlit_app_prefsum.py` | 34 | PrefSum entry point (referenced by Makefile, docs) |
| `start.sh` | 61 | Startup entry point (referenced by streamlit_requirements.txt) |
| `start-with-minio.sh` | 88 | MinIO startup (referenced by docs/setup/minio.md, docs/architecture/minio-storage.md) |
| `README.md` | 366 | Project README |
| `START_HERE.md` | 97 | Quick-start pointer |
| `2408.12175v3.pdf` | - | Reference paper |
| `three_axioms_demonstration.png` | - | Reference diagram |

## ⚠️ MOVE CANDIDATES — Under 200–300 LoC

### Moved in this cleanup

| File | From | To | LoC | Rationale |
|------|------|-----|-----|-----------|
| `analyze_md_files.py` | root | `scripts/maintenance/analyze_md_files.py` | 63 | Diagnostic/maintenance utility; zero external references |
| `organize_root_scripts.sh` | root | `scripts/maintenance/organize_root_scripts.sh` | 57 | Root-organization script; fits with other maintenance scripts; zero external references |

### Still at root — candidates for future cleanup

| File | LoC | Proposed location | Notes |
|------|-----|-------------------|-------|
| `analysis_results.txt` | 132 | `docs/validation/results.txt` or keep at root | Referenced once by `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`; moving requires updating that link |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | `docs/architecture/` | Referenced by `README.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `COMPLETE_SYSTEM_FLOW.md` |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | `docs/development/` | Referenced by `README.md` |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | `docs/archive/` or `docs/development/` | Proposal doc from 2026-06-24; referenced internally |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | `docs/development/` or `docs/architecture/` | Referenced internally by itself |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | `docs/archive/` or `docs/development/` | Proposal doc from 2026-06-24; referenced by dependency analysis doc |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | `docs/development/` or `docs/architecture/` | Referenced by `TERMINOLOGY_CLARIFICATION.md` |

### Larger docs that could also move

| File | LoC | Proposed location | Notes |
|------|-----|-------------------|-------|
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | `docs/development/` | Proposal doc from 2026-06-24 |
| `IMPORT_GUIDE.md` | 491 | `docs/development/` | Developer guide |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | `docs/development/` | Developer guide |

## 🗂️ Recommended Next Steps

1. **Archive or move 2026-06 proposal docs** (`PACKAGE_REORGANIZATION_PROPOSAL.md`, `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md`, `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`, `FINAL_ARCHITECTURE_DECISION.md`) to `docs/archive/` or `docs/development/`.
2. **Move developer guides** (`IMPORT_GUIDE.md`, `COMPLETE_SYSTEM_FLOW.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `TERMINOLOGY_CLARIFICATION.md`, `ARCHITECTURE_CLARIFICATION.md`) into `docs/development/` and `docs/architecture/`.
3. **Decide on `analysis_results.txt`** — either keep at root or relocate to `docs/validation/` and update the reference in `HYPOTHESIS_VERIFICATION_RESULTS.md`.
4. **Update all internal markdown links** after any move.

## Benefits

- Cleaner root: only entry points, config, and the primary README remain.
- Docs live under `docs/` where existing feature, validation, and development docs already live.
- Scripts live under `scripts/maintenance/` alongside other cleanup/diagnostic tools.
