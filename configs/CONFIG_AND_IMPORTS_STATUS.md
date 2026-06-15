# Configuration and Imports Status

## Summary

After codebase consolidation, here's the current state of configs and imports in `walaris-cen`.

## 1. Configuration Files

### Old YAML Configs (Still Valid)
Located in [`configs/`](configs:1):
```
configs/
├── example_cnn_mcdropout.yaml
├── example_resnet18_mcdropout.yaml
├── experiment/
│   ├── default.yaml
│   └── fast_pilot.yaml
└── test/
    ├── test_cnn_mcdropout.yaml
    ├── test_dinov2_mlp.yaml
    └── test_resnet18_mcdropout.yaml
```

**Status**: ✅ **Still valid and used by [`run_fast.py`](run_fast.py:1)**

### New Python Configs (Post-Consolidation)
Located in [`src/walaris/shared/config/`](src/walaris/shared/config:1):
- [`classification.py`](src/walaris/shared/config/classification.py:1) - Main config classes
- [`schemas.py`](src/walaris/shared/config/schemas.py:1) - Pydantic schemas

**Status**: ✅ **Active - Used by new MLOps structure**

### Multiple ExperimentConfig Classes
Found in 3 locations:
1. [`src/walaris/shared/config/classification.py`](src/walaris/shared/config/classification.py:1) - **Primary**
2. [`src/walaris/shared/config/schemas.py`](src/walaris/shared/config/schemas.py:1) - Pydantic version
3. [`src/walaris/4_evaluation/benchmarks/datatypes.py`](src/walaris/4_evaluation/benchmarks/datatypes.py:1) - Benchmark-specific

**Recommendation**: Consolidate these into a single source of truth.

## 2. Import Structure

### Current Import Patterns in `run_fast.py`

#### ✅ Working: Archived `src.*` Imports (Restored)
```python
from src.data.cifar10n_loader import CIFAR10NDataset
from src.metrics.mc_dropout_uq import calculate_mc_dropout_uncertainty
from src.triage.dualxda_axioms import DualXDATracer
```

**Status**: ✅ **RESTORED** - Copied back from `archive/legacy_src/` to `src/`

**Why**: 8+ files still use these imports, including:
- `run_fast.py`
- Various scripts
- Notebooks

#### ✅ Working: `uq_classification.*` Imports (Backward Compatible)
```python
from uq_classification.models import EmbeddingDataset
from uq_classification.config import ExperimentConfig
from uq_classification.model_factory import build_model
from uq_classification.feature_extractor import create_feature_extractor
from uq_classification.utils import auto_device, dino_transform
from uq_classification.data_loader import EmbeddingOrganizer, SplitSpec
from uq_classification.signal_formula_specs import build_signal_formula_manifest
from uq_classification.evaluation import binary_auroc, save_per_sample_csv
```

**How it works**:
1. `uq_classification` is a **symlink** → `src/walaris/classification`
2. [`classification/__init__.py`](src/walaris/classification/__init__.py:1) has **backward compatibility redirects**
3. Imports are redirected to new locations in MLOps structure

**Maps to**:
- `uq_classification.models` → [`2_models/classification_models.py`](src/walaris/2_models/classification_models.py:1)
- `uq_classification.model_factory` → [`2_models/factory.py`](src/walaris/2_models/factory.py:1)
- `uq_classification.feature_extractor` → [`2_models/feature_extractors.py`](src/walaris/2_models/feature_extractors.py:1)
- `uq_classification.config` → [`shared/config/classification.py`](src/walaris/shared/config/classification.py:1)
- `uq_classification.utils` → [`shared/utils/classification.py`](src/walaris/shared/utils/classification.py:1)
- `uq_classification.data_loader` → [`classification/data_loader.py`](src/walaris/classification/data_loader.py:1) ⚠️ *needs merge*
- `uq_classification.signal_formula_specs` → [`4_evaluation/signals/formulas.py`](src/walaris/4_evaluation/signals/formulas.py:1)
- `uq_classification.evaluation` → [`4_evaluation/evaluator.py`](src/walaris/4_evaluation/evaluator.py:1)

