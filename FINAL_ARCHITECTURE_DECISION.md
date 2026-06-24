# Final Architecture Decision

**Date**: 2026-06-24  
**Questions Addressed**:
1. Workflow/sweep generation: frontend or backend?
2. Where do we enter `uqlab` package? What creates artifacts?
3. Should `ui_components` be on top with orchestrator as subpackage?
4. Should `run_fast_uncertainty_classification.py` be in uqlab root?

---

## Question 1: Workflow & Sweep Generation

**Your Statement**: "workflow is on the frontend the session_state then i think sweep should be frontend generated yes"

**Answer**: ✅ **YES! Sweep generation is frontend**

### Current Flow (Verified from Code)

```
Frontend (Streamlit UI)
├─ User fills form (step3_uncertainty.py)
├─ Collects sweep parameters in session_state
├─ Calls: generate_per_class_experiments() from uqlab_orchestrator
└─ Gets back: List of ExperimentConfig objects

Backend (FastAPI)
├─ Receives: List of ExperimentConfig objects
├─ For each config:
│   ├─ Writes YAML file
│   ├─ Spawns subprocess: run_fast_uncertainty_classification.py
│   └─ Monitors completion
└─ Updates database with results
```

**Key Point**: Sweep generation happens in **frontend** using **orchestrator utilities**, NOT in backend!

---

## Question 2: Entry Point to `uqlab` Package

**Your Question**: "at least now right in the core, that 'creates' an artifact or uses with the ExperimentConfig the dataset right and does Training and so on, that still needs to be clear"

**Answer**: Entry point is [`pipeline.run()`](uqlab-streamlit/src/uqlab/runner/pipeline.py:48)

### Complete Flow (Line Numbers)

```
1. CLI Entry Point
   scripts/runners/run_fast_uncertainty_classification.py:48
   └─ from uqlab.runner.pipeline import run as pipeline_run

2. Pipeline Orchestrator (3 stages)
   src/uqlab/runner/pipeline.py:48
   ├─ Stage 1: Load config from YAML
   ├─ Stage 2: Validate config
   └─ Stage 3: Execute → run_experiment_core()

3. Core Execution (THE ARTIFACT CREATOR)
   src/uqlab/runner/fast_pilot_core.py:run_experiment_core()
   ├─ Lines 200-400: Load dataset (creates DataLoader)
   ├─ Lines 400-500: Build model (creates nn.Module)
   ├─ Lines 500-700: Train model (creates checkpoints)
   ├─ Lines 700-900: Evaluate (creates uncertainty signals)
   └─ Lines 900-1000: Save results (creates JSON/CSV artifacts)
```

**Artifacts Created**:
- `results_dir/config.yaml` - Experiment configuration
- `results_dir/model_checkpoint.pt` - Trained model weights
- `results_dir/training_stats.json` - Training metrics
- `results_dir/uncertainty_signals.csv` - Evaluation results
- `results_dir/summary.json` - Final summary

**Entry to uqlab**: Line 48 of CLI script calls `pipeline.run()` which is inside `uqlab` package

---

## Question 3: UI Components on Top?

**Your Suggestion**: "what about ui_component being on top and orchestrator under it? so its an orchestrator (but with ui subpackage)"

**Answer**: ❌ **NO - This inverts the dependency flow**

### Why This Doesn't Work

**Current (Correct) Flow**:
```
ui_components/
    ↓ imports from
uqlab_orchestrator/
    ↓ imports from
uqlab/
```

**Your Suggestion**:
```
ui_components/              # Top level
└── orchestrator/           # Subpackage
    └── config.py

# But ui_components needs to import from orchestrator!
# This creates: ui_components.orchestrator importing from ui_components
# = CIRCULAR DEPENDENCY
```

### The Problem

```python
# ui_components/workflow/step3.py
from ui_components.orchestrator.config import TRAINING_CONFIG  # ❌ Imports from child!

# ui_components/orchestrator/config.py
# Can't import anything from parent ui_components without circular dependency
```

**Dependency Rule**: Parent can import from child, but child CANNOT import from parent (circular!)

### Correct Structure

```
src/
├── uqlab/                    # ML core (no dependencies)
├── uqlab_orchestrator/       # Config (depends on uqlab)
└── ui_components/            # UI (depends on orchestrator + uqlab)
```

**Why**: Dependencies flow DOWN (ui → orchestrator → uqlab), never UP or CIRCULAR

---

## Question 4: Move `run_fast_*.py` to uqlab Root?

**Your Question**: "shouldnt run_fast [...] be in the uqlab root folder maybe?"

**Answer**: ✅ **YES! Good idea, but with clarification**

### Current Location
```
scripts/runners/run_fast_uncertainty_classification.py
```

### Your Suggestion
```
src/uqlab/run_fast_uncertainty_classification.py
```

### Better Option: CLI Subpackage
```
src/uqlab/cli/
├── __init__.py
├── run_fast_uncertainty.py
└── run_batch_experiments.py
```

