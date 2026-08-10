# Small file relocation candidates in `/workspace`

Thresholds: <200 LoC and 200-300 LoC (configurable with --threshold).

Found 12 files under 300 lines of code.

## <200 LoC

- `streamlit_requirements.txt` (9 LoC)
  - Suggested target: `configs/`
  - Reason: Python requirements file
  - References found (9):
    - `docs/user-guides/README_PARENT.md:103:pip install -r streamlit_requirements.txt`
    - `docs/development/UV_PYTHON_FIX.md:37:uv pip install -r streamlit_requirements.txt`
    - `docs/development/UV_PYTHON_FIX.md:78:uv pip install -r streamlit_requirements.txt`
    - `docs/development/UV_PYTHON_FIX.md:117:cd /Users/andrearachetta/Documents/old_pilots && rm -rf .venv && uv venv --python 3.12 && source .venv/bin/activate && cd uqlab-streamlit && uv pip install -r backend/requirements.txt && uv pip install -r streamlit_requirements.txt && uv pip install -e .`
    - `docs/development/UV_PYTHON_FIX.md:148:pip install -r streamlit_requirements.txt`
    - ... and 4 more

- `start.sh` (47 LoC)
  - Suggested target: `scripts/deployment/`
  - Reason: Shell entry-point / deployment script
  - References found (10):
    - `streamlit_requirements.txt:3:#   ./start.sh`
    - `backend/scripts/entrypoint.sh:5:if [ -f /app/scripts/prestart.sh ]; then`
    - `backend/scripts/entrypoint.sh:6:    echo "Running prestart.sh..."`
    - `backend/scripts/entrypoint.sh:7:    /app/scripts/prestart.sh`
    - `scripts/maintenance/find_small_root_files.py:229:    print("- Entry-point scripts (`start.sh`, `Makefile` targets) may need symlink or README updates when moved.")`
    - ... and 5 more

- `organize_root_scripts.sh` (48 LoC)
  - Suggested target: `scripts/deployment/`
  - Reason: Shell entry-point / deployment script
  - No references found in the codebase

- `analyze_md_files.py` (53 LoC)
  - Suggested target: `scripts/analysis/`
  - Reason: Analysis / reporting Python script
  - No references found in the codebase

- `start-with-minio.sh` (69 LoC)
  - Suggested target: `scripts/deployment/`
  - Reason: Shell entry-point / deployment script
  - References found (7):
    - `docs/setup/minio.md:22:./start-with-minio.sh`
    - `docs/setup/minio.md:285:./start-with-minio.sh`
    - `docs/architecture/minio-storage.md:50:**File**: `start-with-minio.sh` (executable)`
    - `docs/architecture/minio-storage.md:102:./start-with-minio.sh`
    - `docs/architecture/minio-storage.md:136:- [ ] Test script: `./start-with-minio.sh` should start both services`
    - ... and 2 more

- `analysis_results.txt` (111 LoC)
  - Suggested target: `data/`
  - Reason: Generated results / output artifact
  - References found (1):
    - `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md:279:**Full Results:** `analysis_results.txt``

- `ARCHITECTURE_CLARIFICATION.md` (117 LoC)
  - Suggested target: `docs/`
  - Reason: Documentation / markdown file
  - References found (3):
    - `EXECUTION_FLOW_AND_CONFIG_GUIDE.md:223:| [`ARCHITECTURE_CLARIFICATION.md`](ARCHITECTURE_CLARIFICATION.md) | Package boundaries |`
    - `COMPLETE_SYSTEM_FLOW.md:6:> **📖 Architecture Questions?** See [`ARCHITECTURE_CLARIFICATION.md`](ARCHITECTURE_CLARIFICATION.md) for package boundaries and responsibilities.`
    - `README.md:50:Package boundaries: [`ARCHITECTURE_CLARIFICATION.md`](ARCHITECTURE_CLARIFICATION.md).`

- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md` (170 LoC)
  - Suggested target: `docs/`
  - Reason: Documentation / markdown file
  - References found (1):
    - `README.md:49:Full flow diagram and FAQ: [`EXECUTION_FLOW_AND_CONFIG_GUIDE.md`](EXECUTION_FLOW_AND_CONFIG_GUIDE.md).`

- `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md` (177 LoC)
  - Suggested target: `docs/`
  - Reason: Documentation / markdown file
  - No references found in the codebase

## 200-300 LoC

- `TERMINOLOGY_CLARIFICATION.md` (204 LoC)
  - Suggested target: `docs/`
  - Reason: Documentation / markdown file
  - No references found in the codebase

- `FINAL_ARCHITECTURE_DECISION.md` (229 LoC)
  - Suggested target: `docs/`
  - Reason: Documentation / markdown file
  - References found (1):
    - `TERMINOLOGY_CLARIFICATION.md:269:**Proposed fix**: Move `scripts/runners/` → `src/uqlab/cli/` (see FINAL_ARCHITECTURE_DECISION.md)`

- `PACKAGE_REORGANIZATION_PROPOSAL.md` (234 LoC)
  - Suggested target: `docs/`
  - Reason: Documentation / markdown file
  - References found (1):
    - `DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md:215:**Migration**: 2 hours (as detailed in PACKAGE_REORGANIZATION_PROPOSAL.md)`

## Files above 300 LoC (for context)

- `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` (323 LoC) — suggested: `docs/`
- `streamlit_app_progressive.py` (328 LoC) — suggested: `scripts/maintenance/`
- `IMPORT_GUIDE.md` (358 LoC) — suggested: `docs/`
- `COMPLETE_SYSTEM_FLOW.md` (408 LoC) — suggested: `docs/`
- `dependencies.json` (21420 LoC) — suggested: `configs/`
- `2408.12175v3.pdf` (86869 LoC) — suggested: `archive/`

## Notes

- Files listed as `KEEP_AT_ROOT` (e.g., `pyproject.toml`, `Makefile`) are intentionally omitted.
- Generated artifacts and one-off analysis scripts are usually safe to move.
- Entry-point scripts (`start.sh`, `Makefile` targets) may need symlink or README updates when moved.
- Always verify references before moving a file.
