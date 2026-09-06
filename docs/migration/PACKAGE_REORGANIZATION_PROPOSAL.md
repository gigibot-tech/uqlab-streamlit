# Package Reorganization Proposal

**Date**: 2026-06-24  
**Purpose**: Fix illogical package structure where UI components are inside ML core

---

## Problem Statement

You're absolutely right - **`ui_components` being inside `src/uqlab/` is stupid!**

### Current Structure (WRONG)
```
src/
├── uqlab/                    # ML Core package
│   ├── ui_components/        # ❌ UI code inside ML package!
│   ├── data/                 # ✅ ML: Dataset loading
│   ├── models/               # ✅ ML: Model architectures
│   ├── evaluation/           # ✅ ML: Uncertainty metrics
│   └── runner/               # ✅ ML: Training pipeline
└── uqlab_orchestrator/       # Config transformation
```

**Why This Is Wrong**:
1. `uqlab` is an ML library - it should have ZERO UI dependencies
2. `ui_components` depends on Streamlit - pollutes ML package
3. Can't use `uqlab` without Streamlit installed
4. Violates separation of concerns

---

## Proposed Solution

### Option A: Move to Root Level (RECOMMENDED)

```
src/
├── uqlab/                    # ✅ Pure ML (no UI)
│   ├── data/
│   ├── models/
│   ├── evaluation/
│   ├── runner/
│   └── shared/
├── uqlab_orchestrator/       # ✅ Config transformation (no UI)
│   ├── experiment_launcher.py
│   ├── run_spec.py
│   └── sweep_generator.py
└── streamlit_ui/             # ✅ NEW: All UI code here
    ├── components/           # Reusable widgets
    │   ├── workflow/         # Step 1-5 UI
    │   ├── results/          # Results display
    │   └── visualization/    # Plots
    └── pages/                # Streamlit pages
        ├── progressive_app.py
        └── main_app.py
```

**Benefits**:
- `uqlab` is pure ML (can be used in notebooks, CLI, other UIs)
- `streamlit_ui` is clearly UI-only
- Clean separation of concerns
- Each package has single responsibility

### Option B: UI as Subpackage of Orchestrator (YOUR SUGGESTION)

```
src/
├── uqlab/                    # ✅ Pure ML
│   ├── data/
│   ├── models/
│   ├── evaluation/
│   └── runner/
└── uqlab_orchestrator/       # Config + UI
    ├── config/               # Config transformation
    │   ├── experiment_launcher.py
    │   ├── run_spec.py
    │   └── sweep_generator.py
    └── ui/                   # UI components
        ├── components/
        │   ├── workflow/
        │   ├── results/
        │   └── visualization/
        └── pages/
```

**Benefits**:
- Orchestrator + UI are related (both deal with experiment configuration)
- Single package for "experiment management"
- Modular UI is subpackage

**Drawbacks**:
- Orchestrator becomes large (config + UI)
- Still mixes concerns (config transformation + UI rendering)

---

## Detailed Analysis

### What Does `ui_components` Actually Do?

Let me check what logic it has:

**Current `src/uqlab/ui_components/` structure**:
```
ui_components/
├── workflow/                 # Step 1-5 configuration UI
│   ├── step1_dataset.py      # Dataset selection widgets
│   ├── step2_model.py        # Model configuration widgets
│   ├── step3_uncertainty.py  # Uncertainty config widgets
│   ├── step4_evaluation.py   # Evaluation config widgets
│   └── step5_review.py       # Review & launch widgets
├── results/                  # Results display
│   ├── experiment_results_panel.py
│   └── metrics_display.py
├── visualization/            # Plots & charts
│   ├── signals/              # Signal plots
│   └── validation/           # Validation plots
└── config/                   # Config builders
    └── experiment_config.py  # Builds ExperimentConfig from UI
```

**What it uses**:
- **Streamlit** (st.text_input, st.selectbox, etc.) - UI rendering
- **uqlab.shared.config** - Config dataclasses
- **uqlab_orchestrator** - Config transformation
- **Plotly/Matplotlib** - Visualization

**What logic it has**:
- ❌ **NO ML logic** - Just UI rendering
- ✅ **Config building** - Transforms UI inputs → workflow dict
- ✅ **Validation** - Checks user inputs
- ✅ **Visualization** - Renders plots

---

## Recommendation: Option A (Root Level)

### Why Option A is Better

**Separation of Concerns**:
```
uqlab/              → Pure ML (data, models, training, evaluation)
uqlab_orchestrator/ → Config transformation (workflow → ExperimentConfig)
streamlit_ui/       → UI rendering (Streamlit widgets, plots)
```

