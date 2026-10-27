# Architecture Improvement Proposal

**Date**: 2026-06-24  
**Question**: "cant it be more readable? and is this even architecture wise the best way?"

---

## Current Architecture Issues

### Problem 1: Confusing Naming

**Current**:
```
scripts/runners/run_fast_uncertainty_classification.py  # CLI wrapper
src/uqlab/runner/pipeline.py                            # Execution engine
```

**Issues**:
- ❌ "runners" (plural) vs "runner" (singular) - confusing
- ❌ "run_fast_uncertainty_classification" - too verbose
- ❌ CLI script outside package - not installable
- ❌ No clear distinction between wrapper and engine

### Problem 2: Unnecessary Indirection

**Current Flow** (3 layers):
```
CLI Script (scripts/runners/)
    ↓ imports
Pipeline (uqlab/runner/pipeline.py)
    ↓ calls
Core (uqlab/runner/fast_pilot_core.py)
```

**Question**: Do we need 3 layers? Can we simplify?

### Problem 3: Monolithic Core

**Current**: `fast_pilot_core.py` is 1000+ lines doing everything
- Data loading
- Model building
- Training
- Evaluation
- Results saving

**Question**: Should this be split using the facade pattern we already created?

---

## Proposed Architecture (Better)

### Option A: Simplified 2-Layer Architecture

**Structure**:
```
src/uqlab/
├── cli/
│   └── run.py                    # CLI entry point (thin wrapper)
└── execution/
    ├── __init__.py
    ├── experiment.py             # Main execution (uses facade)
    └── facade/                   # Facade pattern (already exists!)
        ├── data_coordinator.py
        ├── model_coordinator.py
        ├── training_coordinator.py
        ├── evaluation_coordinator.py
        └── experiment_facade.py
```

**Flow** (2 layers):
```
CLI (uqlab/cli/run.py)
    ↓ calls
Experiment (uqlab/execution/experiment.py)
    ↓ uses
Facade (uqlab/execution/facade/)
```

**Benefits**:
- ✅ Clear naming: `cli/` = entry point, `execution/` = engine
- ✅ Simpler: 2 layers instead of 3
- ✅ Uses existing facade pattern
- ✅ Installable: `pip install uqlab` → `uqlab run exp.yaml`

### Option B: Keep 3 Layers But Rename

**Structure**:
```
src/uqlab/
├── cli/
│   └── run.py                    # CLI entry point
├── orchestration/
│   └── pipeline.py               # 3-stage orchestrator
└── execution/
    └── experiment.py             # Main execution
```

**Flow** (3 layers):
```
CLI (uqlab/cli/run.py)
    ↓ calls
Orchestrator (uqlab/orchestration/pipeline.py)
    ↓ calls
Execution (uqlab/execution/experiment.py)
```

**Benefits**:
- ✅ Clear naming: cli → orchestration → execution
- ✅ Keeps 3-stage pattern
- ✅ Each layer has clear responsibility

**Drawbacks**:
- ⚠️ Still 3 layers (more complex)
- ⚠️ Doesn't use facade pattern

---

## Detailed Comparison

### Current Architecture

```python
# scripts/runners/run_fast_uncertainty_classification.py (60 lines)
def main():
    args = parse_args()
    config = ExperimentConfig.from_yaml(args.config)
    
    from uqlab.runner.pipeline import run
    run(config_path, output_dir, seed=args.seed)

# src/uqlab/runner/pipeline.py (200 lines)
def run(config_path, output_dir, ...):
    ctx = RunContext()
    ctx = _stage_load_config(ctx)      # Stage 1
    ctx = _stage_validate_config(ctx)  # Stage 2
    ctx = _stage_execute(ctx)          # Stage 3 → calls run_experiment_core()
    return ctx.get("summary")

# src/uqlab/runner/fast_pilot_core.py (1000+ lines)
def run_experiment_core(config, results_dir, ...):
    # Load data (200 lines)
    # Build model (100 lines)
    # Train model (200 lines)
    # Evaluate model (200 lines)
    # Save results (100 lines)
```

