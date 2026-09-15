# Root Small-File Relocation Candidates

**Branch**: `cursor/small-file-relocation-candidates-d2bc`  
**Date**: 2026-09-15  
**Scope**: Root-level files in `/workspace` with < 300 lines of code, evaluated for relocation into existing project folders.

---

## Changes Executed on This Branch

### Phase 1 — Safe utility-artifact relocation (done)

- `organize_root_scripts.sh` → `scripts/maintenance/organize_root_scripts.sh`
- `analyze_md_files.py` → `scripts/analysis/analyze_md_files.py`  
  - Updated the script to resolve the project root from its new location so it still categorizes root `.md` files correctly.
- `analysis_results.txt` → `scripts/analysis/analysis_results.txt`

These three files had no operational references in `Makefile`, `pyproject.toml`, `docker-compose.yml`, `README.md`, or deployment scripts, so the move is safe.

### Phase 2 / 3 — Documentation and startup scripts (pending approval)

The remaining candidates listed below are proposed moves only; execute them only after updating any internal links/references noted in the table.

---

## Method

1. Listed every root file tracked in git that is not a lockfile, large data artifact, or binary reference asset.
2. Measured non-blank lines with `wc -l`.
3. Checked whether each file is referenced by `Makefile`, `pyproject.toml`, `docker-compose.yml`, `README.md`, deployment scripts, or docs.
4. Proposed a destination folder based on the existing layout (`scripts/`, `docs/`, `configs/`, `backend/`, etc.).

---

## Root File Inventory (sorted by LoC)

| File | LoC | Category | Referenced? | Current Fit | Proposed Home | Move? |
|------|-----|----------|-------------|-------------|---------------|-------|
| `streamlit_requirements.txt` | 10 | Config | Yes (`scripts/deployment/run_streamlit*.sh`) | Streamlit-specific deps | Keep at root **or** merge into `pyproject.toml` extras | Keep / Merge |
| `docker-compose.yml` | 44 | Config | No in checked files | Docker orchestration | Keep at root | Keep |
| `pytest.ini` | 46 | Config | No | Test runner config | Keep at root | Keep |
| `organize_root_scripts.sh` | 57 | Maintenance script | No | One-off migration script | `scripts/maintenance/` | **MOVED** |
| `start.sh` | 61 | Startup script | No | Service startup | `scripts/deployment/` or keep | Optional |
| `analyze_md_files.py` | 63 | Analysis script | No | Categorizes root `.md` files | `scripts/analysis/` (updated to read project root) | **MOVED** |
| `mypy.ini` | 80 | Config | No | Type-checker config | Keep at root | Keep |
| `start-with-minio.sh` | 88 | Startup script | Yes (`docs/setup/minio.md`) | Minio startup helper | `scripts/deployment/` + update doc | Optional |
| `START_HERE.md` | 97 | Docs | Yes (`README.md`) | Onboarding guide | `docs/` + update `README.md` | Optional |
| `pyproject.toml` | 116 | Config | Yes (build/install) | Package metadata | Keep at root | Keep |
| `analysis_results.txt` | 132 | Generated output | No | Output of `analyze_md_files.py` | `scripts/analysis/` or delete | **MOVED** |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | Docs | No | Architecture clarification | `docs/architecture/` | **Move** |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | Docs | No | Execution/config guide | `docs/development/` | **Move** |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | Docs | No | Dependency analysis | `docs/development/` | **Move** |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | Docs | No | Terminology glossary | `docs/development/` | **Move** |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | Docs | No | Package reorg proposal | `docs/development/` | **Move** |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | Docs | No | Architecture decision record | `docs/architecture/` | **Move** |
| `README.md` | 366 | Docs | Yes | Main project README | Keep at root | Keep |
| `streamlit_app_progressive.py` | 370 | App | Yes (`Makefile`) | Main Streamlit entrypoint | Keep at root | Keep |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | Docs | No | Architecture proposal | `docs/architecture/` | **Move** |
| `IMPORT_GUIDE.md` | 491 | Docs | No | Import guide | `docs/development/` | **Move** |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | Docs | No | System flow doc | `docs/development/` | **Move** |

Files excluded from this scan: `.gitignore`, `.bobignore`, `.env.example`, `.env.production.example`, `.python-version`, `.ruffignore`, `uv.lock`, `dependencies.json`, `package-lock.json`, `2408.12175v3.pdf`, `three_axioms_demonstration.png`, and symlink entries (`uq_benchmarks`, `uq_classification`).

---

## Threshold Summary

### Files under 200 LoC (12 files)

1. `streamlit_requirements.txt`
2. `docker-compose.yml`
3. `pytest.ini`
4. `organize_root_scripts.sh`
5. `start.sh`
6. `analyze_md_files.py`
7. `mypy.ini`
8. `start-with-minio.sh`
9. `START_HERE.md`
10. `pyproject.toml`
11. `analysis_results.txt`
12. `ARCHITECTURE_CLARIFICATION.md`