**Dependencies**:
```
streamlit_ui → uqlab_orchestrator → uqlab
     ↓              ↓                ↓
  Streamlit    Pure Python      PyTorch/NumPy
```

**Use Cases**:
1. **ML Research**: Use `uqlab` directly (no UI)
2. **CLI Tools**: Use `uqlab` + `uqlab_orchestrator` (no UI)
3. **Web UI**: Use all three packages

### Why NOT Option B

**Problem**: Orchestrator becomes bloated
```
uqlab_orchestrator/
├── config/          # Config transformation (pure Python)
└── ui/              # UI rendering (Streamlit)
```

**Issues**:
- Mixes config transformation (pure Python) with UI rendering (Streamlit)
- Can't use orchestrator without Streamlit
- Violates single responsibility principle

---

## Migration Plan

### Phase 1: Create New Structure (1 hour)

```bash
# Create new streamlit_ui package
mkdir -p src/streamlit_ui/{components,pages}

# Move ui_components
mv src/uqlab/ui_components/* src/streamlit_ui/components/

# Update imports
find src/streamlit_ui -type f -name "*.py" -exec sed -i '' 's/from uqlab.ui_components/from streamlit_ui.components/g' {} \;
```

### Phase 2: Update Imports (30 minutes)

**Files to update**:
1. `streamlit_app_progressive.py` - Main app
2. `streamlit_app.py` - Legacy app
3. Any scripts that import ui_components

**Change**:
```python
# OLD
from uqlab.ui_components.workflow import step3_uncertainty

# NEW
from streamlit_ui.components.workflow import step3_uncertainty
```

### Phase 3: Update Package Metadata (15 minutes)

**Create** `src/streamlit_ui/pyproject.toml`:
```toml
[project]
name = "uqlab-streamlit-ui"
version = "0.1.0"
dependencies = [
    "streamlit>=1.28.0",
    "plotly>=5.17.0",
    "uqlab>=0.1.0",
    "uqlab-orchestrator>=0.1.0",
]
```

### Phase 4: Test (30 minutes)

1. Run `streamlit_app_progressive.py`
2. Verify all imports work
3. Test experiment launch
4. Verify results display

---

## Final Structure

```
uqlab-streamlit/
├── src/
│   ├── uqlab/                    # ✅ Pure ML package
│   │   ├── data/                 # Dataset loading
│   │   ├── models/               # Model architectures
│   │   ├── evaluation/           # Uncertainty metrics
│   │   ├── runner/               # Training pipeline
│   │   └── shared/               # Shared utilities
│   ├── uqlab_orchestrator/       # ✅ Config transformation
│   │   ├── experiment_launcher.py
│   │   ├── run_spec.py
│   │   └── sweep_generator.py
│   └── streamlit_ui/             # ✅ NEW: UI package
│       ├── components/           # Reusable widgets
│       │   ├── workflow/         # Step 1-5 UI
│       │   ├── results/          # Results display
│       │   └── visualization/    # Plots
│       └── pages/                # Streamlit pages
├── streamlit_app_progressive.py  # Main app (imports streamlit_ui)
├── backend/                      # FastAPI backend
└── scripts/                      # CLI tools
```

---

## Summary

### Your Question: "Why not UI as subpackage of orchestrator?"

**Answer**: Because it mixes concerns:
- **Orchestrator** = Config transformation (pure Python, no UI)
- **UI** = Rendering widgets (Streamlit-dependent)

**Better**: Keep them separate at root level:
- `uqlab/` = ML core (pure ML, no UI, no config transformation)
- `uqlab_orchestrator/` = Config transformation (pure Python, no UI)
- `streamlit_ui/` = UI rendering (Streamlit, uses orchestrator)

### Your Observation: "ui_components being part of uqlab seems stupid"

**Answer**: ✅ **100% CORRECT!**

**Fix**: Move `src/uqlab/ui_components/` → `src/streamlit_ui/components/`

**Result**:
- `uqlab` becomes pure ML library
- `streamlit_ui` becomes pure UI package
- Clean separation of concerns

---

## Next Steps

1. **Review this proposal**
2. **Decide**: Option A (root level) or Option B (orchestrator subpackage)
3. **Execute migration** (2 hours total)
4. **Test thoroughly**
5. **Update documentation**

---

**Created**: 2026-06-24  
**Author**: Bob (AI Assistant)  
**Status**: Proposal - Awaiting Decision