#### ✅ Working: `walaris.*` Imports
```python
from walaris.run_artifacts import save_zwischen_result
```

**Status**: ✅ **Works** - File exists at [`src/walaris/run_artifacts.py`](src/walaris/run_artifacts.py:1)

## 3. Current Directory Structure

```
walaris-cen/
├── configs/                    # ✅ YAML configs (still used)
│   ├── experiment/
│   └── test/
├── src/
│   ├── data/                   # ✅ RESTORED from archive
│   ├── metrics/                # ✅ RESTORED from archive
│   ├── triage/                 # ✅ RESTORED from archive
│   ├── models/                 # ✅ RESTORED from archive
│   ├── experiments/            # ✅ RESTORED from archive
│   ├── utils/                  # ✅ RESTORED from archive
│   └── walaris/                # ✅ NEW MLOps structure
│       ├── 1_data/
│       ├── 2_models/
│       ├── 3_training/
│       ├── 4_evaluation/
│       ├── 5_api/
│       ├── 6_ui/
│       ├── 7_orchestration/
│       ├── shared/
│       ├── classification/     # Backward compat + data_loader.py
│       ├── benchmarks/         # Backward compat only
│       └── notebook_support/   # Backward compat only
├── archive/
│   ├── legacy_src/             # Original archived location
│   └── research/
└── run_fast.py                 # ✅ Main entry point
```

## 4. What Models/Configs Are Used Now?

### Primary Models (New Structure)
Located in [`src/walaris/2_models/`](src/walaris/2_models:1):
- **DINOv2 Feature Extractor** - [`feature_extractors.py`](src/walaris/2_models/feature_extractors.py:1)
- **Classification Models** - [`classification_models.py`](src/walaris/2_models/classification_models.py:1)
- **Model Factory** - [`factory.py`](src/walaris/2_models/factory.py:1)
- **Uncertainty Models** - [`uncertainty.py`](src/walaris/2_models/uncertainty.py:1)

### Primary Configs (New Structure)
Located in [`src/walaris/shared/config/`](src/walaris/shared/config:1):
- **ExperimentConfig** - [`classification.py`](src/walaris/shared/config/classification.py:1)
- **Pydantic Schemas** - [`schemas.py`](src/walaris/shared/config/schemas.py:1)

### Legacy Configs (Still Used)
- **YAML files** in [`configs/`](configs:1) - Used by `run_fast.py` and scripts

## 5. Action Items

### ✅ Completed
1. Restored `src/data/`, `src/metrics/`, `src/triage/` from archive
2. Maintained backward compatibility for `uq_classification.*` imports
3. Verified all import paths work

### ⚠️ Pending (Optional Improvements)
1. **Merge data loaders**: 
   - [`classification/data_loader.py`](src/walaris/classification/data_loader.py:1) (589 lines)
   - [`1_data/loaders.py`](src/walaris/1_data/loaders.py:1) (718 lines)

2. **Consolidate ExperimentConfig**: Choose one primary location

3. **Migrate YAML configs**: Consider moving to Python configs for better type safety

4. **Update imports gradually**: Migrate from `uq_classification.*` to direct imports from new structure

## 6. Recommendations

### For New Code
Use the new MLOps structure directly:
```python
# Instead of:
from uq_classification.models import SomeModel

# Use:
from walaris.2_models.classification_models import SomeModel
```

### For Existing Code
Keep using current imports - they work via backward compatibility:
```python
# These still work:
from uq_classification.models import EmbeddingDataset
from src.data.cifar10n_loader import CIFAR10NDataset
```

### Config Strategy
- **Short term**: Keep using YAML configs in `configs/`
- **Long term**: Migrate to Python configs in `src/walaris/shared/config/`

## 7. Summary

✅ **All imports work** - Both old and new  
✅ **Configs are valid** - YAML and Python both active  
✅ **Backward compatible** - No breaking changes  
✅ **New structure ready** - Can start using MLOps folders  

**Bottom line**: Everything works! You can continue using existing code while gradually migrating to the new structure.