# Post-Execution Flow: What Happens After run_fast_uncertainty_classification.py

**Date**: 2026-06-24  
**Question**: What happens after `run_fast_uncertainty_classification.py` completes?

---

## Complete End-to-End Flow

```
UI (Step 3) → Launcher → API → Executor → Runner Script → Pipeline → Results → Database → UI Display
```

---

## Detailed Post-Execution Flow

### Phase 1: Script Execution (Inside Runner)

**File**: [`scripts/runners/run_fast_uncertainty_classification.py`](uqlab-streamlit/scripts/runners/run_fast_uncertainty_classification.py:1)

```python
# CLI wrapper calls pipeline
from uqlab.runner.pipeline import run as pipeline_run

pipeline_run(
    config_path,      # YAML config file
    results_dir,      # Output directory
    seed=seed,
    device_str=device_str,
)
```

**What it does**:
1. Parses command-line arguments
2. Loads YAML config
3. Calls [`uqlab.runner.pipeline.run()`](uqlab-streamlit/src/uqlab/runner/pipeline.py:112-137)

---

### Phase 2: Pipeline Execution

**File**: [`src/uqlab/runner/pipeline.py`](uqlab-streamlit/src/uqlab/runner/pipeline.py:112-137)

```python
def run(
    config_path: Path,
    output_dir: Path,
    *,
    seed: Optional[int] = None,
    device_str: Optional[str] = None,
    progress_callback: Optional[Callable[..., Any]] = None,
    pipeline: Optional[ExperimentPipeline] = None,
) -> dict[str, Any]:
    """Execute one experiment from a run YAML file."""
    
    # Create execution context
    ctx = RunContext(data={
        "config_path": config_path,
        "output_dir": output_dir,
        "seed": seed,
        "device_str": device_str,
        "progress_callback": progress_callback,
    })
    
    # Execute pipeline stages
    pipe = pipeline or _DEFAULT_PIPELINE
    ctx = _execute_pipeline(ctx, pipe)
    
    # Return summary
    return ctx.get("summary") or {}
```

**Pipeline Stages** (from [`runner/patterns.py`](uqlab-streamlit/src/uqlab/runner/patterns.py:40-58)):
1. **Load** - Parse YAML config
2. **Validate** - Check config validity
3. **Execute** - Run training & evaluation
4. **Save** - Write results to disk

**What happens during execution**:
```
Load Config
    ↓
Validate Config
    ↓
Load Dataset (CIFAR-10N with noise)
    ↓
Build Model (DINOv2 + MLP head)
    ↓
Train Model (with dropout for MC sampling)
    ↓
Evaluate Model (MC Dropout passes)
    ↓
Calculate Uncertainty Signals
    ↓
Compute Metrics (AUROC, etc.)
    ↓
Save Results to Disk
    ↓
Return Summary Dict
```

---

### Phase 3: Results Saved to Disk

**Output Directory Structure**:
```
results/fast_uncertainty_classification_20260624_143000/
├── experiment.log          # Full execution log
├── config.yaml             # Copy of input config
├── model_checkpoint.pt     # Trained model weights
├── training_history.json   # Loss/accuracy per epoch
├── evaluation_results.json # Uncertainty metrics
├── predictions.npz         # Model predictions
├── uncertainty_scores.npz  # Per-sample uncertainty
└── summary.json            # High-level metrics
```

**Key Files**:
- **`summary.json`** - Returned by `pipeline.run()`, contains:
  ```json
  {
    "test_accuracy": 0.85,
    "auroc_epistemic": 0.72,
    "auroc_aleatoric": 0.68,
    "training_time_seconds": 450,
    "evaluation_time_seconds": 120
  }
  ```

- **`evaluation_results.json`** - Detailed metrics:
  ```json
  {
    "signals": {
      "entropy": {...},
      "mutual_information": {...},
      "variation_ratio": {...}
    },
    "auroc_scores": {...},
    "confusion_matrix": [...]
  }
  ```

---

### Phase 4: Backend Receives Results

**File**: `backend/app/core/direct_executor.py` (executor that called the script)

**What happens**:
1. **Script completes** - Returns exit code 0 (success) or non-zero (failure)
2. **Executor reads results** - Parses `summary.json` from output directory
3. **Updates database** - Stores results in PostgreSQL

**Database Update**:
```python
# Pseudocode from DirectExecutor
experiment = db.query(Experiment).filter_by(id=experiment_id).first()

if exit_code == 0:
    # Success
    experiment.status = "completed"
    experiment.results = load_json(output_dir / "summary.json")
    experiment.completed_at = datetime.now()
else:
    # Failure
    experiment.status = "failed"
    experiment.error_message = stderr_output
    experiment.failed_at = datetime.now()

db.commit()
```

**Database Schema** (simplified):
```sql
experiments (
    id UUID PRIMARY KEY,
    name VARCHAR,
    status VARCHAR,  -- 'pending', 'running', 'completed', 'failed'
    config JSONB,    -- Input YAML as JSON
    results JSONB,   -- Output summary.json
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
)
```

---

### Phase 5: UI Polls for Updates

**File**: [`streamlit_app_progressive.py`](uqlab-streamlit/streamlit_app_progressive.py:1)

**Auto-Refresh Mechanism**:
```python
# In Results section
if st.session_state.get("auto_refresh", False):
    # Poll every 5 seconds
    time.sleep(5)
    st.rerun()
```

