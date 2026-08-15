# Root Level Cleanup Analysis

## Files at Root Level of `uqlab-streamlit/`

### ✅ KEEP - Active/Important Files

#### Entry Points (KEEP)
- `run_fast.py` - Main CLI entry point for experiments
- `streamlit_app.py` - Main Streamlit dashboard
- `streamlit_app_progressive.py` - Progressive disclosure Streamlit app

#### Configuration (KEEP)
- `.env`, `.env.example` - Environment configuration
- `.env.production`, `.env.production.example` - Production config
- `docker-compose.yml` - Docker setup
- `pyproject.toml` - Python project config
- `pytest.ini` - Test configuration
- `mypy.ini` - Type checking config
- `.gitignore` - Git ignore rules
- `.bobignore` - Bob ignore rules

#### Documentation (KEEP - But could move to docs/)
- `README.md` - Main project README
- `AGENTS.md` - Agent documentation

### ⚠️ ARCHIVE - Old/Redundant Files

#### Old Documentation (MOVE TO archive/docs/)
- `MLOPS_REFACTORED_STRUCTURE.md`
- `MLOPS_REFACTORING_FINAL_STATUS.md`
- `MLOPS_REFACTORING_IMPLEMENTATION_PLAN.md`
- `MLOPS_REFACTORING_PROGRESS.md`
- `COMPLETE_CODEBASE_CONSOLIDATION_PLAN.md`
- `CODEBASE_CONSOLIDATION_COMPLETE.md`
- `CONSOLIDATION_COMPLETE.md`
- `FINAL_CONSOLIDATION_PLAN.md`
- `UI_COMPONENTS_CONSOLIDATION_PLAN.md`
- `STREAMLIT_REDESIGN_PLAN.md`
- `STREAMLIT_PROGRESSIVE_UX_SPEC.md`
- `EXPERIMENT_TRACKER_INTEGRATION_PLAN.md`
- `DEPENDENCY_ANALYSIS_README.md`

#### Utility Scripts (MOVE TO scripts/utils/)
- `analyze_dependencies.py`
- `dependency_visualizer.py`
- `visualize_7x2_structure.py`
- `run_dependency_analysis.sh`

#### Old/Duplicate Files (DELETE or ARCHIVE)
- `ui_components_old.py` - Old backup
- `ui_components_backup_20260604_205217.tar.gz` - Backup archive
- `uncertainty_visualization_demo copy.ipynb` - Duplicate notebook
- `watsonx_deployment_experiment copy.ipynb` - Duplicate notebook

#### Consolidation Scripts (MOVE TO archive/scripts/)
- `consolidate_codebase.sh` - Already executed
- `rename_to_uqlab.sh` - Will be executed once

### 📊 MOVE - Notebooks (to notebooks/)
- `resnet_baseline_experiment.ipynb`
- `uncertainty_visualization_demo.ipynb`
- `uncertainty_viz_3class.ipynb`
- `watsonx_deployment_experiment.ipynb`

### 🔧 KEEP - Utility Scripts (But could move to scripts/)
- `run_streamlit.sh`
- `run_streamlit_modular.sh`
- `test_api.sh`

### 📄 KEEP - Reference Documents
- `2408.12175v3.pdf` - Research paper
- `three_axioms_demonstration.png` - Diagram
- `CONFIG_AND_IMPORTS_STATUS.md` - Current status
- `RENAME_TO_UQLAB.md` - Rename plan

## Recommended Actions

### Phase 1: Archive Old Documentation
```bash
mkdir -p archive/old_docs
mv MLOPS_*.md archive/old_docs/
mv COMPLETE_CODEBASE_*.md archive/old_docs/
mv CODEBASE_CONSOLIDATION_*.md archive/old_docs/
mv CONSOLIDATION_*.md archive/old_docs/
mv FINAL_CONSOLIDATION_*.md archive/old_docs/
mv UI_COMPONENTS_*.md archive/old_docs/
mv STREAMLIT_REDESIGN_*.md archive/old_docs/
mv STREAMLIT_PROGRESSIVE_*.md archive/old_docs/
mv EXPERIMENT_TRACKER_*.md archive/old_docs/
mv DEPENDENCY_ANALYSIS_*.md archive/old_docs/
```

### Phase 2: Move Notebooks
```bash
# Already have notebooks/ directory
mv resnet_baseline_experiment.ipynb notebooks/
mv uncertainty_visualization_demo.ipynb notebooks/
mv uncertainty_viz_3class.ipynb notebooks/
mv watsonx_deployment_experiment.ipynb notebooks/
```

### Phase 3: Move Utility Scripts
```bash
mkdir -p scripts/utils
mv analyze_dependencies.py scripts/utils/
mv dependency_visualizer.py scripts/utils/
mv visualize_7x2_structure.py scripts/utils/
mv run_dependency_analysis.sh scripts/utils/
```

### Phase 4: Delete Duplicates/Old Files
```bash
rm "uncertainty_visualization_demo copy.ipynb"
rm "watsonx_deployment_experiment copy.ipynb"
rm ui_components_old.py
rm ui_components_backup_20260604_205217.tar.gz
```

### Phase 5: Archive Consolidation Scripts
```bash
mkdir -p archive/consolidation_scripts
mv consolidate_codebase.sh archive/consolidation_scripts/
# Keep rename_to_uqlab.sh until rename is complete
```

