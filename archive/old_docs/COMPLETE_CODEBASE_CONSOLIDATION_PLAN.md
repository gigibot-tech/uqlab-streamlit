# Complete Codebase Consolidation Plan

## Overview

The `walaris-cen` codebase has **multiple organizational issues** that need consolidation:

1. ✅ **UI Components**: Symlink architecture (CORRECT - no action needed)
2. ⚠️ **Three UQ Packages**: `uq_classification`, `uq_benchmarks`, `uq_disentanglement_comparison`
3. ⚠️ **MLOps Folders (1-7)**: Should be in `src/` or `backend/`
4. ⚠️ **Scattered Source Code**: `src/data/`, `src/models/`, `src/metrics/`, etc.

---

## Issue 1: UI Components ✅ RESOLVED

### Current State
```
walaris-cen/
├── ui_components -> src/walaris/ui_components  # Symlink
└── src/walaris/ui_components/                  # Actual code
```

### Status: **CORRECT ARCHITECTURE**
- Symlink provides convenience for Streamlit app
- Single source of truth in `src/walaris/ui_components/`
- No action needed

---

## Issue 2: Three UQ Packages ⚠️ NEEDS CONSOLIDATION

### Current State
```
walaris-cen/
├── uq_classification/              # Legacy package
├── uq_benchmarks/                  # Benchmarking package
└── uq_disentanglement_comparison/  # Research comparison package
```

### Analysis Needed

**Questions:**
1. Are these three packages **active** or **legacy**?
2. Do they have **overlapping functionality**?
3. Which one is the **primary** package?
4. Can they be **merged** or should they be **archived**?

**Action:** Analyze each package's purpose and usage

---

## Issue 3: MLOps Folders (1-7) ⚠️ NEEDS RELOCATION

### Current State
```
walaris-cen/
├── 1_data/           # Data layer
├── 2_models/         # Model architectures
├── 3_training/       # Training pipeline
├── 4_evaluation/     # Evaluation & metrics
├── 5_api/            # API endpoints
├── 6_ui/             # UI components
├── 7_orchestration/  # Workflow management
└── shared/           # Shared utilities
```

### Problem
These folders are at **root level** but should be organized within the project structure.

### Proposed Solutions

#### Option A: Move to `src/walaris/` (RECOMMENDED)
```
src/walaris/
├── data/           # From 1_data/
├── models/         # From 2_models/
├── training/       # From 3_training/
├── evaluation/     # From 4_evaluation/
├── api/            # From 5_api/
├── ui/             # From 6_ui/
├── orchestration/  # From 7_orchestration/
└── shared/         # From shared/
```

**Benefits:**
- ✅ Proper Python package structure
- ✅ Installable with `pip install -e .`
- ✅ Clean imports: `from walaris.data import ...`
- ✅ Follows Python best practices

#### Option B: Move to `backend/app/`
```
backend/app/
├── data/           # From 1_data/
├── models/         # From 2_models/
├── training/       # From 3_training/
├── evaluation/     # From 4_evaluation/
├── api/            # From 5_api/ (merge with existing routes/)
├── ui/             # From 6_ui/
├── orchestration/  # From 7_orchestration/
└── shared/         # From shared/
```

**Benefits:**
- ✅ Co-located with FastAPI backend
- ✅ Clear separation: backend vs frontend
- ⚠️ Less suitable for standalone package

#### Option C: Keep at Root (NOT RECOMMENDED)
**Problems:**
- ❌ Clutters root directory
- ❌ Not a proper Python package
- ❌ Harder to install/distribute
- ❌ Confusing structure

### Recommendation: **Option A** (Move to `src/walaris/`)

---

## Issue 4: Scattered Source Code ⚠️ NEEDS CONSOLIDATION

### Current State
```
src/
├── data/           # Data utilities (overlaps with 1_data?)
├── models/         # Model code (overlaps with 2_models?)
├── metrics/        # Metrics (overlaps with 4_evaluation?)
├── experiments/    # Experiment code
├── triage/         # Triage utilities
├── utils/          # General utilities
└── walaris/        # Main package
```

### Problem
Code is **scattered** across multiple locations with **potential overlap**.

### Analysis Needed
1. Compare `src/data/` vs `1_data/` - are they duplicates?
2. Compare `src/models/` vs `2_models/` - are they duplicates?
3. Compare `src/metrics/` vs `4_evaluation/` - are they duplicates?
4. Identify which is **active** vs **legacy**

---

## Comprehensive Consolidation Strategy

### Phase 1: Analysis (1-2 hours)

1. **Analyze UQ Packages**
   ```bash
   # Check which packages are imported
   grep -r "import uq_classification" --include="*.py"
   grep -r "import uq_benchmarks" --include="*.py"
   grep -r "import uq_disentanglement" --include="*.py"
   
   # Check last modification dates
   find uq_* -name "*.py" -exec stat -f "%Sm %N" {} \; | sort
   ```

