# Complete System Flow: UI to Evaluation

**Date**: 2026-06-24
**Purpose**: End-to-end flow from Streamlit UI through evaluation

> **📖 Architecture Questions?** See [`ARCHITECTURE_CLARIFICATION.md`](ARCHITECTURE_CLARIFICATION.md) for package boundaries and responsibilities.

---

## Executive Summary

✅ **`run_experiment_core` IS STILL USED** - It's the main execution function  
✅ **Complete flow documented** - From UI click to database update  
✅ **Evaluation happens INSIDE the runner** - Not a separate step

---

## The Complete Flow

### Layer 1: UI Layer (Streamlit)

```
Step 3 UI (step3_uncertainty.py)
    ↓ User configures epistemic/aleatoric settings
    ↓ Stores in session_state.workflow dict
    ↓ User clicks "Launch Experiment"
    ↓
launch_benchmark_primary() (step3_uncertainty.py:500)
    ↓ Validates workflow config
    ↓ Calls orchestrator
```

**File**: [`src/uqlab/ui_components/workflow/step3_uncertainty.py`](src/uqlab/ui_components/workflow/step3_uncertainty.py:500)

---

### Layer 2: Orchestrator Layer

```
launch_workflow_experiments() (experiment_launcher.py:50)
    ↓ Receives workflow dict
    ↓ Calls sweep generator
    ↓
generate_sweep_runs() (experiment_launcher.py:100)
    ↓ Generates experiment configs
    ↓ For each config, calls YAML builder
    ↓
build_run_yaml() (run_spec.py:200)
    ↓ Transforms workflow → YAML config
    ↓ Returns ExperimentConfig object
    ↓
launch_workflow_experiments() (continued)
    ↓ Submits each config to backend
    ↓ POST /api/v1/experiments/no-auth
```

**Files**:
- [`src/uqlab_orchestrator/experiment_launcher.py`](src/uqlab_orchestrator/experiment_launcher.py:50)
- [`src/uqlab_orchestrator/run_spec.py`](src/uqlab_orchestrator/run_spec.py:200)

---

### Layer 3: Backend API Layer

```
FastAPI Backend (POST /api/v1/experiments/no-auth)
    ↓ Receives ExperimentConfig
    ↓ Creates database record (status="pending")
    ↓ Calls executor
    ↓
DirectExecutor.execute() (direct_executor.py:50)
    ↓ Writes config to YAML file
    ↓ Builds subprocess command
    ↓ Executes: python run_fast_uncertainty_classification.py --config run.yaml
```

**Files**:
- [`backend/app/api/routes/experiments.py`](backend/app/api/routes/experiments.py:100)
- [`backend/app/services/executors/direct_executor.py`](backend/app/services/executors/direct_executor.py:50)

---

### Layer 4: CLI Entry Point

```
run_fast_uncertainty_classification.py (CLI script)
    ↓ main() function
    ↓ Parses command-line arguments
    ↓ Loads config from YAML
    ↓ Calls run_from_yaml()
```

**File**: [`scripts/runners/run_fast_uncertainty_classification.py`](scripts/runners/run_fast_uncertainty_classification.py:16)

**Code**:
```python
def main() -> None:
    """Parse args and delegate to uqlab.runner.execute.run_from_yaml."""
    parser = argparse.ArgumentParser(description="Fast uncertainty classification pilot")
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    
    config = ExperimentConfig.from_yaml(args.config)
    
    from uqlab.runner.execute import run_from_yaml as pipeline_run
    
    pipeline_run(
        config_path,
        results_dir,
        seed=seed,
        device_str=device_str,
    )
```

---

### Layer 5: Pipeline Orchestrator

```
run_from_yaml() (execute.py)
    ↓ Creates RunContext
    ↓ Executes 3-stage pipeline:
    ↓
    ├─ Stage 1: _stage_load_config()
    │   └─ Load YAML → ExperimentConfig
    ↓
    ├─ Stage 2: _stage_validate_config()
    │   └─ Validate architecture, signals, etc.
    ↓
    └─ Stage 3: _stage_execute()
        └─ Calls run_experiment_core() ← MAIN EXECUTION
```

