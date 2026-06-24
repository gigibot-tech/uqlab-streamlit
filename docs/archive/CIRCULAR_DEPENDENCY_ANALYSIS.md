# UI / Core Coupling Analysis (resolved: catalog split + facade)

## Problem Statement (reframed)

**Issue**: The Streamlit workflow UI was **eagerly importing torch** at startup through a shared import chain — not because of a true import cycle (core never imports `ui_components`, and UI never calls `pipeline.run`).

**Root cause**: `workflow` → `orchestrator.config` / `shared.config.signals` → `evaluation.signals.registry` (which imports `torch` and attribution sources at module load). Step 5 also pulled `thesis_diagram_viz` → `fast_pilot_loader` at import time.

**Answer to “isn’t that bad?”**: The coupling was **shared low-layer + eager imports**, not bidirectional architecture. Both UI and runner legitimately need signal *metadata*; only the runner needs signal *compute*.

## Resolution (implemented)

```text
ui_components/workflow  →  uqlab_orchestrator.* facades  →  signals/catalog.py (no torch)
runner / pipeline       →  signals/registry.py (torch + compute)
```

| Piece | Path | Torch? |
|-------|------|--------|
| **Catalog (light)** | `evaluation/signals/catalog.py` | No — `MetricMeta`, groups, aliases |
| **Registry (heavy)** | `evaluation/signals/registry.py` | Yes — `MetricEntry.compute`, `build_signal_table` |
| **Signal facade** | `uqlab_orchestrator/signal_facade.py` | No — Step 4 groups / defaults |
| **Dataset facade** | `uqlab_orchestrator/dataset_facade.py` | No — dataset spec for Step 1 |

**UI rule**: `ui_components/workflow/*` imports `uqlab_orchestrator.*` and `uqlab.ui_components.*` only (allowlist: `runtime_paths`). Guarded by `tests/test_ui_import_is_light.py`.

**Package `__init__` rule**: `workflow`, `signals`, `evaluation.pipeline`, `data`, `orchestrator` root packages use lazy exports so `import uqlab.ui_components.workflow` does not transitively load torch.

---

## Historical note (pre-refactor architecture sketch)

The sections below describe the *original* concern (UI reaching into `uqlab.*` internals). The facade + catalog split above is the implemented fix; runner/evaluator paths still import `registry` for compute — by design.

## Original framing (problematic import graph)

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Components (Frontend)                 │
│  src/uqlab/ui_components/workflow/                          │
│    ├─ step1_dataset.py                                      │
│    ├─ step2_training.py                                     │
│    ├─ step3_uncertainty.py                                  │
│    ├─ step4_evaluation.py                                   │
│    └─ step5_review.py                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ imports from
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Core Library (Backend)                    │
│  src/uqlab/                                                  │
│    ├─ data/                                                  │
│    │   ├─ dataset_registry.py                               │
│    │   └─ fast_pilot_loader.py                              │
│    ├─ evaluation/                                            │
│    │   ├─ signals/registry.py                               │
│    │   └─ pipeline/                                          │
│    ├─ models/                                                │
│    ├─ runner/                                                │
│    │   ├─ fast_pilot_core.py                                │
│    │   └─ pipeline.py                                        │
│    └─ shared/config/                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ ALSO imports from
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              Same Core Library Modules!                      │
│  (runner, pipeline, evaluation all import from uqlab.*)     │
└─────────────────────────────────────────────────────────────┘
```

### Specific Import Violations

#### UI Components → Core Library
```python
# ui_components/workflow/step1_dataset.py
from uqlab.data.dataset_registry import get_dataset_spec

# ui_components/workflow/step3_uncertainty.py
from uqlab_orchestrator.per_class_sweep import generate_per_class_experiments

