# Terminology Clarification: runners vs runner

> **Superseded (2026-06):** Module names below predate `runner/execute.py`, `runner/experiment_core.py`, and the evaluation package split. See [`docs/architecture/PACKAGE_REDESIGN.md`](docs/architecture/PACKAGE_REDESIGN.md) and [`START_HERE.md`](START_HERE.md).

**Date**: 2026-06-24  
**Question**: "so technically the runners and runner are the same right?"

---

## Answer: NO - They Are Different!

### The Confusion

**`scripts/runners/`** (plural) = Directory containing CLI entry point scripts  
**`uqlab/runner/`** (singular) = Package containing execution pipeline

**They are NOT the same** - one is a script wrapper, the other is the execution engine.

---

## Detailed Breakdown

### 1. `scripts/runners/` (Plural) - CLI Scripts Directory

**Location**: `scripts/runners/run_fast_uncertainty_classification.py`

**Purpose**: Command-line entry points (thin wrappers)

**What it does**:
```python
def main():
    """Parse CLI args and delegate to pipeline."""
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    
    # Load config
    config = ExperimentConfig.from_yaml(args.config)
    
    # Delegate to pipeline
    from uqlab.runner.pipeline import run
    run(config_path, output_dir, seed=args.seed)
```

**Characteristics**:
- ✅ Thin wrapper (< 60 lines)
- ✅ Parses command-line arguments
- ✅ Delegates to `uqlab.runner.pipeline`
- ✅ No ML logic
- ✅ Entry point for CLI usage

**Usage**:
```bash
python scripts/runners/run_fast_uncertainty_classification.py \
    --config exp.yaml \
    --seed 42 \
    --device cuda
```

---

### 2. `uqlab/runner/` (Singular) - Execution Pipeline Package

**Location**: `src/uqlab/runner/`

**Purpose**: ML execution engine (orchestrates training/evaluation)

**Structure**:
```
uqlab/runner/
├── __init__.py
├── pipeline.py              # 3-stage orchestrator
├── fast_pilot_core.py       # Main execution (1000+ lines)
└── patterns.py              # Pipeline patterns
```

**What it does**:

#### `pipeline.py` (Orchestrator)
```python
def run(config_path, output_dir, seed=None, device_str=None):
    """
    3-stage pipeline orchestrator.
    
    Stage 1: Load config from YAML
    Stage 2: Validate config
    Stage 3: Execute training
    """
    ctx = RunContext()
    
    # Stage 1: Load
    ctx = _stage_load_config(ctx)
    
    # Stage 2: Validate
    ctx = _stage_validate_config(ctx)
    
    # Stage 3: Execute
    ctx = _stage_execute(ctx)  # Calls run_experiment_core()
    
    return ctx.get("summary")
```

#### `fast_pilot_core.py` (Execution Engine)
```python
def run_experiment_core(config, results_dir, ...):
    """
    Main execution function (1000+ lines).
    
    - Load dataset
    - Build model
    - Train model
    - Evaluate model
    - Save artifacts
    """
    # Lines 200-400: Data loading
    train_loader, val_loader = load_data(config.data)
    
    # Lines 400-500: Model building
    model = build_model(config.model)
    
    # Lines 500-700: Training
    for epoch in range(config.training.epochs):
        train_epoch(model, train_loader)
    
    # Lines 700-900: Evaluation
    signals = evaluate_uncertainty(model, val_loader)
    
    # Lines 900-1000: Save results
    save_artifacts(results_dir, model, signals)
```

**Characteristics**:
- ✅ Heavy ML logic (1000+ lines)
- ✅ Orchestrates complete experiment
- ✅ Loads data, builds models, trains, evaluates
- ✅ Core execution engine
- ✅ Used by CLI, backend, notebooks

---

## Comparison Table

| Aspect | `scripts/runners/` (Plural) | `uqlab/runner/` (Singular) |
|--------|----------------------------|---------------------------|
| **Type** | CLI script directory | Python package |
| **Purpose** | Entry point wrapper | Execution engine |
| **Size** | < 60 lines | 1000+ lines |
| **Logic** | Argument parsing | ML training/evaluation |
| **Dependencies** | argparse, pathlib | PyTorch, NumPy, etc. |
| **Used by** | Command line | CLI, backend, notebooks |
| **Location** | `scripts/runners/` | `src/uqlab/runner/` |
| **Imports from** | `uqlab.runner` | Nothing (it's the engine) |

---

## Execution Flow

```
1. User runs CLI script
   $ python scripts/runners/run_fast_uncertainty_classification.py --config exp.yaml
   
2. CLI script (scripts/runners/)
   - Parses arguments
   - Loads config
   - Calls: from uqlab.runner.pipeline import run
   
3. Pipeline (uqlab/runner/pipeline.py)
   - Stage 1: Load config
   - Stage 2: Validate
   - Stage 3: Call run_experiment_core()
   
4. Core (uqlab/runner/fast_pilot_core.py)
   - Load data
   - Build model
   - Train
   - Evaluate
   - Save artifacts
```

---

## Why The Confusion?

**Similar Names**:
- `scripts/runners/` (plural) - sounds like it contains multiple runners
- `uqlab/runner/` (singular) - sounds like it's a single runner

**Reality**:
- `scripts/runners/` = Directory of CLI entry point scripts (wrappers)
- `uqlab/runner/` = Package containing the actual execution engine

**Better Names** (proposed):
- `scripts/runners/` → `scripts/cli/` (clearer: CLI entry points)
- `uqlab/runner/` → `uqlab/execution/` (clearer: execution engine)

But we keep current names for backward compatibility.

---

## Key Takeaway

**`scripts/runners/`** (plural):
- CLI entry point scripts
- Thin wrappers
- Parse arguments
- Delegate to pipeline

**`uqlab/runner/`** (singular):
- Execution engine package
- Heavy ML logic
- Orchestrates training/evaluation
- Core functionality

**Relationship**:
```
scripts/runners/run_fast_*.py  →  imports from  →  uqlab/runner/pipeline.py
     (CLI wrapper)                                    (Execution engine)
```

---

## Recommendation

### Current Structure (Confusing)
```
scripts/
└── runners/                    # CLI scripts (plural)
    └── run_fast_*.py

src/uqlab/
└── runner/                     # Execution engine (singular)
    ├── pipeline.py
    └── fast_pilot_core.py
```

### Proposed Structure (Clearer)
```
src/uqlab/
├── cli/                        # CLI entry points
│   └── run_fast_uncertainty.py
└── runner/                     # Execution engine
    ├── pipeline.py
    └── fast_pilot_core.py
```

**Benefits**:
1. ✅ CLI scripts inside package (installable)
2. ✅ Clear separation: `cli/` = entry points, `runner/` = engine
3. ✅ No more `scripts/runners/` confusion
4. ✅ Can install as console script: `pip install uqlab` → `uqlab-run` command

---

## Summary

**Question**: "so technically the runners and runner are the same right?"

**Answer**: ❌ **NO!**

- **`scripts/runners/`** (plural) = CLI script directory (thin wrappers)
- **`uqlab/runner/`** (singular) = Execution engine package (heavy ML logic)

**They are different layers**:
```
CLI Layer:     scripts/runners/run_fast_*.py
                      ↓ imports from
Engine Layer:  uqlab/runner/pipeline.py → fast_pilot_core.py
```

**Proposed fix**: Move `scripts/runners/` → `src/uqlab/cli/` (see FINAL_ARCHITECTURE_DECISION.md)

---

**Created**: 2026-06-24  
**Author**: Bob (AI Assistant)  
**Status**: Clarification Complete