**File**: [`src/uqlab/runner/execute.py`](src/uqlab/runner/execute.py)

**Code**:
```python
def run(
    config_path: Path,
    output_dir: Path,
    *,
    seed: Optional[int] = None,
    device_str: Optional[str] = None,
) -> dict[str, Any]:
    """Execute one experiment from a run YAML file."""
    ctx = RunContext(data={
        "config_path": config_path,
        "output_dir": output_dir,
        "seed": seed,
        "device_str": device_str,
    })
    
    # Run 3-stage pipeline
    ctx = _execute_pipeline(ctx, _DEFAULT_PIPELINE)
    return ctx.get("summary") or {}

# Pipeline stages
_DEFAULT_PIPELINE = ExperimentPipeline([
    _stage_load_config,      # Load YAML
    _stage_validate_config,  # Validate
    _stage_execute,          # Execute (calls run_experiment_core)
])
```

---

### Layer 6: Core Execution (Training + Evaluation)

```
run_experiment_core() (fast_pilot_core.py:200)
    ↓
    ├─ PHASE 1: Data Loading (lines 200-400)
    │   ├─ Load CIFAR-10N dataset
    │   ├─ Apply noise injection
    │   ├─ Sample train/eval splits
    │   └─ Create data loaders
    ↓
    ├─ PHASE 2: Model Building (lines 400-500)
    │   ├─ Build DINOv2/ResNet/CNN model
    │   ├─ Initialize optimizer
    │   └─ Setup training
    ↓
    ├─ PHASE 3: Training (lines 500-700)
    │   ├─ Train for N epochs
    │   ├─ Track loss/accuracy
    │   └─ Save checkpoints
    ↓
    ├─ PHASE 4: Evaluation (lines 700-900) ← EVALUATION HAPPENS HERE
    │   ├─ collect_uncertainty_signals()
    │   │   ├─ Run MC Dropout (if enabled)
    │   │   ├─ Compute attribution (DualXDA, EK-FAC)
    │   │   ├─ Compute predictive uncertainty
    │   │   └─ Return signal_table dict
    │   ↓
    │   ├─ score_uncertainty_signals()
    │   │   ├─ Compute AUROC per signal
    │   │   ├─ Detect noisy labels (aleatoric)
    │   │   ├─ Detect under-supported classes (epistemic)
    │   │   └─ Return metrics dict
    │   ↓
    │   └─ persist_experiment_summaries()
    │       ├─ Save summary.json
    │       ├─ Save metrics.csv
    │       ├─ Save per_sample_signals.csv
    │       └─ Save results.pt
    ↓
    └─ PHASE 5: Return Summary (lines 900-1000)
        └─ Return dict with all results
```

**File**: [`src/uqlab/runner/fast_pilot_core.py`](src/uqlab/runner/fast_pilot_core.py:200)

**Key Point**: `run_experiment_core()` is a **monolithic function** that does:
1. Data loading
2. Model building
3. Training
4. **Evaluation** (embedded, not separate)
5. Result saving

---

### Layer 7: Evaluation Details

#### Step 1: Signal Collection

**File**: [`src/uqlab/evaluation/pipeline/fast_pilot_eval.py:46`](src/uqlab/evaluation/pipeline/fast_pilot_eval.py:46)