**API Call**:
```python
# Fetch all experiments
response = requests.get(
    f"{API_BASE_URL}/api/v1/experiments",
    headers=get_headers()
)
experiments = response.json()
```

**What the UI displays**:
1. **Experiment List** - All experiments with status badges
2. **Progress Indicators** - Running experiments show spinner
3. **Results Panel** - Completed experiments show metrics
4. **Error Messages** - Failed experiments show error details

---

### Phase 6: Results Visualization

**File**: [`src/uqlab/ui_components/results/experiment_results_panel.py`](uqlab-streamlit/src/uqlab/ui_components/results/experiment_results_panel.py:1)

**What gets displayed**:

1. **Experiment Card**:
   ```
   ✅ exp_20260624_143000 (completed)
   
   Test Accuracy: 85.2%
   AUROC (Epistemic): 0.72
   AUROC (Aleatoric): 0.68
   Training Time: 7m 30s
   ```

2. **Detailed Metrics** (expandable):
   - Confusion matrix
   - ROC curves
   - Uncertainty distribution plots
   - Per-class performance

3. **Download Options**:
   - Download results JSON
   - Download model checkpoint
   - Download predictions

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ EXECUTION PHASE                                                  │
└─────────────────────────────────────────────────────────────────┘

run_fast_uncertainty_classification.py
    ↓
pipeline.run(config_path, output_dir)
    ↓
┌─────────────────────────────────────┐
│ Pipeline Stages:                    │
│ 1. Load config from YAML            │
│ 2. Validate config                  │
│ 3. Load dataset (CIFAR-10N)         │
│ 4. Build model (DINOv2 + MLP)       │
│ 5. Train model (with MC Dropout)    │
│ 6. Evaluate model (MC passes)       │
│ 7. Calculate uncertainty signals    │
│ 8. Compute AUROC metrics            │
│ 9. Save results to disk             │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESULTS ON DISK                                                  │
│                                                                  │
│ results/fast_uncertainty_classification_20260624_143000/        │
│ ├── experiment.log                                              │
│ ├── config.yaml                                                 │
│ ├── model_checkpoint.pt                                         │
│ ├── training_history.json                                       │
│ ├── evaluation_results.json                                     │
│ ├── predictions.npz                                             │
│ ├── uncertainty_scores.npz                                      │
│ └── summary.json  ← KEY FILE                                    │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND PROCESSING                                               │
└─────────────────────────────────────────────────────────────────┘

DirectExecutor (backend/app/core/direct_executor.py)
    ↓
1. Script exits with code 0 (success)
    ↓
2. Read summary.json from output_dir
    ↓
3. Parse results into dict
    ↓
4. Update database:
   - experiment.status = "completed"
   - experiment.results = summary_dict
   - experiment.completed_at = now()
    ↓
5. Commit transaction

┌─────────────────────────────────────────────────────────────────┐
│ DATABASE STATE                                                   │
│                                                                  │
│ experiments table:                                               │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ id: abc-123                                                │ │
│ │ name: "exp_20260624_143000"                                │ │
│ │ status: "completed"  ← UPDATED                             │ │
│ │ config: {...}                                              │ │
│ │ results: {                                                 │ │
│ │   "test_accuracy": 0.85,                                   │ │
│ │   "auroc_epistemic": 0.72,                                 │ │
│ │   "auroc_aleatoric": 0.68,                                 │ │
│ │   ...                                                      │ │
│ │ }  ← UPDATED                                               │ │
│ │ completed_at: "2026-06-24T14:37:30Z"  ← UPDATED            │ │
│ └────────────────────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ UI POLLING & DISPLAY                                             │
└─────────────────────────────────────────────────────────────────┘

Streamlit UI (auto-refresh every 5 seconds)
    ↓
GET /api/v1/experiments
    ↓
Receive updated experiment list
    ↓
Detect status change: "running" → "completed"
    ↓
Render results panel:
    ├── Show success badge ✅
    ├── Display metrics (accuracy, AUROC)
    ├── Show plots (ROC curves, confusion matrix)
    └── Offer downloads (JSON, checkpoint)
```

---

## Key Takeaways

### 1. Results Flow is Linear

```
Script → Disk → Database → UI
```

No circular dependencies, clean one-way data flow.

### 2. Database is Source of Truth

- Script writes to **disk** (file system)
- Executor reads from **disk** and writes to **database**
- UI reads from **database** (not disk)

This ensures:
- ✅ Concurrent access safety
- ✅ Persistent storage
- ✅ Query-able results
- ✅ Multi-user support

### 3. Asynchronous Execution

- **UI doesn't block** - User can navigate away
- **Polling updates** - UI checks for completion every 5 seconds
- **Multiple experiments** - Can run in parallel (if resources allow)

### 4. Error Handling

If script fails:
```
Script exits with code ≠ 0
    ↓
Executor catches error
    ↓
Database updated:
    - status = "failed"
    - error_message = stderr
    ↓
UI displays error message
```

---

## Summary

**After `run_fast_uncertainty_classification.py` completes**:

1. ✅ **Results saved to disk** (`summary.json`, checkpoints, logs)
2. ✅ **Database updated** (status, results, timestamps)
3. ✅ **UI polls for changes** (auto-refresh every 5 seconds)
4. ✅ **Results displayed** (metrics, plots, downloads)

**The flow is completely linear and asynchronous** - no circular dependencies, clean separation between execution and display.

---

**Made with Bob**