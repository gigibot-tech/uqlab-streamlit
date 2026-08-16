# Small File Relocation Candidates — Root Level

**Branch**: `cursor/small-file-relocation-candidates-a1c5`  
**Generated**: 2026-08-16  
**Scope**: Project root folder (`/workspace`)  
**Threshold**: Files with ≤ 300 lines of code (LoC), with a stricter ≤ 200 LoC tier highlighted.

## Methodology

LoC was measured with `wc -l` for every regular file at the project root. Only the project root itself is in scope; subdirectories such as `src/`, `backend/`, `scripts/`, and `docs/` are covered by their own organization efforts.

## Root File Inventory (sorted by LoC)

| File | LoC | Type | Current Purpose | Relocation Candidate | Notes |
|------|-----|------|-----------------|----------------------|-------|
| `package-lock.json` | 6 | Generated lockfile | npm package lock | No | Keep at root alongside any frontend dependency file. |
| `streamlit_requirements.txt` | 10 | Config | Streamlit-specific Python dependencies | Maybe | Referenced by `README.md` and deployment scripts. Could move to `scripts/deployment/` or `configs/` but updating references is required. |
| `docker-compose.yml` | 44 | Config | Docker Compose orchestration | No | Referenced across `docs/`, `backend/`, and `README.md`. Standard root location. |
| `pytest.ini` | 46 | Config | pytest configuration | No | Conventionally lives at project root. |
| `organize_root_scripts.sh` | 57 | Maintenance script | One-time helper that moves scripts from root to `scripts/` subfolders | **Yes** | No references found. Move to `scripts/maintenance/`. |
| `start.sh` | 61 | Entrypoint script | Main application start script | Maybe | Referenced by docs and deployment scripts. Could move to `scripts/runners/` but root is common for entrypoints. |
| `analyze_md_files.py` | 63 | Diagnostic script | Categorizes root `.md` files by keyword | **Yes** | No references found. Move to `scripts/analysis/`; update script to resolve project root. |
| `mypy.ini` | 80 | Config | mypy type-checking configuration | No | Conventionally lives at project root. |
| `start-with-minio.sh` | 88 | Entrypoint script | Start script with MinIO backend | Maybe | Same as `start.sh`. |
| `START_HERE.md` | 97 | Documentation | Quick onboarding pointer | Maybe | Could move to `docs/` or `docs/user-guides/`, but root onboarding card is acceptable. |
| `pyproject.toml` | 116 | Config | Python packaging / tool configuration | No | Must stay at project root. |
| `Makefile` | 119 | Build automation | Common tasks | No | Conventionally at root. |
| `analysis_results.txt` | 132 | Generated output | Experiment summary output | **Yes** | Referenced once by `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`. Move to `data/` or `docs/validation/`; update the reference. |
| `ARCHITECTURE_CLARIFICATION.md` | 171 | Documentation | Architecture clarification | **Yes** | Cross-referenced by other root `.md` files. Move to `docs/development/` and update links. |
| `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` | 229 | Documentation | Execution flow guide | **Yes** | Cross-referenced by root docs. Move to `docs/development/` and update links. |
| `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` | 234 | Documentation | Dependency analysis | **Yes** | Cross-referenced by root docs. Move to `docs/development/` and update links. |
| `TERMINOLOGY_CLARIFICATION.md` | 274 | Documentation | Terminology glossary | **Yes** | Cross-referenced by root docs. Move to `docs/development/` and update links. |
| `PACKAGE_REORGANIZATION_PROPOSAL.md` | 295 | Documentation | Reorganization proposal | **Yes** | Move to `docs/development/`. |
| `FINAL_ARCHITECTURE_DECISION.md` | 299 | Documentation | Architecture decision record | **Yes** | Move to `docs/development/`. |
| `README.md` | 366 | Documentation | Main project README | No | Keep at root. |
| `streamlit_app_progressive.py` | 370 | Application | Progressive Streamlit entrypoint | No | Keep at root (or later merge into `src/` per app architecture). |
| `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` | 416 | Documentation | Architecture proposal | No | Larger than threshold; keep or move to `docs/development/` separately. |
| `IMPORT_GUIDE.md` | 491 | Documentation | Import guide | No | Larger than threshold; keep or move to `docs/development/` separately. |
| `COMPLETE_SYSTEM_FLOW.md` | 498 | Documentation | System flow | No | Larger than threshold; keep or move to `docs/development/` separately. |
| `uv.lock` | 4,626 | Generated lockfile | uv dependency lock | No | Keep at root. |
| `dependencies.json` | 21,419 | Generated data | Dependency graph output | No | Keep at root or consider `data/` in a separate cleanup. |
| `2408.12175v3.pdf` | N/A | Asset | Reference paper | No | Keep at root. |
| `three_axioms_demonstration.png` | N/A | Asset | Diagram | No | Keep at root. |

