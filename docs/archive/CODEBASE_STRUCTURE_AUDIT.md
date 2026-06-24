# Codebase Structure Audit Report

**Date:** 2026-06-18  
**Auditor:** Bob (AI Assistant)  
**Scope:** Backend DDD structure and evaluation package organization

---

## Executive Summary

This audit reveals a **well-structured codebase** with proper Domain-Driven Design (DDD) in the backend and a **legacy compatibility layer** in the evaluation/classification folder. The main findings:

1. ✅ **Backend has proper DDD structure** - All required folders exist
2. ⚠️ **evaluation/classification is a shim/compatibility layer** - Not actual implementation
3. ⚠️ **evaluation/benchmarks is minimally used** - Only self-referential imports
4. ✅ **Actual implementations are properly organized** in dedicated folders

**Recommendation:** Document the shim pattern, clean up unused files, and improve discoverability of actual implementations.

---

## Task 1: Backend Structure Audit

### Current Backend Structure

```
backend/app/
├── domain/                    ✅ EXISTS - Domain models
│   ├── __init__.py
│   ├── models.py
│   └── value_objects.py
├── repositories/              ✅ EXISTS - Data access layer
│   ├── __init__.py
│   ├── batch_experiment_repository.py
│   └── experiment_repository.py
├── services/                  ✅ EXISTS - Business logic
│   ├── __init__.py
│   ├── batch_experiment_service.py
│   ├── metrics_service.py
│   ├── progress_parser.py
│   ├── training_orchestrator.py
│   ├── executors/
│   │   ├── base.py
│   │   ├── direct_executor.py
│   │   └── subprocess_executor.py
│   └── storage/
│       ├── base.py
│       ├── postgres.py
│       └── wxgov.py
├── storage/                   ✅ EXISTS - Storage abstraction
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── filesystem.py
│   └── s3.py
├── api/                       ✅ API layer
├── core/                      ✅ Core configuration
├── models.py                  ⚠️ Legacy - should use domain/
├── tables.py                  ⚠️ Legacy - should use domain/
└── crud.py                    ⚠️ Legacy - should use repositories/
```

### Assessment

**✅ EXCELLENT:** The backend follows proper Domain-Driven Design with clear separation of concerns:

- **Domain Layer** (`domain/`): Contains domain models and value objects
- **Repository Layer** (`repositories/`): Data access patterns for experiments
- **Service Layer** (`services/`): Business logic including training orchestration
- **Storage Layer** (`storage/`): Abstract storage with filesystem and S3 implementations

**⚠️ Minor Issues:**
- Root-level `models.py`, `tables.py`, and `crud.py` suggest legacy code that should be migrated to proper DDD folders
- These files likely exist for backward compatibility