```python
def collect_uncertainty_signals(
    model: nn.Module,
    train_dataset,
    eval_inputs: torch.Tensor,
    device: torch.device,
    config: EvalSignalConfig,
) -> dict[str, Any]:
    """
    Compute uncertainty signals for each evaluation sample.
    
    Process:
    1. Run MC Dropout (if mc_passes > 0)
       - Forward pass model N times with dropout
       - Collect softmax outputs
       - Compute entropy, mutual info
    
    2. Run Attribution (if enabled)
       - DualXDA: Gradient-based attribution
       - EK-FAC: Eigenvalue-based attribution
       - Compute coherence, mass, etc.
    
    3. Run Deterministic Forward
       - Single forward pass
       - Get logits, predictions
    
    Returns:
        signal_table: dict[signal_name → tensor[N_eval_samples]]
        Example: {
            "expected_entropy": tensor([0.5, 0.3, 0.8, ...]),
            "mutual_info": tensor([0.2, 0.1, 0.4, ...]),
            "dualxda_coherence": tensor([0.7, 0.9, 0.6, ...]),
            ...
        }
    """
```

#### Step 2: Signal Scoring

**File**: [`src/uqlab/evaluation/pipeline/fast_pilot_eval.py:314`](src/uqlab/evaluation/pipeline/fast_pilot_eval.py:314)

```python
def score_uncertainty_signals(
    signal_table: dict[str, torch.Tensor],
    eval_group_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    ...
) -> dict[str, Any]:
    """
    Compute AUROC for each signal.
    
    Process:
    1. For each signal in signal_table:
       a. Aleatoric AUROC: Can it detect noisy labels?
          - Positives: eval_is_noisy == True
          - Negatives: eval_is_noisy == False
          - AUROC = how well signal ranks noisy above clean
       
       b. Epistemic AUROC: Can it detect under-supported classes?
          - Positives: eval_group_labels == GROUP_EPISTEMIC
          - Negatives: eval_group_labels == GROUP_CLEAN
          - AUROC = how well signal ranks epistemic above clean
    
    2. Save per-sample results to CSV
    
    3. Return metrics dict
    
    Returns:
        metrics: dict with AUROC scores
        Example: {
            "expected_entropy_aleatoric_auroc": 0.68,
            "expected_entropy_epistemic_auroc": 0.72,
            "mutual_info_aleatoric_auroc": 0.65,
            "mutual_info_epistemic_auroc": 0.70,
            ...
        }
    """
```

#### Step 3: Result Persistence

**File**: [`src/uqlab/evaluation/evaluator.py:500`](src/uqlab/evaluation/evaluator.py:500)

```python
def persist_experiment_summaries(
    results_dir: Path,
    signal_table: dict,
    metrics: dict,
    ...
):
    """
    Save results to disk.
    
    Files created:
    1. summary.json - For backend (status, metrics, config)
    2. metrics.csv - For analysis (AUROC per signal)
    3. per_sample_signals.csv - For debugging (per-sample values)
    4. results.pt - For plots (PyTorch tensors)
    """
```

---

### Layer 8: Post-Execution (Backend)

```
DirectExecutor.execute() (continued)
    ↓ Subprocess completes
    ↓ Read exit code
    ↓ Load summary.json from disk
    ↓ Update database record:
    │   ├─ status = "completed" (or "failed")
    │   ├─ results = summary.json content
    │   ├─ completed_at = now()
    │   └─ error_message (if failed)
    ↓
Database Updated
```

**File**: [`backend/app/services/executors/direct_executor.py:150`](backend/app/services/executors/direct_executor.py:150)

---

### Layer 9: UI Display

```
UI Auto-Refresh (every 5 seconds)
    ↓ GET /api/v1/experiments
    ↓ Fetch all experiments from database
    ↓ Group by sweep (if applicable)
    ↓ Display in results panel:
    │   ├─ Status (pending/running/completed/failed)
    │   ├─ Metrics (accuracy, AUROC scores)
    │   ├─ Plots (if completed)
    │   └─ Download buttons
```