**Issues**:
- ❌ 3 layers of indirection
- ❌ Monolithic core (1000+ lines)
- ❌ Doesn't use facade pattern (already created!)
- ❌ Confusing names

### Proposed Architecture (Option A)

```python
# src/uqlab/cli/run.py (40 lines)
def main():
    """CLI entry point - parse args and run experiment."""
    args = parse_args()
    config = ExperimentConfig.from_yaml(args.config)
    
    from uqlab.execution import run_experiment
    run_experiment(config, output_dir=args.output_dir, seed=args.seed)

# src/uqlab/execution/experiment.py (150 lines)
def run_experiment(config, output_dir, seed=None, device=None):
    """
    Run complete experiment using facade pattern.
    
    This replaces both pipeline.py and fast_pilot_core.py
    by using the coordinators we already created!
    """
    from uqlab.execution.facade import ExperimentFacade
    
    # Create facade
    facade = ExperimentFacade(config, output_dir, seed, device)
    
    # Execute (facade handles all coordination)
    summary = facade.run()
    
    return summary

# src/uqlab/execution/facade/experiment_facade.py (400 lines - already exists!)
class ExperimentFacade:
    def run(self):
        # Stage 1: Data
        self.data_coordinator.load_data()
        
        # Stage 2: Model
        self.model_coordinator.build_model()
        
        # Stage 3: Training
        self.training_coordinator.train()
        
        # Stage 4: Evaluation
        self.evaluation_coordinator.evaluate()
        
        # Stage 5: Results
        return self.result_coordinator.save_results()
```

**Benefits**:
- ✅ 2 layers instead of 3
- ✅ Uses facade pattern (already created!)
- ✅ Clear separation: CLI → Execution → Coordinators
- ✅ Each coordinator is focused (200-300 lines)
- ✅ Easy to test each coordinator independently

---

## Readability Comparison

### Current (Confusing)

```
User runs: python scripts/runners/run_fast_uncertainty_classification.py --config exp.yaml

Question: What does this do?
Answer: Unclear - "runners" sounds like multiple things, "run_fast_uncertainty_classification" is verbose

Flow:
scripts/runners/run_fast_*.py → uqlab/runner/pipeline.py → uqlab/runner/fast_pilot_core.py
     (wrapper)                      (orchestrator)              (monolithic core)
```

### Proposed (Clear)

```
User runs: uqlab run exp.yaml

Question: What does this do?
Answer: Clear - runs an experiment with config exp.yaml

Flow:
uqlab/cli/run.py → uqlab/execution/experiment.py → uqlab/execution/facade/
   (CLI entry)         (experiment runner)            (coordinators)
```

---

## Migration Plan

### Phase 1: Create New Structure (2 hours)

```bash
# Create new directories
mkdir -p src/uqlab/cli
mkdir -p src/uqlab/execution

# Move and simplify CLI
mv scripts/runners/run_fast_uncertainty_classification.py src/uqlab/cli/run.py
# Simplify to 40 lines (remove unnecessary code)

# Create new experiment.py (uses facade)
# This replaces both pipeline.py and fast_pilot_core.py
cat > src/uqlab/execution/experiment.py << 'EOF'
def run_experiment(config, output_dir, seed=None, device=None):
    from uqlab.execution.facade import ExperimentFacade
    facade = ExperimentFacade(config, output_dir, seed, device)
    return facade.run()
EOF

# Move facade to execution
mv src/uqlab/facade src/uqlab/execution/facade
```

### Phase 2: Update Imports (1 hour)

```python
# OLD
from uqlab.runner.pipeline import run
run(config_path, output_dir)

# NEW
from uqlab.execution import run_experiment
config = ExperimentConfig.from_yaml(config_path)
run_experiment(config, output_dir)
```

