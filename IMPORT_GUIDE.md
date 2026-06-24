# Import Guide for UQLab-Streamlit

**Purpose:** Help developers understand import patterns and where implementations live.

> **2026 update:** `uqlab.evaluation.classification` shims were removed. See
> [docs/architecture/classification-package-redirect.md](docs/architecture/classification-package-redirect.md).

---

## Quick Reference

### Recommended imports (direct from source)

```python
# Configuration
from uqlab.shared.config.classification import ExperimentConfig, ModelConfig, DataConfig

# Models
from uqlab.models.classification_models import EmbeddingDataset, EmbeddingDropoutMLP
from uqlab.models.factory import build_model
from uqlab.models.feature_extractors import create_feature_extractor, DINOv2FeatureExtractor

# Data loading
from uqlab.data.loaders.cifar10n_loader import CIFAR10NDataset
from uqlab.data import SplitSpec, EmbeddingOrganizer, sample_indices_for_fast_pilot
from uqlab.data.fast_pilot_loader import train_feature_model
from uqlab.data.image_dataset import ClassificationImageDataset, load_image_datasets

# Fast-pilot pipeline
from uqlab.evaluation.pipeline.data_setup import prepare_fast_pilot_data
from uqlab.evaluation.pipeline.fast_pilot_eval import collect_uncertainty_signals

# Evaluation
from uqlab.evaluation.metrics import binary_auroc, evaluate_three_way_classification

# Training
from uqlab.training.trainer import Trainer
from uqlab.training.callbacks import CheckpointCallback
```

### Removed legacy package

`uqlab.evaluation.classification.*` shims no longer exist. The abandoned `uqlab.api` REST
routers live in `dead_code/api/`; use `backend/app/api/routes/` instead.

---

## Understanding the Shim Pattern

### What is a Shim?

A **shim** is a compatibility layer that redirects imports to their actual location. This maintains backward compatibility when code is reorganized.

### Example: config.py Shim

```python
# File: src/uqlab/evaluation/classification/config.py
"""Shim: uq_classification.config → uqlab.shared.config.classification"""

from uqlab.shared.config.classification import (
    DataConfig,
    ExperimentConfig,
    ModelConfig,
    # ... other imports
)

__all__ = ["DataConfig", "ExperimentConfig", "ModelConfig", ...]
```

When you import:
```python
from uqlab.evaluation.classification.config import ExperimentConfig
```

You actually get:
```python
from uqlab.shared.config.classification import ExperimentConfig
```

---

## Import Map: Where Things Actually Live

### Configuration Classes

| Legacy Import | Actual Location | Status |
|--------------|-----------------|--------|
| `uqlab.evaluation.classification.config` | `uqlab.shared.config.classification` | SHIM |

**Actual Implementation:**
```python
# src/uqlab/shared/config/classification.py
@dataclass
class ExperimentConfig:
    model: ModelConfig
    data: DataConfig
    training: TrainingConfig
    evaluation: EvaluationConfig
    paths: PathConfig
```

**Recommended Import:**
```python
from uqlab.shared.config.classification import ExperimentConfig
```

### Model Classes

| Legacy Import | Actual Location | Status |
|--------------|-----------------|--------|
| `uqlab.evaluation.classification.models` | `uqlab.models.classification_models` | SHIM |

**Actual Implementation:**
```python
# src/uqlab/models/classification_models.py
class EmbeddingDataset(Dataset):
    """Dataset for pre-computed embeddings."""
    ...

class EmbeddingDropoutMLP(nn.Module):
    """MLP with dropout for uncertainty estimation."""
    ...
```

**Recommended Import:**
```python
from uqlab.models.classification_models import EmbeddingDataset, EmbeddingDropoutMLP
```

### Data Loading

| Import Path | Location | Status |
|------------|----------|--------|
| `uqlab.evaluation.classification.data_loader` | Same location | REAL |
| `uqlab.data` | `src/uqlab/data/__init__.py` | REAL |

**Note:** `data_loader.py` contains real implementations, not shims!

```python
# src/uqlab/evaluation/classification/data_loader.py
@dataclass
class SplitSpec:
    """Specification of train/eval data splits."""
    train_indices: np.ndarray
    clean_eval_indices: np.ndarray
    aleatoric_eval_indices: np.ndarray
    epistemic_eval_indices: np.ndarray
    under_supported_classes: List[int]

class EmbeddingOrganizer:
    """Organizes embeddings for training and evaluation."""
    ...
```

