# Dependency Analysis & Final Recommendation

**Date**: 2026-06-24  
**Question**: "Shouldn't ui_components use the config stuff though?"

---

## YES! You're Absolutely Right

### Current Dependencies (Verified from Code)

**`ui_components` HEAVILY uses `uqlab_orchestrator`**:

```python
# From ui_components/workflow/step3_uncertainty.py
from uqlab_orchestrator.config import (
    CIFAR10N_NOISE_LABELS,
    FIXED_REGULAR_TRAIN_PER_CLASS,
    LABEL_NOISE_SWEEP,
    TRAINING_CONFIG,
    aligned_under_train_sweep,
    get_sweep_target,
    launch_mirror_preview,
)
from uqlab_orchestrator.uncertainty import step3_sweep_options
from uqlab_orchestrator.uncertainty.registry import SINGLE_SWEEP_TARGET, SWEEP_BOTH_TARGET
from uqlab_orchestrator.run_spec import filter_under_train_values, is_clean_noise
from uqlab_orchestrator.per_class_sweep import generate_per_class_experiments, get_sweep_summary
```

**Dependency Flow**:
```
streamlit_ui → uqlab_orchestrator → uqlab
     ↓              ↓                ↓
  Streamlit    Pure Python      PyTorch/NumPy
```

---

## Why This STILL Supports Option A (Root Level)

### The Key Insight

**Dependencies flow ONE WAY**:
```
UI → Orchestrator → ML Core
```

**NOT**:
```
UI ← Orchestrator (circular!)
```

### If UI Becomes Subpackage of Orchestrator

**Problem**: Creates confusing structure where:
```
uqlab_orchestrator/
├── config.py           # Config constants
├── run_spec.py         # YAML building
├── per_class_sweep.py  # Sweep generation
└── ui/                 # UI components
    └── workflow/
        └── step3.py    # Imports from ../config, ../run_spec, ../per_class_sweep
```

**Issues**:
1. **Relative imports everywhere**: `from ..config import X` instead of `from uqlab_orchestrator.config import X`
2. **Package bloat**: Orchestrator becomes 2 things (config + UI)
3. **Dependency confusion**: Is orchestrator a library or an app?
4. **Can't install orchestrator alone**: Pulls in Streamlit even if you just want config logic

---

## Correct Understanding of Dependencies

### What Each Package Does

| Package | Purpose | Dependencies | Used By |
|---------|---------|--------------|---------|
| `uqlab/` | ML core (data, models, training, eval) | PyTorch, NumPy | orchestrator, UI |
| `uqlab_orchestrator/` | Config transformation (workflow → ExperimentConfig) | uqlab | UI |
| `streamlit_ui/` | UI rendering (widgets, plots) | Streamlit, orchestrator, uqlab | streamlit_app.py |

### Dependency Graph

```
streamlit_app.py
    ↓
streamlit_ui/
    ↓
uqlab_orchestrator/
    ↓
uqlab/
    ↓
PyTorch, NumPy
```

**Key Point**: Dependencies flow DOWN, never UP or CIRCULAR

---

## Why Option A is STILL Better

### Option A: Root Level (RECOMMENDED)

```
src/
├── uqlab/                    # Pure ML
├── uqlab_orchestrator/       # Config transformation
└── streamlit_ui/             # UI rendering
```

**Benefits**:
1. ✅ **Clear dependency flow**: UI → orchestrator → ML
2. ✅ **Each package independent**: Can install orchestrator without Streamlit
3. ✅ **Single responsibility**: Each package does ONE thing
4. ✅ **Absolute imports**: `from uqlab_orchestrator.config import X` (clear)
5. ✅ **Flexible**: Can create other UIs (Flask, FastAPI, CLI) that use orchestrator

### Option B: UI as Subpackage

```
src/
├── uqlab/                    # Pure ML
└── uqlab_orchestrator/       # Config + UI
    ├── config/
    ├── run_spec.py
    └── ui/                   # UI components
```

**Problems**:
1. ❌ **Relative imports**: `from ..config import X` (confusing)
2. ❌ **Package bloat**: Orchestrator does 2 things (config + UI)
3. ❌ **Dependency pollution**: Can't install orchestrator without Streamlit
4. ❌ **Inflexible**: Hard to create other UIs (Flask, CLI) without pulling in Streamlit

---

## Real-World Analogy

### Option A (Recommended)
```
kitchen/          # Core cooking logic
recipes/          # Recipe transformation (ingredients → instructions)
restaurant_ui/    # Customer-facing UI (menus, ordering)
```

**Dependencies**: `restaurant_ui` uses `recipes` uses `kitchen`

**Benefits**:
- Can use `recipes` in a food truck (different UI)
- Can use `recipes` in a cookbook (no UI)
- Can use `kitchen` in a catering service (no recipes, no UI)

### Option B (Your Suggestion)
```
kitchen/          # Core cooking logic
recipes/          # Recipe transformation + restaurant UI
    ├── ingredients/
    ├── instructions/
    └── ui/       # Customer-facing UI
```

**Problems**:
- Can't use `recipes` without restaurant UI
- Food truck needs to install restaurant UI (unnecessary)
- Cookbook needs to install restaurant UI (unnecessary)

---

## Answer to Your Question

**Q**: "Shouldn't ui_components use the config stuff though?"

**A**: YES! And it DOES use it heavily. But that's exactly WHY it should be separate:

### Current Reality
```python
# ui_components imports FROM orchestrator (correct!)
from uqlab_orchestrator.config import TRAINING_CONFIG
from uqlab_orchestrator.run_spec import filter_under_train_values
```

### If UI becomes subpackage
```python
# ui_components imports FROM parent package (confusing!)
from ..config import TRAINING_CONFIG
from ..run_spec import filter_under_train_values
```

**Key Insight**: Just because A uses B doesn't mean A should be INSIDE B!

---

## Final Recommendation

### Keep Option A: Root Level

**Structure**:
```
src/
├── uqlab/                    # ML core
├── uqlab_orchestrator/       # Config transformation
└── streamlit_ui/             # UI rendering
```

**Why**:
1. ✅ UI uses orchestrator (correct dependency flow)
2. ✅ Orchestrator stays pure Python (no Streamlit)
3. ✅ Each package has single responsibility
4. ✅ Can create other UIs (Flask, CLI) easily
5. ✅ Clear, absolute imports

**Migration**: 2 hours (as detailed in PACKAGE_REORGANIZATION_PROPOSAL.md)

---

## Summary

Your question revealed the KEY insight:

**"UI uses config" is TRUE**  
**"Therefore UI should be inside config package" is FALSE**

**Correct**: UI depends on config → UI imports from config  
**Incorrect**: UI depends on config → UI lives inside config

**Analogy**: Your car uses gasoline, but your car isn't stored inside the gas tank!

---

**Created**: 2026-06-24  
**Author**: Bob (AI Assistant)  
**Status**: Final Recommendation - Ready for Implementation