### Files between 200–300 LoC (6 files)

1. `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`
2. `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`
3. `TERMINOLOGY_CLARIFICATION.md`
4. `PACKAGE_REORGANIZATION_PROPOSAL.md`
5. `FINAL_ARCHITECTURE_DECISION.md`
6. `analysis_results.txt` is actually 132 LoC, so it falls in the <200 group.

---

## Recommended Relocation Plan

### Phase 1: Must-move utility artifacts (no external references)

```bash
# One-off root organization helper — belongs with maintenance scripts
mv organize_root_scripts.sh scripts/maintenance/

# Markdown analyzer + its generated output — belong with analysis scripts
mv analyze_md_files.py scripts/analysis/
mv analysis_results.txt scripts/analysis/
```

After moving `analyze_md_files.py`, update the hard-coded `os.listdir('.')` to point at the project root so it keeps working from its new location.

### Phase 2: Move design/proposal docs to `docs/architecture/` or `docs/development/`

```bash
# Architecture decision records & clarifications
mv ARCHITECTURE_CLARIFICATION.md docs/architecture/
mv FINAL_ARCHITECTURE_DECISION.md docs/architecture/
mv ARCHITECTURE_IMPROVEMENT_PROPOSAL.md docs/architecture/

# Guides, proposals, and analyses
mv EXECUTION_FLOW_AND_CONFIG_GUIDE.md docs/development/
mv DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md docs/development/
mv TERMINOLOGY_CLARIFICATION.md docs/development/
mv PACKAGE_REORGANIZATION_PROPOSAL.md docs/development/
mv IMPORT_GUIDE.md docs/development/
mv COMPLETE_SYSTEM_FLOW.md docs/development/
```

### Phase 3: Optional startup / onboarding consolidation

```bash
# Startup helpers are deployment-related
mv start.sh scripts/deployment/
mv start-with-minio.sh scripts/deployment/

# Update docs/setup/minio.md to reference scripts/deployment/start-with-minio.sh
# Update README.md to reference docs/START_HERE.md if START_HERE.md is moved
mv START_HERE.md docs/
```

---

## Files That Should Stay at Root

These are either required by tooling conventions or actively referenced by entry commands:

| File | Reason to keep at root |
|------|--------------------------|
| `README.md` | Project landing page; convention. |
| `pyproject.toml` | Python packaging; must be at package root. |
| `docker-compose.yml` | Docker Compose convention; referenced relative to root. |
| `pytest.ini` / `mypy.ini` | Tool configs; root placement is standard. |
| `.env.example` / `.env.production.example` | Env templates; root placement is standard. |
| `.gitignore`, `.bobignore`, `.ruffignore` | Dotfiles; root placement is standard. |
| `streamlit_app_progressive.py` | Main app; `Makefile` runs `uv run streamlit run streamlit_app_progressive.py`. |
| `streamlit_requirements.txt` | Referenced by `scripts/deployment/run_streamlit*.sh`. Better long-term: fold into `pyproject.toml` extras, then delete. |
| `Makefile` | Root Makefile is the conventional entry point. |

---

## Expected Root After Full Cleanup

```
uqlab-streamlit/
├── .env.example
├── .env.production.example
├── .gitignore
├── .bobignore
├── .ruffignore
├── Makefile
├── README.md
├── docker-compose.yml
├── mypy.ini
├── pyproject.toml
├── pytest.ini
├── streamlit_app_progressive.py
├── streamlit_requirements.txt   # or merged into pyproject.toml
├── backend/
├── configs/
├── data/
├── docs/
├── notebooks/
├── scripts/
├── src/
├── tests/
├── uqlab-flask/
└── ... (large reference assets)
```

---

## Risks / Notes

1. **Relative references inside docs**: Some markdown files may link to each other with relative paths (e.g., `../docs/UQLAB_FLOW.md`). After moving, a bulk link-rewriting pass is required.
2. **`analyze_md_files.py`**: Reads from the current working directory. If moved, update to accept a `--root` argument or hard-code the project root.
3. **`start-with-minio.sh`**: Referenced by `docs/setup/minio.md`. Move only if the doc is updated.
4. **`START_HERE.md`**: Referenced by `README.md`. Update the README link if moved.
5. **`analysis_results.txt`**: Generated file; consider deleting instead of moving if it is not needed in version control.

---

## Next Steps

1. Review and approve the recommended moves.
2. Decide whether `streamlit_requirements.txt` should be merged into `pyproject.toml` extras.
3. Execute Phase 1 (safe, no reference updates needed).
4. Execute Phase 2 and update any internal markdown links.
5. Optionally execute Phase 3 and update `README.md` + `docs/setup/minio.md`.
6. Run `make lint` / `make test-fast` to verify nothing breaks.