# ui_components/workflow/step4_evaluation.py
from uqlab.evaluation.signals.registry import normalize_signal_id
from uqlab.shared.config.signals import DEFAULT_SELECTED_SIGNALS
```

#### Core Library → Same Modules
```python
# runner/fast_pilot_core.py
from uqlab.data.dataset_registry import get_dataset_spec  # ← Same import!
from uqlab.evaluation.signals.formulas import build_signal_formula_manifest
from uqlab.models.factory import build_model

# runner/pipeline.py
from uqlab.shared.config.classification import ExperimentConfig
from uqlab.models.architecture import normalize_architecture
```

---

## Why This Is Bad

### 1. **Tight Coupling**
- UI components directly depend on internal implementation details
- Changes to core library break UI components
- Cannot evolve UI and core independently

### 2. **Testability Issues**
- Cannot test UI components without full core library
- Cannot mock/stub core functionality easily
- Integration tests become mandatory

### 3. **Deployment Complexity**
- UI components cannot be packaged separately
- Core library changes require UI redeployment
- Violates single responsibility principle

### 4. **Circular Import Risk**
- If core library ever imports from `ui_components`, you get circular imports
- Python's import system can handle some cases, but it's fragile
- Refactoring becomes dangerous

### 5. **Violation of Layered Architecture**
```
❌ Current (Bad):
UI Layer ←→ Core Layer  (bidirectional)

✅ Should Be:
UI Layer → Facade Layer → Core Layer  (unidirectional)
```

---

## Solution: Introduce Facade Layer

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Components (Frontend)                 │
│  src/uqlab/ui_components/workflow/                          │
│    ├─ step1_dataset.py                                      │
│    ├─ step2_training.py                                     │
│    ├─ step3_uncertainty.py                                  │
│    ├─ step4_evaluation.py                                   │
│    └─ step5_review.py                                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ imports ONLY from
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      Facade Layer (API)                      │
│  src/uqlab_orchestrator/                                     │
│    ├─ dataset_facade.py      ← Wraps uqlab.data             │
│    ├─ model_facade.py         ← Wraps uqlab.models          │
│    ├─ evaluation_facade.py    ← Wraps uqlab.evaluation      │
│    ├─ config_facade.py        ← Wraps uqlab.shared.config   │
│    └─ experiment_facade.py    ← Wraps uqlab.runner          │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ imports from
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Core Library (Backend)                    │
│  src/uqlab/                                                  │
│    ├─ data/                                                  │
│    ├─ evaluation/                                            │
│    ├─ models/                                                │
│    ├─ runner/                                                │
│    └─ shared/config/                                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **UI components NEVER import from `uqlab.*` directly**
2. **UI components ONLY import from `uqlab_orchestrator.*`**
3. **Facade layer provides stable API for UI**
4. **Core library can change without breaking UI**

---

## Implementation Plan

### Phase 1: Create Facade Modules (2-3 hours)

#### 1.1 Dataset Facade
```python
# src/uqlab_orchestrator/dataset_facade.py
"""
Facade for dataset operations.
Provides stable API for UI components.
"""
from typing import Dict, Any
from uqlab.data.dataset_registry import get_dataset_spec as _get_dataset_spec

def get_dataset_info(dataset_name: str) -> Dict[str, Any]:
    """
    Get dataset information for UI display.
    
    Args:
        dataset_name: Name of dataset (e.g., "cifar10n")
    
    Returns:
        Dictionary with dataset metadata
    """
    spec = _get_dataset_spec(dataset_name)
    return {
        "name": spec.name,
        "num_classes": spec.num_classes,
        "class_names": spec.class_names,
        "description": spec.description,
    }

def list_available_datasets() -> list[str]:
    """Get list of available dataset names."""
    from uqlab.data.dataset_registry import DATASET_REGISTRY
    return list(DATASET_REGISTRY.keys())
```

#### 1.2 Evaluation Facade
```python
# src/uqlab_orchestrator/evaluation_facade.py
"""
Facade for evaluation operations.
"""
from typing import List, Dict
from uqlab.evaluation.signals.registry import (
    normalize_signal_id as _normalize_signal_id,
    step4_signal_groups as _step4_signal_groups,
)