### Phase 3: Make CLI Installable (30 minutes)

```toml
# src/uqlab/pyproject.toml
[project.scripts]
uqlab = "uqlab.cli.run:main"
```

**Result**: `pip install uqlab` → `uqlab run exp.yaml`

### Phase 4: Deprecate Old Structure (30 minutes)

```python
# src/uqlab/runner/pipeline.py
import warnings

def run(*args, **kwargs):
    warnings.warn(
        "uqlab.runner.pipeline.run is deprecated. "
        "Use uqlab.execution.run_experiment instead.",
        DeprecationWarning
    )
    from uqlab.execution import run_experiment
    return run_experiment(*args, **kwargs)
```

---

## Final Structure (Proposed)

```
uqlab-streamlit/
├── src/
│   ├── uqlab/                          # ML Core Package
│   │   ├── cli/                        # ✅ NEW: CLI entry points
│   │   │   ├── __init__.py
│   │   │   └── run.py                  # Main CLI (40 lines)
│   │   ├── execution/                  # ✅ RENAMED: Execution engine
│   │   │   ├── __init__.py
│   │   │   ├── experiment.py           # ✅ NEW: Main runner (150 lines)
│   │   │   └── facade/                 # ✅ MOVED: Facade pattern
│   │   │       ├── __init__.py
│   │   │       ├── experiment_facade.py
│   │   │       ├── data_coordinator.py
│   │   │       ├── model_coordinator.py
│   │   │       ├── training_coordinator.py
│   │   │       ├── evaluation_coordinator.py
│   │   │       └── result_coordinator.py
│   │   ├── data/                       # Dataset loading
│   │   ├── models/                     # Model architectures
│   │   ├── evaluation/                 # Uncertainty metrics
│   │   └── shared/                     # Shared utilities
│   ├── uqlab_orchestrator/             # Config transformation
│   └── ui_components/                  # UI rendering
├── backend/                            # FastAPI backend
└── streamlit_app_progressive.py        # Main UI
```

**Deprecated** (keep for backward compatibility):
```
src/uqlab/runner/                       # ⚠️ DEPRECATED
├── pipeline.py                         # → uqlab.execution.run_experiment
└── fast_pilot_core.py                  # → uqlab.execution.facade
```

---

## Benefits Summary

### Readability

**Before**:
```
scripts/runners/run_fast_uncertainty_classification.py
src/uqlab/runner/pipeline.py
src/uqlab/runner/fast_pilot_core.py
```
- ❌ Confusing names
- ❌ 3 layers of indirection
- ❌ Monolithic core (1000+ lines)

**After**:
```
src/uqlab/cli/run.py
src/uqlab/execution/experiment.py
src/uqlab/execution/facade/
```
- ✅ Clear names
- ✅ 2 layers (simpler)
- ✅ Modular coordinators (200-300 lines each)

### Architecture

**Before**:
- ❌ CLI outside package (not installable)
- ❌ Doesn't use facade pattern (even though we created it!)
- ❌ Monolithic core

**After**:
- ✅ CLI inside package (installable)
- ✅ Uses facade pattern (already created!)
- ✅ Modular coordinators

### Usage

**Before**:
```bash
python scripts/runners/run_fast_uncertainty_classification.py --config exp.yaml
```

**After**:
```bash
uqlab run exp.yaml  # After pip install uqlab
```

---

## Recommendation

✅ **Implement Option A** (Simplified 2-Layer Architecture)

**Why**:
1. ✅ More readable (clear naming)
2. ✅ Simpler (2 layers instead of 3)
3. ✅ Uses facade pattern (already created!)
4. ✅ Modular (easy to test/maintain)
5. ✅ Installable (professional CLI)

**Migration Time**: 4 hours total

**Backward Compatibility**: Keep old structure with deprecation warnings

---

**Created**: 2026-06-24  
**Author**: Bob (AI Assistant)  
**Status**: Proposal - Awaiting Decision