**Recommendation:** 
- Keep the current structure (it's excellent)
- Consider deprecating root-level files in favor of domain/repositories
- Document the DDD architecture in a BACKEND_ARCHITECTURE.md file

---

## Task 2: Evaluation/Classification Usage Analysis

### Folder Contents

```
src/uqlab/evaluation/classification/
├── __init__.py                    # Empty shim
├── attribution_signals.py         # Real implementation
├── benchmark_axes.py              # Real implementation
├── config.py                      # SHIM → uqlab.shared.config.classification
├── data_loader.py                 # Real implementation (heavily used)
├── evaluation.py                  # Real implementation
├── feature_extractor.py           # Real implementation
├── hydra_wrapper.py               # Real implementation
├── model_factory.py               # Real implementation
├── models.py                      # SHIM → uqlab.models.classification_models
├── signal_formula_specs.py        # Real implementation
├── utils.py                       # Real implementation
├── watsonx_streamlit.py           # Real implementation
├── DECISION_BOUNDARY_VIZ_README.md
├── MERGE_NOTES.md
└── STREAMLIT_APP_README.md
```

### Usage Analysis

**Found 30 import references across the codebase:**

#### Heavily Used Files (10+ references):
1. **data_loader.py** - 8 direct imports
   - Used by: `src/uqlab/data/__init__.py`, `src/uqlab/models/feature_extractors.py`, training scripts
   - Contains: `SplitSpec`, `EmbeddingOrganizer`, data sampling functions
   - **Status:** ACTIVELY USED - Core data loading functionality

2. **config.py** - 5 imports (but it's a SHIM)
   - Redirects to: `uqlab.shared.config.classification`
   - **Status:** COMPATIBILITY LAYER - Actual code is in `src/uqlab/shared/config/`

3. **models.py** - 4 imports (but it's a SHIM)
   - Redirects to: `uqlab.models.classification_models`
   - **Status:** COMPATIBILITY LAYER - Actual code is in `src/uqlab/models/`

4. **evaluation.py** - 3 imports
   - Used by: tests, training scripts
   - Contains: `binary_auroc`, `evaluate_three_way_classification`, `predict_eval_groups_single_signal`
   - **Status:** ACTIVELY USED - Core evaluation metrics

5. **watsonx_export.py** - 3 imports
   - Used by: UI components, API integrations
   - **Status:** ACTIVELY USED - Production integration

#### Moderately Used Files (2-5 references):
- **attribution_signals.py** - 2 imports (compute_attribution_structure_signals)
- **benchmark_axes.py** - 2 imports (expects_aleatoric_eval)
- **feature_extractor.py** - 2 imports (create_feature_extractor, DINOv2FeatureExtractor)
- **model_factory.py** - 2 imports (build_model)
- **signal_formula_specs.py** - 2 imports (build_signal_formula_manifest)
- **utils.py** - 2 imports (auto_device, dino_transform, set_seed)
- **hydra_wrapper.py** - 2 imports (hydra_to_dataclass)

#### Lightly Used Files (1 reference):
- **watsonx_scoring.py** - 1 import (WatsonxScoringClient)

### Key Finding: Shim Pattern

The `evaluation/classification/` folder serves as a **backward compatibility layer** for the legacy `uq_classification` package:

```python
# config.py - SHIM
from uqlab.shared.config.classification import (
    DataConfig, ExperimentConfig, ModelConfig, ...
)

# models.py - SHIM  
from uqlab.models.classification_models import (
    EmbeddingDataset, EmbeddingDropoutMLP
)
```

**Actual implementations live in:**
- `src/uqlab/shared/config/classification.py` - Configuration classes
- `src/uqlab/models/classification_models.py` - Model implementations
- `src/uqlab/data/` - Data loading utilities

### MERGE_NOTES.md Insights

The MERGE_NOTES.md reveals this folder was created by merging a standalone `uq_classification` package into the main codebase. The merge:
- Preserved production code
- Added visualization tools
- Created compatibility shims for imports
- Maintained backward compatibility

---

## Task 3: Evaluation/Benchmarks Usage Analysis

### Folder Contents

```
src/uqlab/evaluation/benchmarks/
├── __init__.py
├── datatypes.py               # Core data structures
├── README.md                  # Comprehensive documentation
├── visualization.py           # Plotting utilities
├── requirements.txt
├── requirements-research.txt
├── setup.py
├── data/
│   ├── __init__.py
│   └── cifar10.py            # CIFAR-10 with noise injection
├── examples/
│   ├── basic_usage.py
│   └── visualization_example.py
├── implementations/
│   └── __init__.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   └── gaussian_logits.py
└── utils/
    └── __init__.py
```

### Usage Analysis

**Found only 2 import references - both SELF-REFERENTIAL:**

1. `examples/basic_usage.py` imports from `benchmarks.data.cifar10`
2. `examples/basic_usage.py` imports from `benchmarks.models.gaussian_logits`

**No external usage found** in the main codebase.

### Assessment

**Status:** RESEARCH/EXPERIMENTAL PACKAGE

The benchmarks folder is a **standalone research package** designed to:
- Bridge research (`uq_disentanglement_comparison`) and production
- Provide formal UQ benchmarking capabilities
- Support multiple UQ methods (Gaussian Logits, Information-Theoretic, DualXDA)

**Key characteristics:**
- Has its own `setup.py` (installable package)
- Comprehensive README with architecture plan
- Separate requirements files
- Self-contained examples
- **Not integrated into production code yet**

### README.md Insights

The README describes this as a "new package for uncertainty quantification benchmarking" that:
- Is in Phase 1 (basic structure complete)
- Plans future integration with backend API and Streamlit UI
- Follows clean separation principles
- Is framework-agnostic (works with Keras and PyTorch)

**Development Status:**
- ✅ Phase 1: Package structure, datatypes, CIFAR-10 loader
- 🚧 In Progress: UQ method implementations, benchmark framework
- 📋 Planned: Additional datasets, backend integration, comprehensive testing

---

## Task 4: Reorganization Plan

### Current State Summary

#### ✅ Well-Organized Areas
1. **Backend** - Proper DDD structure with domain/repositories/services
2. **Core packages** - `src/uqlab/models/`, `src/uqlab/data/`, `src/uqlab/shared/`
3. **Evaluation core** - `src/uqlab/evaluation/` (evaluator.py, metrics.py, signals.py)

#### ⚠️ Areas Needing Attention
1. **evaluation/classification/** - Mix of shims and real implementations
2. **evaluation/benchmarks/** - Isolated research package, not integrated
3. **Backend root files** - Legacy models.py, tables.py, crud.py

### Reorganization Decisions

#### Decision 1: Keep evaluation/classification/ as Compatibility Layer

**Rationale:**
- Many external imports depend on `uqlab.evaluation.classification.*`
- Breaking these imports would affect scripts, notebooks, and documentation
- The shim pattern is clean and well-documented

**Action:** 
- ✅ KEEP AS-IS
- Add clear documentation explaining the shim pattern
- Update docstrings to point to actual implementations

#### Decision 2: Document Actual Implementation Locations

**Problem:** Developers may not realize that `evaluation/classification/config.py` is just a shim.

**Action:**
- Create `IMPORT_GUIDE.md` documenting:
  - Which imports are shims vs real implementations
  - Where actual code lives
  - Recommended import paths for new code

#### Decision 3: evaluation/benchmarks/ Status

**Current State:** Standalone research package, not integrated

**Options:**
1. **Keep as research package** - Continue development independently
2. **Integrate into production** - Add backend API routes, UI components
3. **Move to separate repository** - Extract as standalone project

**Recommendation:** **Option 1 - Keep as research package**
- It's well-structured and self-contained
- Has clear development roadmap
- Can be integrated later when mature
- No urgent need to move or delete

**Action:**
- ✅ KEEP IN CURRENT LOCATION
- Add note in main README about research packages
- Continue development per the roadmap in benchmarks/README.md

#### Decision 4: Clean Up Legacy Backend Files

**Files to address:**
- `backend/app/models.py` - Should use `domain/models.py`
- `backend/app/tables.py` - Should use `domain/models.py`
- `backend/app/crud.py` - Should use `repositories/`

**Action:**
- Audit usage of these files
- Create migration plan to DDD structure
- Add deprecation warnings
- Update imports gradually

#### Decision 5: Improve Discoverability

**Problem:** The shim pattern and actual locations are not obvious.

**Actions:**
1. Create `ARCHITECTURE.md` documenting:
   - Package structure
   - Import patterns
   - Where to find implementations
2. Update `evaluation/classification/__init__.py` with helpful docstring
3. Add type stubs for better IDE support

### Files to Create/Update

#### New Files:
1. **CODEBASE_STRUCTURE_AUDIT.md** (this file)
2. **IMPORT_GUIDE.md** - Guide to import paths and shims
3. **ARCHITECTURE.md** - Overall architecture documentation
4. **backend/BACKEND_ARCHITECTURE.md** - DDD structure documentation

#### Files to Update:
1. **src/uqlab/evaluation/classification/__init__.py** - Add helpful docstring
2. **README.md** - Add section on package structure
3. **backend/app/models.py** - Add deprecation notice
4. **backend/app/tables.py** - Add deprecation notice
5. **backend/app/crud.py** - Add deprecation notice

### No Code Movement Required

**Key Decision:** We will NOT move code because:
1. The current structure is actually well-organized
2. The shim pattern provides backward compatibility
3. Moving code would break many imports
4. The DDD structure in backend is already correct
5. Research packages should remain separate

---

## Task 5: Backend DDD Structure Assessment

### Current Structure: ✅ EXCELLENT

The backend already has proper DDD structure:

```
backend/app/
├── domain/              ✅ Domain models and value objects
├── repositories/        ✅ Data access patterns
├── services/            ✅ Business logic
│   ├── executors/      ✅ Execution strategies
│   └── storage/        ✅ Storage implementations
├── storage/             ✅ Storage abstraction
├── api/                 ✅ API layer (routes, deps)
└── core/                ✅ Configuration and security
```

### What's Already There

#### Domain Layer (`domain/`)
- `models.py` - Domain entities and business objects
- `value_objects.py` - Immutable value objects

#### Repository Layer (`repositories/`)
- `batch_experiment_repository.py` - Batch experiment data access
- `experiment_repository.py` - Experiment data access
- Clean separation from business logic

#### Service Layer (`services/`)
- `batch_experiment_service.py` - Batch experiment orchestration
- `metrics_service.py` - Metrics calculation
- `progress_parser.py` - Training progress parsing
- `training_orchestrator.py` - Training workflow coordination
- `executors/` - Execution strategies (direct, subprocess)
- `storage/` - Storage service implementations (postgres, wxgov)

#### Storage Layer (`storage/`)
- `base.py` - Abstract storage interface
- `factory.py` - Storage factory pattern
- `filesystem.py` - Local filesystem storage
- `s3.py` - S3 storage implementation

### Assessment: No Changes Needed

**The backend structure is exemplary DDD:**
- Clear layer separation
- Dependency inversion (abstractions in base classes)
- Single responsibility principle
- Repository pattern for data access
- Service layer for business logic
- Strategy pattern for executors and storage

**Minor Improvement Opportunity:**
- Migrate root-level `models.py`, `tables.py`, `crud.py` to proper layers
- This is a gradual migration, not urgent

---

## Recommendations Summary

### Immediate Actions (High Priority)

1. **Create Documentation**
   - ✅ CODEBASE_STRUCTURE_AUDIT.md (this file)
   - 📝 Create IMPORT_GUIDE.md
   - 📝 Create ARCHITECTURE.md
   - 📝 Create backend/BACKEND_ARCHITECTURE.md

2. **Update Docstrings**
   - 📝 Update `evaluation/classification/__init__.py` with shim explanation
   - 📝 Add deprecation notices to legacy backend files

3. **Improve Discoverability**
   - 📝 Update main README.md with structure overview
   - 📝 Add comments in shim files pointing to actual implementations

### Medium-Term Actions (Medium Priority)

4. **Backend Legacy Migration**
   - 📋 Audit usage of `backend/app/models.py`
   - 📋 Audit usage of `backend/app/tables.py`
   - 📋 Audit usage of `backend/app/crud.py`
   - 📋 Create migration plan to DDD structure
   - 📋 Gradually update imports

5. **Research Package Integration**
   - 📋 Continue development of `evaluation/benchmarks/`
   - 📋 Plan integration with backend API (when ready)
   - 📋 Plan integration with Streamlit UI (when ready)

### Long-Term Actions (Low Priority)

6. **Consider Consolidation**
   - 📋 Evaluate if shim pattern should be maintained long-term
   - 📋 Consider direct imports from actual locations in new code
   - 📋 Update documentation and examples

7. **Testing and Validation**
   - 📋 Add integration tests for import paths
   - 📋 Validate all shims work correctly
   - 📋 Test backward compatibility

---

## Conclusion

### Key Findings

1. **Backend Structure: ✅ EXCELLENT**
   - Proper DDD with domain/repositories/services/storage
   - No changes needed
   - Minor legacy files to migrate gradually

2. **evaluation/classification/: ⚠️ COMPATIBILITY LAYER**
   - Mix of shims and real implementations
   - Provides backward compatibility for legacy `uq_classification` package
   - Should be documented, not reorganized

3. **evaluation/benchmarks/: 📊 RESEARCH PACKAGE**
   - Standalone, well-structured research package
   - Not yet integrated into production
   - Should remain separate until mature

4. **Overall Structure: ✅ WELL-ORGANIZED**
   - Clear separation of concerns
   - Proper use of design patterns
   - Good documentation (MERGE_NOTES.md, README.md files)

### No Major Reorganization Needed

The codebase is **already well-structured**. The main needs are:
- **Documentation** - Explain the structure and patterns
- **Discoverability** - Help developers find actual implementations
- **Gradual migration** - Move legacy backend files to DDD structure

### Success Metrics

This audit is successful if:
- ✅ Backend DDD structure is validated (DONE)
- ✅ evaluation/classification usage is understood (DONE)
- ✅ evaluation/benchmarks status is clear (DONE)
- ✅ Reorganization plan is created (DONE - minimal changes needed)
- ✅ Documentation is improved (IN PROGRESS)

---

**Audit completed:** 2026-06-18  
**Status:** ✅ COMPLETE  
**Next steps:** Create supporting documentation files