**Recommended Import:**
```python
# Either works (data_loader is real implementation)
from uqlab.evaluation.classification.data_loader import SplitSpec, EmbeddingOrganizer

# Or use the re-export from uqlab.data
from uqlab.data import SplitSpec, EmbeddingOrganizer
```

### Evaluation Functions

| Import Path | Location | Status |
|------------|----------|--------|
| `uqlab.evaluation.classification.evaluation` | Same location | REAL |
| `uqlab.evaluation.metrics` | `src/uqlab/evaluation/metrics.py` | REAL |

**Both are real implementations:**

```python
# src/uqlab/evaluation/classification/evaluation.py
def binary_auroc(y_true, y_scores):
    """Compute binary AUROC."""
    ...

def evaluate_three_way_classification(signals, labels):
    """Evaluate three-way classification."""
    ...
```

**Recommended Import:**
```python
from uqlab.evaluation.classification.evaluation import binary_auroc
# Or
from uqlab.evaluation.metrics import binary_auroc
```

---

## Package Structure Overview

```
src/uqlab/
├── evaluation/
│   ├── classification/          # Mix of SHIMS and REAL implementations
│   │   ├── config.py           # SHIM → uqlab.shared.config.classification
│   │   ├── models.py           # SHIM → uqlab.models.classification_models
│   │   ├── data_loader.py      # REAL - Data loading utilities
│   │   ├── evaluation.py       # REAL - Evaluation metrics
│   │   ├── feature_extractor.py # REAL - Feature extraction
│   │   ├── model_factory.py    # REAL - Model factory
│   │   ├── utils.py            # REAL - Utility functions
│   │   └── ...
│   ├── benchmarks/             # Research package (standalone)
│   ├── legacy/                 # Legacy code
│   ├── evaluator.py            # Core evaluator
│   ├── metrics.py              # Core metrics
│   └── signals.py              # Signal computation
├── models/                      # ACTUAL model implementations
│   ├── classification_models.py # EmbeddingDataset, EmbeddingDropoutMLP
│   ├── feature_extractors.py   # Feature extraction models
│   ├── architectures.py         # Model architectures
│   └── ...
├── data/                        # ACTUAL data implementations
│   ├── loaders/
│   │   └── cifar10n_loader.py  # CIFAR10NDataset
│   ├── preprocessing.py
│   └── ...
├── shared/                      # ACTUAL shared implementations
│   ├── config/
│   │   └── classification.py   # ExperimentConfig, ModelConfig, etc.
│   └── utils/
│       └── classification.py   # Utility functions
└── ...
```

---

## Decision Tree: Which Import Should I Use?

### For New Code

```
Are you writing new code?
├─ YES → Use direct imports from actual locations
│         from uqlab.shared.config.classification import ExperimentConfig
│         from uqlab.models.classification_models import EmbeddingDataset
│
└─ NO → Maintaining existing code?
          ├─ Keep existing imports (they work via shims)
          └─ Consider updating to direct imports for clarity
```

### For Configuration

```
Need configuration classes?
└─ Use: from uqlab.shared.config.classification import ExperimentConfig
   (Not: from uqlab.evaluation.classification.config import ExperimentConfig)
```

### For Models

```
Need model classes?
└─ Use: from uqlab.models.classification_models import EmbeddingDataset
   (Not: from uqlab.evaluation.classification.models import EmbeddingDataset)
```

### For Data Loading

```
Need data loading utilities?
├─ SplitSpec, EmbeddingOrganizer:
│  └─ Use: from uqlab.evaluation.classification.data_loader import SplitSpec
│     (This is the actual implementation, not a shim)
│
└─ Dataset classes:
   └─ Use: from uqlab.data.loaders.cifar10n_loader import CIFAR10NDataset
```

### For Evaluation

```
Need evaluation functions?
└─ Use: from uqlab.evaluation.classification.evaluation import binary_auroc
   (This is the actual implementation, not a shim)
```

---

## Backend Imports

### Domain-Driven Design Structure

```python
# Domain models
from backend.app.domain.models import Experiment, BatchExperiment
from backend.app.domain.value_objects import ExperimentStatus

# Repositories (data access)
from backend.app.repositories.experiment_repository import ExperimentRepository
from backend.app.repositories.batch_experiment_repository import BatchExperimentRepository

# Services (business logic)
from backend.app.services.batch_experiment_service import BatchExperimentService
from backend.app.services.training_orchestrator import TrainingOrchestrator

# Storage
from backend.app.storage.factory import create_storage
from backend.app.storage.filesystem import FilesystemStorage
from backend.app.storage.s3 import S3Storage
```

### ⚠️ Legacy Backend Imports (Avoid in New Code)