def get_available_signals() -> Dict[str, List[str]]:
    """
    Get available uncertainty signals grouped by category.
    
    Returns:
        Dictionary mapping category names to signal IDs
    """
    return _step4_signal_groups()

def normalize_signal_name(signal_id: str) -> str:
    """Normalize signal ID for display."""
    return _normalize_signal_id(signal_id)
```

#### 1.3 Config Facade
```python
# src/uqlab_orchestrator/config_facade.py
"""
Facade for configuration operations.
"""
from typing import Dict, Any
from uqlab.shared.config.classification import PerClassConfig as _PerClassConfig

class PerClassConfigFacade:
    """
    Facade for per-class configuration.
    Provides UI-friendly interface.
    """
    
    @staticmethod
    def create_default() -> Dict[int, Dict[str, Any]]:
        """Create default per-class configuration."""
        return {
            cls: {
                "train_samples": 300,
                "label_noise_pct": 0.0,
                "sweep_epistemic": False,
                "sweep_aleatoric": False,
            }
            for cls in range(10)
        }
    
    @staticmethod
    def to_internal_format(ui_config: Dict[int, Dict[str, Any]]) -> Dict[int, _PerClassConfig]:
        """Convert UI config to internal format."""
        return {
            cls: _PerClassConfig(**cfg)
            for cls, cfg in ui_config.items()
        }
```

### Phase 2: Update UI Components (1-2 hours)

#### Before (Bad):
```python
# ui_components/workflow/step1_dataset.py
from uqlab.data.dataset_registry import get_dataset_spec  # ❌ Direct import

def render_step1_dataset():
    spec = get_dataset_spec("cifar10n")
    st.write(f"Classes: {spec.num_classes}")
```

#### After (Good):
```python
# ui_components/workflow/step1_dataset.py
from uqlab_orchestrator.dataset_facade import get_dataset_info  # ✅ Facade import

def render_step1_dataset():
    info = get_dataset_info("cifar10n")
    st.write(f"Classes: {info['num_classes']}")
```

### Phase 3: Update Imports Systematically

```bash
# Find all problematic imports
grep -r "from uqlab\." src/uqlab/ui_components/workflow/

# Replace with facade imports
# Example:
# from uqlab.data.dataset_registry import get_dataset_spec
# →
# from uqlab_orchestrator.dataset_facade import get_dataset_info
```

---

## Benefits of Facade Approach

### 1. **Decoupling**
```python
# UI doesn't know about internal implementation
from uqlab_orchestrator.dataset_facade import get_dataset_info

# Core library can change without breaking UI
# Old: get_dataset_spec() returns DatasetSpec object
# New: get_dataset_spec() returns different object
# Facade handles conversion → UI unaffected
```

### 2. **Testability**
```python
# Mock facade in tests
from unittest.mock import patch

@patch('uqlab_orchestrator.dataset_facade.get_dataset_info')
def test_step1_dataset(mock_get_info):
    mock_get_info.return_value = {"name": "test", "num_classes": 10}
    # Test UI component without core library
```

### 3. **API Stability**
```python
# Facade provides stable API contract
# Even if core library changes, facade maintains compatibility
def get_dataset_info(dataset_name: str) -> Dict[str, Any]:
    """This signature never changes."""
    # Internal implementation can evolve
```

### 4. **Clear Boundaries**
```
UI Components:
  - Only import from uqlab_orchestrator.*
  - Focus on presentation logic
  - No knowledge of core internals

Facade Layer:
  - Provides stable API
  - Handles data transformation
  - Manages core library complexity

Core Library:
  - Implements business logic
  - No knowledge of UI
  - Can evolve independently
```

---

## Migration Strategy

### Step 1: Audit Current Imports (30 min)
```bash
# Create import inventory
grep -r "from uqlab\." src/uqlab/ui_components/workflow/ > imports_audit.txt

