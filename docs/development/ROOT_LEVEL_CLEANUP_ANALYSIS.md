# Root Level Cleanup Analysis

**Updated**: 2026-09-12  
**Purpose**: Keep the project root lean by relocating files that are small (< 300 LoC) and already have a natural home elsewhere.

---

## Current Root Files (after latest cleanup)

| File | LoC | Status | Notes |
|------|-----|--------|-------|
| `.python-version` | 1 | KEEP | pyenv version pin. |
| `.gitmodules` | 3 | KEEP | Git submodule config. |
| `package-lock.json` | 6 | KEEP | Generated lockfile. |
| `streamlit_requirements.txt` | 10 | KEEP | Streamlit-specific deps (could merge into `pyproject.toml` later). |
| `.DS_Store` | 13 | DELETE | macOS metadata; should be gitignored. |
| `.bobignore` | 14 | KEEP | Bob agent ignore rules. |
| `.ruffignore` | 17 | KEEP | Ruff ignore rules. |
| `.env.example` | 29 | KEEP | Environment template. |
| `docker-compose.yml` | 44 | KEEP | Docker orchestration. |
| `pytest.ini` | 46 | KEEP | Test config. |
| `start.sh` | 61 | KEEP | Frontend entry-point script. |
| `.env.production.example` | 68 | KEEP | Production env template. |
| `mypy.ini` | 80 | KEEP | Type-checking config. |
| `start-with-minio.sh` | 88 | KEEP | MinIO + backend startup script (referenced by docs). |
| `START_HERE.md` | 97 | KEEP | Onboarding doc referenced by README and workflow docs. |
| `pyproject.toml` | 116 | KEEP | Python project config. |
| `.gitignore_parent` | 118 | KEEP | Parent-level gitignore. |
| `Makefile` | 119 | KEEP | Build / run tasks. |
| `.gitignore` | 150 | KEEP | Git ignore rules. |
| `README.md` | 366 | KEEP | Main project README. |
| `streamlit_app_progressive.py` | 370 | KEEP | Primary UI entry point. |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | KEEP | Architecture proposal (> 300 LoC). |
| `IMPORT_GUIDE.md` | 491 | KEEP | Import guide (> 300 LoC). |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | KEEP | System flow doc (> 300 LoC). |
| `uv.lock` | 4,626 | KEEP | UV lockfile. |
| `dependencies.json` | 21,419 | KEEP | Dependency analysis output. |
| `three_axioms_demonstration.png` | — | KEEP | Reference diagram. |
| `2408.12175v3.pdf` | — | KEEP | Reference paper. |

---

## Relocated in This Cleanup

| Original root path | New path | Reason |
|--------------------|----------|--------|
| `organize_root_scripts.sh` | `scripts/maintenance/organize_root_scripts.sh` | Maintenance helper; belongs with other maintenance scripts. |
| `analyze_md_files.py` | `scripts/diagnostics/analyze_md_files.py` | Small diagnostic script for categorising markdown files. |
| `analysis_results.txt` | `data/analysis_results.txt` | Generated experiment results, not source/docs. |
| `ARCHITECTURE_CLARIFICATION.md` | `docs/architecture/ARCHITECTURE_CLARIFICATION.md` | Small architecture doc. |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | `docs/architecture/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | Small architecture/flow doc. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | `docs/architecture/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | Small architecture/proposal doc. |
| `TERMINOLOGY_CLARIFICATION.md` | `docs/architecture/TERMINOLOGY_CLARIFICATION.md` | Small terminology doc. |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | `docs/architecture/PACKAGE_REORGANIZATION_PROPOSAL.md` | Small package-reorg proposal. |
| `FINAL_ARCHITECTURE_DECISION.md` | `docs/architecture/FINAL_ARCHITECTURE_DECISION.md` | Small architecture-decision doc. |

### References updated

- `README.md` → points to relocated `docs/architecture/EXECUTION_FLOW_AND_CONFIG_GUIDE.md` and `docs/architecture/ARCHITECTURE_CLARIFICATION.md`.
- `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md` → points to `data/analysis_results.txt`.
- `COMPLETE_SYSTEM_FLOW.md` → points to `docs/architecture/ARCHITECTURE_CLARIFICATION.md`.

---

## Remaining Candidates for Future Cleanups

| File | LoC | Proposed Action | Blocker / Notes |
|------|-----|-----------------|-----------------|
| `.DS_Store` | 13 | Delete and add to `.gitignore` | Trivial, safe. |
| `streamlit_requirements.txt` | 10 | Merge into `pyproject.toml` extras | Needs verification that Streamlit deps are declared elsewhere. |
| `package-lock.json` | 6 | Investigate origin | Only 6 lines; may be stale or accidentally committed. |

---

## Final Root Level Policy

The root should contain only:

- Project configuration (`pyproject.toml`, `pytest.ini`, `mypy.ini`, `.gitignore*`, `.env*`, `.python-version`, `.bobignore`, `.ruffignore`).
- Orchestration (`Makefile`, `docker-compose.yml`).
- Top-level entry points (`start.sh`, `start-with-minio.sh`, `streamlit_app_progressive.py`).
- Primary onboarding docs (`README.md`, `START_HERE.md`).
- Large reference artifacts (`2408.12175v3.pdf`, `three_axioms_demonstration.png`, `uv.lock`, `dependencies.json`).
- Architecture docs that exceed the 300 LoC threshold and are actively referenced (`ARCHITECTURE_IMPROVEMENT_PROPOSAL.md`, `IMPORT_GUIDE.md`, `COMPLETE_SYSTEM_FLOW.md`).

Everything else < 300 LoC should live in `scripts/`, `docs/`, `data/`, `configs/`, or `notebooks/` as appropriate.