```python
# These exist for backward compatibility but should be avoided
from backend.app.models import Experiment  # Use domain.models instead
from backend.app.tables import experiments  # Use domain.models instead
from backend.app.crud import get_experiment  # Use repositories instead
```

---

## Common Patterns

### Pattern 1: Training Script

```python
# Configuration
from uqlab.shared.config.classification import ExperimentConfig

# Models
from uqlab.models.classification_models import EmbeddingDropoutMLP
from uqlab.models.feature_extractors import create_feature_extractor

# Data
from uqlab.data.loaders.cifar10n_loader import CIFAR10NDataset
from uqlab.evaluation.classification.data_loader import SplitSpec

# Training
from uqlab.training.trainer import Trainer

# Evaluation
from uqlab.evaluation.classification.evaluation import binary_auroc
```

### Pattern 2: Backend API Route

```python
# Domain
from backend.app.domain.models import Experiment

# Repository
from backend.app.repositories.experiment_repository import ExperimentRepository

# Service
from backend.app.services.training_orchestrator import TrainingOrchestrator

# Storage
from backend.app.storage.factory import create_storage
```

### Pattern 3: Streamlit UI Component

```python
# Configuration
from uqlab.shared.config.classification import ExperimentConfig

# Evaluation
from uqlab.evaluation.classification.evaluation import evaluate_three_way_classification

# Visualization
from uqlab.ui_components.visualization.signals import plot_signal_distribution

# Backend API
from backend.app.api.routes.experiments import get_experiment
```

---

## Migration Guide

### Updating Legacy Imports

If you have code using legacy imports, here's how to update:

#### Before (Legacy)
```python
from uqlab.evaluation.classification.config import ExperimentConfig, ModelConfig
from uqlab.evaluation.classification.models import EmbeddingDataset
```

#### After (Direct)
```python
from uqlab.shared.config.classification import ExperimentConfig, ModelConfig
from uqlab.models.classification_models import EmbeddingDataset
```

### Why Update?

1. **Clarity** - See where code actually lives
2. **Performance** - Skip the shim layer (minimal impact)
3. **Maintainability** - Easier to understand codebase structure
4. **Future-proof** - Shims may be deprecated eventually

### When NOT to Update

- **Scripts in production** - If it works, don't break it
- **External dependencies** - If other projects depend on legacy imports
- **Documentation examples** - Update when documentation is revised

---

## FAQ

### Q: Why do shims exist?

**A:** The codebase was reorganized from a standalone `uq_classification` package into the main `uqlab` package. Shims maintain backward compatibility so existing scripts, notebooks, and documentation continue to work.

### Q: Should I use shims in new code?

**A:** No. Use direct imports from actual locations. Shims are for backward compatibility only.

### Q: Will shims be removed?

**A:** Not in the near future. They provide valuable backward compatibility. If removed, there will be a deprecation period with warnings.

### Q: How do I know if an import is a shim?

**A:** Check the file. Shims are small files that just re-export from another location:

```python
# This is a shim
from uqlab.actual.location import Thing
__all__ = ["Thing"]
```

### Q: What about `evaluation/classification/data_loader.py`?

**A:** That's NOT a shim - it's a real implementation. It contains actual data loading code that's actively used.

### Q: Can I mix legacy and direct imports?

**A:** Yes, they work together. But for consistency, prefer one style per file.

---

## Best Practices

### ✅ DO

- Use direct imports in new code
- Import from actual locations (`uqlab.shared.config`, `uqlab.models`)
- Check file contents if unsure whether it's a shim
- Update imports when refactoring existing code

### ❌ DON'T

- Use shim imports in new code
- Mix import styles unnecessarily
- Break existing working code to "fix" imports
- Remove shims without a deprecation plan

---

## Getting Help

### Check the Source

If unsure where something lives:

```bash
# Find where a class is defined
grep -r "class ExperimentConfig" src/

# Find where a function is defined
grep -r "def binary_auroc" src/

# Check if a file is a shim
cat src/uqlab/evaluation/classification/config.py
```

### IDE Support

Modern IDEs (VS Code, PyCharm) can "Go to Definition" to show actual implementation location.

### Documentation

- See `CODEBASE_STRUCTURE_AUDIT.md` for detailed structure analysis
- See `ARCHITECTURE.md` for overall architecture (if exists)
- See package-specific README files for module documentation

---

**Last Updated:** 2026-06-18  
**Maintained By:** Development Team  
**Related Docs:** CODEBASE_STRUCTURE_AUDIT.md, ARCHITECTURE.md