# Categorize by module:
# - uqlab.data.*
# - uqlab.evaluation.*
# - uqlab.models.*
# - uqlab.shared.config.*
```

### Step 2: Create Facades (2-3 hours)
- One facade per core module category
- Focus on UI-needed functionality only
- Keep facades thin (delegation, not duplication)

### Step 3: Update UI Components (1-2 hours)
- Replace direct imports with facade imports
- Update function calls to use facade API
- Test each component after migration

### Step 4: Add Tests (1 hour)
- Test facades independently
- Test UI components with mocked facades
- Verify no direct `uqlab.*` imports remain

### Step 5: Documentation (30 min)
- Document facade API
- Update architecture diagrams
- Create migration guide for future developers

---

## Verification Checklist

After migration, verify:

- [ ] No `from uqlab.*` imports in `ui_components/workflow/`
- [ ] All UI components import from `uqlab_orchestrator.*` only
- [ ] Facades provide complete API for UI needs
- [ ] Tests pass with mocked facades
- [ ] Core library can change without breaking UI
- [ ] Architecture diagram updated
- [ ] Documentation complete

---

## Example: Complete Migration

### Before (Problematic)
```python
# ui_components/workflow/step4_evaluation.py
from uqlab.evaluation.signals.registry import normalize_signal_id, step4_signal_groups
from uqlab.shared.config.signals import DEFAULT_SELECTED_SIGNALS

def render_step4_evaluation():
    groups = step4_signal_groups()
    for group_name, signals in groups.items():
        st.write(f"**{group_name}**")
        for sig in signals:
            normalized = normalize_signal_id(sig)
            st.checkbox(normalized, value=(sig in DEFAULT_SELECTED_SIGNALS))
```

### After (Clean)
```python
# ui_components/workflow/step4_evaluation.py
from uqlab_orchestrator.evaluation_facade import (
    get_available_signals,
    normalize_signal_name,
    get_default_signals,
)

def render_step4_evaluation():
    groups = get_available_signals()
    defaults = get_default_signals()
    
    for group_name, signals in groups.items():
        st.write(f"**{group_name}**")
        for sig in signals:
            normalized = normalize_signal_name(sig)
            st.checkbox(normalized, value=(sig in defaults))
```

### Facade Implementation
```python
# uqlab_orchestrator/evaluation_facade.py
from typing import Dict, List
from uqlab.evaluation.signals.registry import (
    normalize_signal_id as _normalize,
    step4_signal_groups as _groups,
)
from uqlab.shared.config.signals import DEFAULT_SELECTED_SIGNALS as _defaults

def get_available_signals() -> Dict[str, List[str]]:
    """Get available signals grouped by category."""
    return _groups()

def normalize_signal_name(signal_id: str) -> str:
    """Normalize signal ID for display."""
    return _normalize(signal_id)

def get_default_signals() -> List[str]:
    """Get default selected signals."""
    return list(_defaults)
```

---

## Conclusion

**Current State**: UI components and core library both import from `uqlab.*`, creating tight coupling and architectural violations.

**Solution**: Introduce facade layer (`uqlab_orchestrator.*`) that provides stable API for UI components.

**Benefits**:
- Decoupling: UI and core can evolve independently
- Testability: Mock facades in tests
- Stability: Facade API remains constant
- Clarity: Clear architectural boundaries

**Effort**: ~5-7 hours total
- 2-3 hours: Create facades
- 1-2 hours: Update UI components
- 1 hour: Add tests
- 1 hour: Documentation

**Priority**: High - This is a fundamental architectural issue that will cause problems as the codebase grows.

---

## Related Files

- Current problematic imports: [`ui_components/workflow/`](src/uqlab/ui_components/workflow/)
- Core library modules: [`src/uqlab/`](src/uqlab/)
- Existing facade (partial): [`src/uqlab_orchestrator/`](src/uqlab_orchestrator/)
- Architecture docs: [`DUAL_FACADE_ARCHITECTURE.md`](DUAL_FACADE_ARCHITECTURE.md)