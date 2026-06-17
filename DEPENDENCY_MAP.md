# Dependency Map - uqlab-streamlit

**Generated**: 2026-06-08  
**Purpose**: Map which applications use which packages and files

## Summary

| Application | Uses uqlab | Uses uqlab_orchestrator | Uses backend API | Imports backend models |
|-------------|------------|-------------------------|------------------|----------------------|
| `streamlit_app.py` | ✅ Yes | ❌ No | ✅ Yes (HTTP) | ❌ No |
| `streamlit_app_progressive.py` | ✅ Yes | ✅ Yes | ✅ Yes (HTTP) | ✅ Yes (types) |
| `backend/` | ❌ No | ❌ No | N/A (is backend) | N/A |

## Detailed Analysis

### streamlit_app.py (Legacy Streamlit App)

**Imports from our packages**:
- `uqlab` ✅
- `ui_components` (root-level shim) ⚠️

**Key imports**:

#### From ui_components (root-level):
```python
from ui_components import (
    build_base_experiment_config,
    render_batch_results,
    render_batch_sweep_config,
    render_dataset_selection,
    render_unified_builder,
    render_hypothesis_validation_tab,
    # ... 30+ UI component functions
)
```

#### From uqlab:
```python
from uqlab.ui_components.visualization.analysis.uq_benchmarks import render_uq_benchmarks_tab
```

#### From uq_classification:
```python
from uq_classification.watsonx_streamlit import render_cloud_mode_toggle
```

**Purpose**: Legacy Streamlit app with comprehensive UI components

**Status**: ⚠️ Legacy - Uses old root-level `ui_components` shim (should migrate to `src/uqlab/ui_components`)

**Backend Usage**:
- ✅ Uses backend via HTTP API calls (`requests.get()`)
- Calls `/api/v1/datasets/{dataset_name}/stats` endpoint
- Uses `API_BASE_URL` and `API_TOKEN` for authentication
- Does NOT import backend models (uses HTTP responses directly)

**Issues**:
- Imports from root-level `ui_components/` instead of `src/uqlab/ui_components/`
- Mixed import patterns (some from uqlab, some from root)
- Should be migrated to use organized structure like progressive app

---

### streamlit_app_progressive.py (Modern Progressive App)

**Imports from our packages**:
- `uqlab` ✅
- `uqlab_orchestrator` ✅
- `app` (backend domain models) ✅

**Key imports**:

#### From uqlab_orchestrator:
```python
from uqlab_orchestrator.experiment_config import (
    build_base_experiment_config,
    build_nested_experiment_config,
)
from uqlab_orchestrator import BatchGenerator, SweepType
```

#### From uqlab (shared config):
```python
from uqlab.shared.config.workflow_validation import (
    validate_workflow,
    get_validation_errors,
)
```

#### From uqlab (UI components):
```python
# Results display
from uqlab.ui_components.results import (
    experiment_results_path,
    fetch_experiments_for_ui,
    fetch_experiments_from_api,
    render_experiment_results_panel,
)

# Experiment selectors
from uqlab.ui_components.selectors.smart_experiment_selector import (
    render_smart_experiment_selector,
    render_sweep_launch_controls,
    render_sweep_launch_toolbar,
)

# Signal visualization
from uqlab.ui_components.visualization.signals.signal_sweep_paper_viz import (
    render_production_signal_sweep_grid,
)
```

#### From uqlab (validation config - optional):
```python
try:
    from uqlab.validation_config import (
        LABEL_NOISE_SWEEP,
        TRAINING_CONFIG,
        aligned_sweep_summary,
        aligned_under_train_sweep,
    )
except ImportError:
    # Fallback to defaults
    pass
```

#### From app (backend domain models):
```python
from app.domain.models import (
    ExperimentConfig,
    DataConfig,
    ModelConfig,
    TrainingRuntimeConfig,
    EvaluationConfig,
    PathsConfig,
)
```

**Backend Usage**:
- ✅ Uses backend via HTTP API calls (`requests.get()`, `requests.post()`)
- Imports backend domain models for type safety (`ExperimentConfig`, `DataConfig`, etc.)
- Calls various `/api/v1/` endpoints for experiments, datasets, etc.
- Uses `API_BASE_URL` and `API_TOKEN` for authentication

**Purpose**: Modern progressive Streamlit app with full MLOps pipeline integration

**Status**: ✅ Active - Current production app

**Architecture**: Clean separation of concerns with proper import hierarchy

