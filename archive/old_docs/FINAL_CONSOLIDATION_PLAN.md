# Final Codebase Consolidation Plan

## Executive Summary
**Decision**: Keep NEW MLOps structure (1-7) and merge OLD code into it.
**Rationale**: The numbered structure follows industry best practices and provides better organization.

## Current State Analysis

### NEW Structure (1-7) - KEEP THIS
```
src/uqlab/
├── 1_data/          # Data loading & preprocessing
├── 2_models/        # Model architectures
├── 3_training/      # Training logic
├── 4_evaluation/    # Evaluation & metrics
├── 5_api/           # API endpoints
├── 6_ui/            # UI components
├── 7_orchestration/ # Workflow orchestration
└── shared/          # Shared utilities
```

### OLD Structure - MERGE INTO NEW
```
src/uqlab/
├── classification/        # 589 lines data_loader.py + models + evaluation
├── benchmarks/           # Benchmark implementations
├── notebook_support/     # Plotting & analysis utilities
└── disentanglement_paper/ # Research code
```

## Detailed Merge Strategy

### 1. classification/ → Multiple Destinations

#### 1.1 Data Loading
- **Source**: `classification/data_loader.py` (589 lines)
- **Destination**: `1_data/loaders.py` (718 lines - already exists)
- **Action**: COMPARE and merge unique functionality
  - Check if 1_data/loaders.py has all features from classification/data_loader.py
  - If not, add missing features
  - Keep 1_data/loaders.py as primary

#### 1.2 Models
- **Source**: `classification/models.py`, `classification/model_factory.py`, `classification/feature_extractor.py`
- **Destination**: `2_models/`
- **Action**: MOVE
  ```bash
  mv classification/models.py → 2_models/classification_models.py
  mv classification/model_factory.py → 2_models/factory.py
  mv classification/feature_extractor.py → 2_models/feature_extractors.py
  ```

#### 1.3 Evaluation
- **Source**: `classification/evaluation.py`, `classification/attribution_signals.py`, `classification/signal_formula_specs.py`
- **Destination**: `4_evaluation/`
- **Action**: MOVE
  ```bash
  mv classification/evaluation.py → 4_evaluation/evaluator.py
  mv classification/attribution_signals.py → 4_evaluation/signals/attribution.py
  mv classification/signal_formula_specs.py → 4_evaluation/signals/formulas.py
  ```

#### 1.4 Configuration
- **Source**: `classification/config.py`, `classification/config_schema.py`
- **Destination**: `shared/config/`
- **Action**: MOVE
  ```bash
  mv classification/config.py → shared/config/classification.py
  mv classification/config_schema.py → shared/config/schemas.py
  ```

#### 1.5 Utilities
- **Source**: `classification/utils.py`, `classification/unified_tracker.py`
- **Destination**: `shared/utils/`
- **Action**: MOVE
  ```bash
  mv classification/utils.py → shared/utils/classification.py
  mv classification/unified_tracker.py → shared/utils/tracking.py
  ```

#### 1.6 Visualization
- **Source**: `classification/decision_boundary_viz.py`, `classification/streamlit_viz_app.py`
- **Destination**: `6_ui/visualization/`
- **Action**: MOVE
  ```bash
  mv classification/decision_boundary_viz.py → 6_ui/visualization/decision_boundaries.py
  mv classification/streamlit_viz_app.py → 6_ui/apps/classification_viz.py
  ```

#### 1.7 watsonx Integration
- **Source**: `classification/watsonx_streamlit.py`
- **Destination**: `5_api/integrations/`
- **Action**: MOVE
  ```bash
  mv classification/watsonx_streamlit.py → 5_api/integrations/watsonx.py
  ```

#### 1.8 Archive
- **Source**: `classification/archive/`, `classification/v2/`
- **Destination**: `archive/classification/`
- **Action**: MOVE to archive

### 2. benchmarks/ → 4_evaluation/benchmarks/

- **Source**: `benchmarks/` (entire folder)
- **Destination**: `4_evaluation/benchmarks/`
- **Action**: MOVE
  ```bash
  mv benchmarks/* → 4_evaluation/benchmarks/
  ```
- **Files to move**:
  - `benchmarks/benchmarks/` → `4_evaluation/benchmarks/implementations/`
  - `benchmarks/data/` → `4_evaluation/benchmarks/data/`
  - `benchmarks/models/` → `4_evaluation/benchmarks/models/`
  - `benchmarks/utils/` → `4_evaluation/benchmarks/utils/`
  - `benchmarks/visualization.py` → `4_evaluation/benchmarks/visualization.py`
  - `benchmarks/datatypes.py` → `4_evaluation/benchmarks/datatypes.py`

### 3. notebook_support/ → shared/notebook_utils/

- **Source**: `notebook_support/` (entire folder)
- **Destination**: `shared/notebook_utils/`
- **Action**: MOVE
  ```bash
  mv notebook_support/* → shared/notebook_utils/
  ```
- **Files to move**:
  - `notebook_support/signals.py` → `shared/notebook_utils/signals.py`
  - `notebook_support/plotting.py` → `shared/notebook_utils/plotting.py`
  - `notebook_support/data_utils.py` → `shared/notebook_utils/data_utils.py`
  - `notebook_support/method_comparison*.py` → `shared/notebook_utils/comparisons/`
  - `notebook_support/metric_specs.py` → `shared/notebook_utils/metrics.py`