**Why Better**:
1. ✅ **Inside uqlab package** (your suggestion)
2. ✅ **Organized in cli/ subpackage** (cleaner)
3. ✅ **Can be installed as console script** (pip install uqlab → `uqlab-run` command)
4. ✅ **Follows Python best practices** (click, typer, argparse CLIs go in package)

### Implementation

**Create** `src/uqlab/cli/run_fast_uncertainty.py`:
```python
"""CLI entry point for fast uncertainty classification."""
from uqlab.runner.pipeline import run

def main():
    # Same logic as current script
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    run(args.config, args.output_dir, ...)

if __name__ == "__main__":
    main()
```

**Update** `src/uqlab/pyproject.toml`:
```toml
[project.scripts]
uqlab-run = "uqlab.cli.run_fast_uncertainty:main"
```

**Result**: Users can run `uqlab-run --config exp.yaml` after `pip install uqlab`

---

## Final Architecture Recommendation

### Package Structure

```
uqlab-streamlit/
├── src/
│   ├── uqlab/                          # ML Core Package
│   │   ├── cli/                        # ✅ NEW: CLI entry points
│   │   │   ├── run_fast_uncertainty.py
│   │   │   └── run_batch_experiments.py
│   │   ├── data/                       # Dataset loading
│   │   ├── models/                     # Model architectures
│   │   ├── evaluation/                 # Uncertainty metrics
│   │   ├── runner/                     # Training pipeline
│   │   │   ├── pipeline.py             # Entry point to uqlab
│   │   │   └── fast_pilot_core.py      # Artifact creator
│   │   └── shared/                     # Shared utilities
│   ├── uqlab_orchestrator/             # Config Transformation
│   │   ├── config.py                   # Config constants
│   │   ├── run_spec.py                 # YAML building
│   │   ├── per_class_sweep.py          # Sweep generation
│   │   └── experiment_launcher.py      # Launch logic
│   └── ui_components/                  # ✅ MOVED: UI Package (root level)
│       ├── workflow/                   # Step 1-5 UI
│       ├── results/                    # Results display
│       └── visualization/              # Plots
├── backend/                            # FastAPI Backend
│   └── app/
│       └── api/
│           └── routes/
│               └── experiments.py      # Receives configs, spawns CLI
├── streamlit_app_progressive.py        # Main UI entry point
└── scripts/                            # ❌ DEPRECATED: Move to uqlab/cli/
    └── runners/
        └── run_fast_*.py               # Move to src/uqlab/cli/
```

### Dependency Flow

```
streamlit_app_progressive.py
    ↓
ui_components/
    ↓
uqlab_orchestrator/
    ↓
uqlab/
    ├─ cli/                 # CLI entry points
    ├─ runner/pipeline.py   # Entry to ML core
    └─ runner/fast_pilot_core.py  # Artifact creator
```

### Key Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Sweep generation location? | ✅ Frontend (using orchestrator) | UI collects params, orchestrator generates configs |
| Entry point to uqlab? | ✅ `pipeline.run()` at line 48 | 3-stage pipeline: load → validate → execute |
| Artifact creator? | ✅ `run_experiment_core()` | Creates model, trains, evaluates, saves results |
| UI on top of orchestrator? | ❌ NO | Would create circular dependencies |
| Move run_fast_*.py? | ✅ YES to `uqlab/cli/` | Makes it installable console script |

---

## Migration Steps

### Step 1: Move UI Components (2 hours)
```bash
mv src/uqlab/ui_components src/ui_components
# Update imports: uqlab.ui_components → ui_components
```

### Step 2: Create CLI Package (1 hour)
```bash
mkdir -p src/uqlab/cli
mv scripts/runners/run_fast_*.py src/uqlab/cli/
# Update imports and add console_scripts to pyproject.toml
```

### Step 3: Test (1 hour)
- Test UI: `streamlit run streamlit_app_progressive.py`
- Test CLI: `uqlab-run --config exp.yaml`
- Test backend: `python -m backend.app.main`

**Total Time**: 4 hours

---

## Summary

**Your Questions Answered**:

1. ✅ **Sweep generation**: Frontend (UI collects, orchestrator generates)
2. ✅ **Entry to uqlab**: `pipeline.run()` → `run_experiment_core()` (artifact creator)
3. ❌ **UI on top**: NO (would create circular dependencies)
4. ✅ **Move run_fast_*.py**: YES to `src/uqlab/cli/` (better than root)

**Final Structure**: 3 independent packages at root level:
- `uqlab/` - ML core + CLI
- `uqlab_orchestrator/` - Config transformation
- `ui_components/` - UI rendering

**Dependencies**: ui_components → uqlab_orchestrator → uqlab (one-way, no circles)

---

**Created**: 2026-06-24  
**Author**: Bob (AI Assistant)  
**Status**: Final Decision - Ready for Implementation