**File**: [`src/uqlab/ui_components/results/experiment_results_panel.py`](src/uqlab/ui_components/results/experiment_results_panel.py:100)

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                              │
│  step3_uncertainty.py → launch_benchmark_primary()              │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                │
│  experiment_launcher.py → generate_sweep_runs()                 │
│  run_spec.py → build_run_yaml()                                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│  POST /api/v1/experiments/no-auth                               │
│  DirectExecutor.execute()                                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CLI ENTRY POINT                               │
│  run_fast_uncertainty_classification.py                         │
│  main() → run_from_yaml()                                         │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PIPELINE ORCHESTRATOR                          │
│  pipeline.py → run()                                             │
│  ├─ _stage_load_config()                                        │
│  ├─ _stage_validate_config()                                    │
│  └─ _stage_execute() → run_experiment_core()                   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              CORE EXECUTION (MONOLITHIC)                         │
│  fast_pilot_core.py → run_experiment_core()                    │
│  ├─ PHASE 1: Data Loading (lines 200-400)                      │
│  ├─ PHASE 2: Model Building (lines 400-500)                    │
│  ├─ PHASE 3: Training (lines 500-700)                          │
│  ├─ PHASE 4: EVALUATION (lines 700-900) ← HERE                 │
│  │   ├─ collect_uncertainty_signals()                          │
│  │   ├─ score_uncertainty_signals()                            │
│  │   └─ persist_experiment_summaries()                         │
│  └─ PHASE 5: Return Summary (lines 900-1000)                   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    POST-EXECUTION                                │
│  DirectExecutor reads summary.json                              │
│  Updates database (status, results, timestamps)                 │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      UI DISPLAY                                  │
│  Auto-refresh polls database every 5 seconds                    │
│  Displays results, plots, download buttons                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Findings

### 1. `run_experiment_core` Status

✅ **STILL USED** - It's the main execution function

**Location**: [`src/uqlab/runner/fast_pilot_core.py:200`](src/uqlab/runner/fast_pilot_core.py:200)

**Called by**: [`execute.py`](src/uqlab/runner/execute.py) in `_stage_execute()`

```python
# pipeline.py line 78
summary = run_experiment_core(
    config,
    results_dir,
    seed=seed,
    device_str=device_str,
    config_path=config_path,
    project_root=Path(project_root),
)
```

### 2. Naming Clarification

| Name | Purpose | File |
|------|---------|------|
| `run_fast_uncertainty_classification.py` | CLI entry point script | `scripts/runners/` |
| `run_from_yaml()` | Experiment orchestrator | `src/uqlab/runner/execute.py` |
| `run_experiment_core()` | Main execution function | `src/uqlab/runner/fast_pilot_core.py` |

**Relationship**:
```
CLI script → run_from_yaml() → run_experiment_core()
```

### 3. Evaluation Location

❌ **NOT a separate step** - Evaluation is embedded in `run_experiment_core()`

**Lines 700-900** of `fast_pilot_core.py`:
1. Training completes (line 700)
2. Evaluation starts (line 700)
3. Evaluation ends (line 900)
4. Results saved (line 900)

**No separation** between training and evaluation phases.

---

## Related Documentation

**Flow Analysis**:
- [`STEP3_FLOW_ANALYSIS.md`](STEP3_FLOW_ANALYSIS.md) - UI to orchestrator flow
- [`POST_EXECUTION_FLOW.md`](POST_EXECUTION_FLOW.md) - Post-execution flow
- [`docs/architecture/evaluation-pipeline.md`](docs/architecture/evaluation-pipeline.md) - Evaluation pipeline structure

**Complete Flows**:
- [`backend/RUN_LABEL_NOISE_SWEEP_FLOW.md`](backend/RUN_LABEL_NOISE_SWEEP_FLOW.md) - Most comprehensive (912 lines)
- [`docs/UQLAB_FLOW.md`](docs/UQLAB_FLOW.md) - System overview

**Architecture**:
- [`DUAL_FACADE_ARCHITECTURE.md`](DUAL_FACADE_ARCHITECTURE.md) - Proposed facade (not implemented)
- [`COMPONENT_REUSE_ANALYSIS.md`](COMPONENT_REUSE_ANALYSIS.md) - Component analysis

---

**Created**: 2026-06-24  
**Author**: Bob (AI Assistant)  
**Status**: Complete Flow Documented