## Immediate Safe Moves (no external references found)

These two files are small, have no known references, and fit cleanly into existing `scripts/` subdirectories:

1. ✅ **Done** — `organize_root_scripts.sh` → `scripts/maintenance/organize_root_scripts.sh`
   - 57 LoC.
   - Already a maintenance script; its own purpose is to organize root scripts.
   - Running it from the project root still works after the move.

2. ✅ **Done** — `analyze_md_files.py` → `scripts/analysis/analyze_md_files.py`
   - 63 LoC.
   - Pure diagnostic / inventory utility.
   - Updated to resolve the project root (`Path(__file__).resolve().parents[2]`) instead of the current working directory, so it still categorizes root `.md` files when run from its new location.
   - Verified by running `python3 /workspace/scripts/analysis/analyze_md_files.py`.

## Candidates Requiring Reference Updates

Moving these would require updating one or more cross-references:

- `analysis_results.txt` → `data/analysis_results.txt` or `docs/validation/analysis_results.txt`
  - Update `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`.
- `ARCHITECTURE_CLARIFICATION.md` → `docs/development/ARCHITECTURE_CLARIFICATION.md`
  - Update links in `README.md`, `COMPLETE_SYSTEM_FLOW.md`, `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`, `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, and `TERMINOLOGY_CLARIFICATION.md`.
- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md`, `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md`, `TERMINOLOGY_CLARIFICATION.md`, `PACKAGE_REORGANIZATION_PROPOSAL.md`, `FINAL_ARCHITECTURE_DECISION.md` → `docs/development/`
  - Update cross-references between these documents and any `README.md` links.

## Files That Should Stay at Root

- **Tooling configs**: `pyproject.toml`, `pytest.ini`, `mypy.ini`, `docker-compose.yml`, `Makefile`, `streamlit_requirements.txt`, `package-lock.json`, `uv.lock`.
- **Environment configs**: `.env.example`, `.env.production.example`, `.gitignore`, `.bobignore`, `.python-version`, `.ruffignore`.
- **Entrypoints**: `start.sh`, `start-with-minio.sh` (root is conventional; optional move to `scripts/runners/` if desired).
- **Primary docs**: `README.md`, `COMPLETE_SYSTEM_FLOW.md`, `IMPORT_GUIDE.md`.
- **Application / assets**: `streamlit_app_progressive.py`, `2408.12175v3.pdf`, `three_axioms_demonstration.png`.
- **Large generated data**: `dependencies.json` (handled separately if needed).

## Recommended Next Steps

1. Move the two safe script candidates (`organize_root_scripts.sh`, `analyze_md_files.py`) into `scripts/`.
2. Update `analyze_md_files.py` to locate the project root programmatically so it still categorizes root `.md` files when run from `scripts/analysis/`.
3. For the markdown candidates, perform a bulk move to `docs/development/` and update all internal Markdown links in a follow-up pass.
4. For `analysis_results.txt`, decide whether it is an artifact (move to `data/`) or a validation report (move to `docs/validation/`), then update its single reference.

## Impact Summary

Moving the two safe candidates alone removes two small files from the root, leaving the root focused on configuration, entrypoints, primary documentation, and the main application file. The remaining ≤ 300 LoC markdown documents can be consolidated into `docs/development/` to complete the cleanup.