2. **Compare Overlapping Folders**
   ```bash
   # Compare data folders
   diff -r src/data/ 1_data/ | head -50
   
   # Compare model folders
   diff -r src/models/ 2_models/ | head -50
   
   # Compare metrics folders
   diff -r src/metrics/ 4_evaluation/ | head -50
   ```

3. **Identify Active vs Legacy**
   - Check git history: `git log --oneline --all -- folder/`
   - Check imports in main apps
   - Check documentation references

### Phase 2: Decision Making (30 minutes)

Create decision matrix:
| Folder | Status | Action | Reason |
|--------|--------|--------|--------|
| `uq_classification/` | ? | ? | ? |
| `uq_benchmarks/` | ? | ? | ? |
| `uq_disentanglement/` | ? | ? | ? |
| `1_data/` | ? | ? | ? |
| `src/data/` | ? | ? | ? |
| ... | ... | ... | ... |

### Phase 3: Consolidation (2-4 hours)

1. **Archive Legacy Code**
   ```bash
   mkdir -p archive/legacy_packages
   mv uq_classification/ archive/legacy_packages/
   ```

2. **Move MLOps Folders**
   ```bash
   # Move to src/walaris/
   mv 1_data/ src/walaris/data/
   mv 2_models/ src/walaris/models/
   # ... etc
   ```

3. **Update Imports**
   ```bash
   # Find all imports
   grep -r "from 1_data" --include="*.py"
   
   # Update to new paths
   sed -i '' 's/from 1_data/from walaris.data/g' **/*.py
   ```

4. **Update Documentation**
   - Update README with new structure
   - Update import examples
   - Update architecture diagrams

### Phase 4: Testing (1 hour)

1. **Verify Imports**
   ```bash
   python -c "from walaris.data import ..."
   python -c "from walaris.models import ..."
   ```

2. **Run Tests**
   ```bash
   pytest tests/
   ```

3. **Test Main Apps**
   ```bash
   streamlit run streamlit_app.py
   uvicorn backend.app.main:app
   ```

---

## Proposed Final Structure

```
walaris-cen/
├── README.md
├── pyproject.toml
├── requirements.txt
│
├── src/walaris/              # Main Python package
│   ├── __init__.py
│   ├── data/                 # Data layer (from 1_data/)
│   ├── models/               # Models (from 2_models/)
│   ├── training/             # Training (from 3_training/)
│   ├── evaluation/           # Evaluation (from 4_evaluation/)
│   ├── api/                  # API logic (from 5_api/)
│   ├── ui_components/        # UI components (existing)
│   ├── orchestration/        # Orchestration (from 7_orchestration/)
│   ├── shared/               # Shared utilities (from shared/)
│   ├── classification/       # Classification utilities
│   ├── notebook_support/     # Notebook helpers
│   └── run_artifacts/        # Run artifacts
│
├── backend/                  # FastAPI backend
│   └── app/
│       ├── main.py
│       ├── api/routes/       # API routes
│       ├── core/             # Core backend logic
│       └── tables.py         # Database tables
│
├── ui_components -> src/walaris/ui_components  # Symlink
├── streamlit_app.py          # Main Streamlit app
├── progressive_app.py        # Progressive disclosure app
│
├── scripts/                  # Utility scripts
├── notebooks/                # Jupyter notebooks
├── tests/                    # Test suite
│
└── archive/                  # Archived/legacy code
    ├── legacy_packages/
    │   ├── uq_classification/
    │   ├── uq_benchmarks/
    │   └── uq_disentanglement/
    └── old_structure/
        ├── src/data/
        ├── src/models/
        └── src/metrics/
```

---

## Next Steps

1. **Run Analysis Phase** to understand current usage
2. **Create Decision Matrix** based on findings
3. **Get Approval** for consolidation plan
4. **Execute Consolidation** in phases
5. **Update Documentation** and tests
6. **Verify Everything Works**

---

## Estimated Timeline

- **Analysis:** 1-2 hours
- **Planning:** 30 minutes
- **Execution:** 2-4 hours
- **Testing:** 1 hour
- **Documentation:** 1 hour
- **Total:** 5-8 hours

---

## Risk Assessment

**Risk Level:** 🟡 **MEDIUM**

**Risks:**
- Breaking existing imports
- Losing track of legacy code
- Merge conflicts if team is active

**Mitigation:**
- Create comprehensive backups
- Use git branches for changes
- Test thoroughly before committing
- Update documentation immediately
- Communicate changes to team

---

**Status:** 📋 **PLAN READY** - Awaiting analysis phase
**Next Action:** Run analysis commands to understand current state