---

### backend/ (FastAPI Backend)

**Imports from our packages**:
- None detected (backend is independent)

**Purpose**: FastAPI backend for experiment management

**Status**: ✅ Active - Independent service

**API Consumers**:
- `streamlit_app.py` - Calls backend via HTTP (no model imports)
- `streamlit_app_progressive.py` - Calls backend via HTTP + imports domain models for type safety

**Note**: Backend does NOT import from `uqlab` or `uqlab_orchestrator`. This is correct - the backend is a separate service that provides REST APIs. Both Streamlit apps consume these APIs via HTTP requests.

---

## Package Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    streamlit_app.py                         │
│                    (Legacy App)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├─> uqlab.ui_components
                         │   └─> visualization.analysis.uq_benchmarks
                         │
                         └─> (No orchestrator, No backend)

┌─────────────────────────────────────────────────────────────┐
│              streamlit_app_progressive.py                    │
│              (Modern Progressive App)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├─> uqlab_orchestrator
                         │   ├─> experiment_config
                         │   ├─> BatchGenerator, SweepType
                         │   └─> api_client
                         │
                         ├─> uqlab
                         │   ├─> shared.config.workflow_validation
                         │   ├─> ui_components.results
                         │   ├─> ui_components.selectors
                         │   ├─> ui_components.visualization
                         │   └─> ui_components.orchestration
                         │
                         └─> app (backend domain models)
                             └─> domain.models

┌─────────────────────────────────────────────────────────────┐
│                      backend/                                │
│                   (FastAPI Service)                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         └─> (Independent - No uqlab imports)
```

## Architecture Layers

### Layer 1: Backend (Independent)
- **Package**: `backend/app/`
- **Purpose**: REST API for experiment management
- **Dependencies**: None from our packages
- **Used by**: Streamlit apps via HTTP

### Layer 2: ML Core
- **Package**: `src/uqlab/`
- **Purpose**: ML pipeline (data, models, training, evaluation)
- **Dependencies**: None (base layer)
- **Used by**: Orchestrator, Streamlit apps

### Layer 3: Orchestration
- **Package**: `src/uqlab_orchestrator/`
- **Purpose**: Experiment coordination, sweep generation
- **Dependencies**: None (parallel to ML Core)
- **Used by**: Streamlit progressive app

### Layer 4: UI Layer
- **Package**: `src/uqlab/ui_components/`
- **Purpose**: Reusable Streamlit components
- **Dependencies**: uqlab (ML Core)
- **Used by**: Streamlit apps

### Layer 5: Applications
- **Files**: `streamlit_app.py`, `streamlit_app_progressive.py`
- **Purpose**: End-user applications
- **Dependencies**: All layers

## Import Patterns

### ✅ Good Patterns (streamlit_app_progressive.py)

1. **Orchestrator for coordination**:
   ```python
   from uqlab_orchestrator.experiment_config import build_base_experiment_config
   from uqlab_orchestrator.api_client import launch_api_sweep
   ```

2. **UI components for visualization**:
   ```python
   from uqlab.ui_components.results import render_experiment_results_panel
   from uqlab.ui_components.selectors.smart_experiment_selector import render_smart_experiment_selector
   ```

3. **Backend models for type safety**:
   ```python
   from app.domain.models import ExperimentCreate, ExperimentStatus
   ```

### ⚠️ Legacy Patterns (streamlit_app.py)

1. **Direct UI component import** (old structure):
   ```python
   from uqlab.ui_components.visualization.analysis.uq_benchmarks import render_uq_benchmarks_tab
   ```

## Recommendations

1. **Migrate streamlit_app.py** to use orchestrator pattern like progressive app
2. **Keep backend independent** - no imports from uqlab/orchestrator
3. **Use progressive app as template** for new features
4. **Deprecate streamlit_app.py** once all features migrated

## File Count

- **Total Python files**: 150
- **uqlab package**: ~130 files
- **uqlab_orchestrator package**: ~20 files
- **Streamlit apps**: 2 files
- **Backend**: Separate (not counted)

## Related Documentation

- `FOLDER_CONSOLIDATION_ANALYSIS.md` - Folder structure analysis
- `IMPORT_FIXES_SUMMARY.md` - Import fixes applied
- `PYTHON_FILES_INVENTORY.md` - Complete file listing
- `6_UI_TO_LEGACY_MIGRATION_PLAN.md` - Legacy UI migration plan