### Phase 6: Move Shell Scripts (Optional)
```bash
mkdir -p scripts/shell
mv run_streamlit.sh scripts/shell/
mv run_streamlit_modular.sh scripts/shell/
mv test_api.sh scripts/shell/
```

## Final Root Level Structure

After cleanup, root should only have:
```
uqlab-streamlit/
├── .env, .env.example          # Config
├── .gitignore, .bobignore      # Git/Bob config
├── docker-compose.yml          # Docker
├── pyproject.toml              # Python project
├── pytest.ini, mypy.ini        # Testing/typing
├── README.md, AGENTS.md        # Main docs
├── run_fast.py                 # Main entry point
├── streamlit_app.py            # Streamlit entry
├── streamlit_app_progressive.py # Progressive Streamlit
├── 2408.12175v3.pdf            # Reference paper
├── three_axioms_demonstration.png # Diagram
├── CONFIG_AND_IMPORTS_STATUS.md # Current status
├── RENAME_TO_UQLAB.md          # Rename plan
├── archive/                    # Old files
├── backend/                    # FastAPI backend
├── configs/                    # YAML configs
├── docs/                       # Documentation
├── frontend/                   # React frontend
├── notebooks/                  # Jupyter notebooks
├── scripts/                    # Utility scripts
├── src/                        # Main source code
│   └── uqlab/                  # Main package
└── tests/                      # Test files
```

## Benefits

✅ **Cleaner root** - Only essential files  
✅ **Better organization** - Files in appropriate folders  
✅ **Easier navigation** - Less clutter  
✅ **Preserved history** - Old files archived, not deleted

---

## Small File Relocation (2026-08-15)

A pass over the current root for files **<300 lines of code** found several candidates that could be relocated or consolidated. The actions below were applied on branch `cursor/small-file-relocation-candidates-7fcc`.

### ✅ Relocated

| File | LoC | Old Location | New Location | Rationale |
|------|-----|--------------|--------------|-----------|
| `organize_root_scripts.sh` | 57 | root | `scripts/maintenance/` | Root-organization script; fits the existing maintenance/cleanup folder. |
| `analyze_md_files.py` | 63 | root | `scripts/maintenance/` | Small utility for categorizing markdown files; no root-level references. |
| `analysis_results.txt` | 132 | root | `docs/validation/` | Generated artifact referenced by `docs/validation/HYPOTHESIS_VERIFICATION_RESULTS.md`; keeping it next to that doc preserves the link. |
| `package-lock.json` | 6 | root | — | Deleted. Empty lockfile with no `package.json`; already listed in `.gitignore`. |

### ⚠️ Remaining Candidates (require care or discussion)

These files are still small enough to consider moving, but have references or represent conventional root configuration.

| File | LoC | Proposed Action | Notes |
|------|-----|-----------------|-------|
| `streamlit_requirements.txt` | 10 | Delete | Marked deprecated in-file. Still referenced by `scripts/deployment/run_streamlit.sh`, `scripts/deployment/run_streamlit_modular.sh`, and several docs. References should be updated to `uv sync` before removal. |
| `mypy.ini` | 80 | Merge into `pyproject.toml` then delete | `[tool.mypy]` already exists in `pyproject.toml`. Merge unique per-module settings (e.g., `ignore_missing_imports` for third-party libs) first. |
| `pytest.ini` | 46 | Merge into `pyproject.toml` then delete | `[tool.pytest.ini_options]` already exists in `pyproject.toml`. Combine `addopts`, markers, and `filterwarnings` carefully. |
| `.ruffignore` | 17 | Merge into `pyproject.toml` then delete | `tool.ruff.extend-exclude` already exists; add the remaining ignore patterns there. |
| `.gitignore_parent` | 118 | Merge unique patterns into `.gitignore` then delete | Mostly a duplicate of `.gitignore`. Unique patterns (e.g., `*.ipynb`) should be evaluated before merging. |
| `START_HERE.md` | 97 | Keep or move to `docs/` | Referenced by `README.md`, `streamlit_app_progressive.py`, and `docs/features/workflow-config.md`. If moved, all references must be updated. |
| `start.sh` | 61 | Keep (or move to `scripts/deployment/`) | Referenced by `START_HERE.md` as the entry point for the frontend. Keep in root for discoverability. |
| `start-with-minio.sh` | 88 | Keep (or move to `scripts/deployment/`) | Docker/MinIO startup helper; paired with `docker-compose.yml`. Keep in root for discoverability. |

### 🚫 Keep in Root

These are standard project-level files and should stay:

- `pyproject.toml` (116 LoC) — workspace definition, dependencies, tool configs
- `Makefile` (119 LoC) — development commands
- `.gitignore` (150 LoC) — git ignore rules
- `.gitmodules` (3 LoC) — submodule definition
- `.env.example` (29 LoC) / `.env.production.example` (68 LoC) — environment templates
- `docker-compose.yml` (44 LoC) — Docker services
- `.python-version` (1 LoC) — pyenv version pin
- `.bobignore` (14 LoC) — Bob-specific ignore rules
- `README.md` — primary project README
- `streamlit_app_progressive.py` — main Streamlit entry point
- `2408.12175v3.pdf`, `three_axioms_demonstration.png` — reference assets

### Summary of Applied Changes

- Reduced root clutter by 4 files (2 scripts, 1 generated artifact, 1 stale lockfile).
- No code imports or runtime paths were broken by the relocated files.
- Config consolidation candidates were documented but left untouched to avoid tooling regressions.
  