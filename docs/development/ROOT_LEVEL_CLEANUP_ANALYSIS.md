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

## `uqlab-flask` (Current Flask Wizard)

The current tree contains `uqlab-flask/` instead of the proposed `frontend/` directory. It is a small local Flask wizard (no API) documented as the "Local Flask wizard" in `START_HERE.md`.

### File Sizes

| File | LoC |
|------|-----|
| `app.py` | 37 |
| `README.md` | 33 |
| `requirements.txt` | 2 |
| `uqlab_flask/__init__.py` | 1 |
| `uqlab_flask/routes/__init__.py` | 0 |
| `uqlab_flask/routes/runs.py` | 139 |
| `uqlab_flask/routes/wizard.py` | 282 |
| `uqlab_flask/static/style.css` | 177 |
| `uqlab_flask/templates/base.html` | 15 |
| `uqlab_flask/templates/launched.html` | 276 |
| `uqlab_flask/templates/review.html` | 25 |
| `uqlab_flask/templates/step1.html` | 25 |
| `uqlab_flask/templates/step2.html` | 35 |
| `uqlab_flask/templates/step3.html` | 25 |
| `uqlab_flask/templates/step4.html` | 18 |
| `uqlab_flask/templates/step5.html` | 13 |
| `uqlab_flask/templates/sweep_not_found.html` | 13 |
| `uqlab_flask/executor.py` | 652 |

All files except `uqlab_flask/executor.py` are under 300 LoC. The whole app is small enough to be considered for relocation or consolidation.

### Relocation Options

- **Option A — Keep as root-level `frontend/`**: Rename `uqlab-flask/` to `frontend/` to match the cleanup plan. This only changes the folder name and import references in `app.py` and routes.
- **Option B — Move into `src/`**: Relocate the package to `src/uqlab_flask/` or `src/flask_ui/` so it lives alongside other source packages (`uqlab_core`, `uqlab_orchestrator`). The root entry point would become a thin launcher.
- **Option C — Merge into `backend/`**: The wizard routes and run API overlap conceptually with the FastAPI backend. `routes/runs.py` and `routes/wizard.py` could be ported to `backend/app/api/routes/` and `backend/app/`, while `executor.py` could be unified with `backend/app/services/executors/direct_executor.py`.
- **Option D — Archive**: If the Streamlit progressive UI is the primary UI and the Flask wizard is no longer maintained, the entire folder could be archived.

### Recommendation

Option A is the lowest-friction change and aligns with the cleanup plan. Option B is better if the goal is to keep the root free of application code. Option C makes sense only if the backend should also serve the HTML wizard.

## Benefits

✅ **Cleaner root** - Only essential files  
✅ **Better organization** - Files in appropriate folders  
✅ **Easier navigation** - Less clutter  
✅ **Preserved history** - Old files archived, not deleted  