### 4. disentanglement_paper/ → archive/research/

- **Source**: `disentanglement_paper/` (entire folder)
- **Destination**: `archive/research/disentanglement_paper/`
- **Action**: MOVE to archive (research code, not production)
  ```bash
  mv disentanglement_paper/ → ../../archive/research/disentanglement_paper/
  ```

## Implementation Steps

### Phase 1: Create Directory Structure
```bash
cd uqlab-streamlit/src/uqlab

# Create missing subdirectories in NEW structure
mkdir -p 2_models
mkdir -p 4_evaluation/signals
mkdir -p 4_evaluation/benchmarks
mkdir -p 5_api/integrations
mkdir -p 6_ui/visualization
mkdir -p 6_ui/apps
mkdir -p shared/config
mkdir -p shared/utils
mkdir -p shared/notebook_utils/comparisons
```

### Phase 2: Move Files (Automated Script)
Create `consolidate.sh` script to perform all moves

### Phase 3: Update Imports
- Search for all imports from old locations
- Update to new locations
- Test each module

### Phase 4: Create Backward Compatibility
- Add `__init__.py` files with import redirects
- Example:
  ```python
  # classification/__init__.py
  from ..1_data.loaders import *  # Redirect old imports
  from ..2_models.classification_models import *
  ```

### Phase 5: Update Documentation
- Update all README files
- Update import examples
- Create migration guide

### Phase 6: Testing
- Run all tests
- Verify imports work
- Check Streamlit app
- Verify FastAPI backend

## Final Structure

```
src/uqlab/
├── 1_data/
│   ├── loaders.py              # MERGED: classification/data_loader.py + existing
│   └── preprocessing.py
├── 2_models/
│   ├── classification_models.py # FROM: classification/models.py
│   ├── factory.py              # FROM: classification/model_factory.py
│   ├── feature_extractors.py  # FROM: classification/feature_extractor.py
│   └── architectures/
├── 3_training/
│   └── trainer.py
├── 4_evaluation/
│   ├── evaluator.py            # FROM: classification/evaluation.py
│   ├── benchmarks/             # FROM: benchmarks/
│   │   ├── implementations/
│   │   ├── data/
│   │   ├── models/
│   │   ├── utils/
│   │   ├── visualization.py
│   │   └── datatypes.py
│   └── signals/
│       ├── attribution.py      # FROM: classification/attribution_signals.py
│       └── formulas.py         # FROM: classification/signal_formula_specs.py
├── 5_api/
│   ├── endpoints/
│   └── integrations/
│       └── watsonx.py          # FROM: classification/watsonx_streamlit.py
├── 6_ui/
│   ├── apps/
│   │   └── classification_viz.py # FROM: classification/streamlit_viz_app.py
│   └── visualization/
│       └── decision_boundaries.py # FROM: classification/decision_boundary_viz.py
├── 7_orchestration/
│   └── workflows.py
├── shared/
│   ├── config/
│   │   ├── classification.py   # FROM: classification/config.py
│   │   └── schemas.py          # FROM: classification/config_schema.py
│   ├── utils/
│   │   ├── classification.py   # FROM: classification/utils.py
│   │   └── tracking.py         # FROM: classification/unified_tracker.py
│   └── notebook_utils/         # FROM: notebook_support/
│       ├── signals.py
│       ├── plotting.py
│       ├── data_utils.py
│       ├── metrics.py
│       └── comparisons/
│           ├── method_comparison.py
│           └── method_comparison_plotly.py
└── ui_components/              # SYMLINK (keep as-is)

archive/
├── legacy_src/                 # Already moved
├── research/
│   ├── uq_disentanglement_comparison-72CC/  # Already moved
│   └── disentanglement_paper/  # TO MOVE
└── classification/
    ├── archive/                # FROM: classification/archive/
    └── v2/                     # FROM: classification/v2/
```

## Benefits of This Structure

1. **Clear Separation of Concerns**: Each numbered folder has a specific purpose
2. **Industry Standard**: Follows MLOps best practices
3. **Scalability**: Easy to add new components
4. **Maintainability**: Clear where to find/add code
5. **Backward Compatible**: Old imports still work via redirects

## Risks & Mitigation

### Risk 1: Breaking Imports
- **Mitigation**: Create backward compatibility layer in old folders
- **Test**: Run full test suite after each phase

### Risk 2: Lost Functionality
- **Mitigation**: Careful comparison of data_loader.py files
- **Test**: Verify all features work

### Risk 3: Merge Conflicts
- **Mitigation**: Move files first, then merge logic
- **Test**: Git diff to verify no code lost

## Next Steps

1. **Review this plan** - Confirm approach
2. **Create consolidation script** - Automate file moves
3. **Execute Phase 1** - Create directories
4. **Execute Phase 2** - Move files
5. **Execute Phase 3** - Update imports
6. **Execute Phase 4** - Add backward compatibility
7. **Execute Phase 5** - Update docs
8. **Execute Phase 6** - Test everything