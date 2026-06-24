# 🔌 Frontend-Backend Interface: How Streamlit Calls run_fast_uncertainty_classification.py

**Quick Answer:** The Streamlit UI does NOT directly call the script. Instead:
1. **Streamlit UI** → sends config to **FastAPI Backend**
2. **FastAPI Backend** → calls **`run_fast_uncertainty_classification.py`** via **DirectExecutor**
3. **Script** → saves results to disk
4. **Backend** → reads results and returns to UI

---

## 📋 COMPLETE FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (Frontend)                   │
│  streamlit_app_progressive.py                                │
│                                                              │
│  User fills form:                                            │
│  • Dataset: CIFAR-10N                                        │
│  • Noise: Custom 20%                                         │
│  • Model: DINOv2 + MLP                                       │
│  • Training: 12 epochs                                       │
│  • Evaluation: 20 MC passes                                  │
│                                                              │
│  [Submit Button] ──────────────────────────────────────────┐ │
└────────────────────────────────────────────────────────────┼─┘
                                                              │
                                                              │ HTTP POST
                                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (API Layer)                │
│  backend/app/api/routes/experiments.py                       │
│                                                              │
│  POST /api/v1/experiments                                    │
│  ├─ Validate config                                          │
│  ├─ Create UncertaintyExperiment row in PostgreSQL           │
│  ├─ Generate YAML config file                                │
│  └─ Call DirectExecutor.execute() ─────────────────────────┐ │
└────────────────────────────────────────────────────────────┼─┘
                                                              │
                                                              │ Python import
                                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  DIRECT EXECUTOR (Orchestrator)              │
│  backend/app/services/executors/direct_executor.py           │
│                                                              │
│  DirectExecutor._run_training_sync():                        │
│  ├─ import run_fast_uncertainty_classification               │
│  ├─ importlib.reload(run_fast_uncertainty_classification)    │
│  ├─ from run_fast_uncertainty_classification import main     │
│  ├─ Set sys.argv = ["script", "--config", "config.yaml"]     │
│  └─ Call main() ────────────────────────────────────────────┐│
└────────────────────────────────────────────────────────────┼─┘
                                                              │
                                                              │ Direct function call
                                                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CORE ML SCRIPT (Training & Evaluation)          │
│  scripts/run_fast_uncertainty_classification.py              │
│                                                              │
│  main():                                                     │
│  1. Load YAML config ← ALL parameters come from here         │
│  2. Extract config values:                                   │
│     • dataset_name = config.data.dataset_name                │
│     • noise_type = config.data.noise_type                    │
│     • aleatoric_noise_percentage = config.data.aleatoric_... │
│     • architecture = config.model.architecture               │
│     • epochs = config.training.epochs                        │
│     • mc_passes = config.evaluation.mc_passes                │
│  3. Load dataset (config-driven):                            │
│     dataset = load_classification_dataset(                   │
│         dataset_name,  ← from config                         │
│         noise_type=noise_type,  ← from config                │
│         aleatoric_noise_percentage=alea_for_load  ← config   │
│     )                                                        │
│  4. Inject custom noise IF aleatoric_noise_percentage > 0    │
│  5. Split data (train/clean/aleatoric/epistemic)             │
│  6. Train model (architecture/epochs from config)            │
│  7. Compute uncertainty signals (mc_passes from config)      │
│  8. Calculate AUROC scores                                   │
│  9. Save results to disk:                                    │
│     ├─ summary.json                                          │
│     ├─ per_sample_signals.csv                                │
│     ├─ checkpoint.pt                                         │
│     └─ results.pt                                            │
└─────────────────────────────────────────────────────────────┘
                                                              │
                                                              │ File I/O
                                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESULTS ON DISK                           │
│  results/exp_20240115_143022/                                │
│  ├─ summary.json          ← Backend reads this               │
│  ├─ per_sample_signals.csv                                   │
│  ├─ checkpoint.pt                                            │
│  └─ results.pt                                               │
└─────────────────────────────────────────────────────────────┘
                                                              │
                                                              │ Read results
                                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  DIRECT EXECUTOR (Result Parser)             │
│  backend/app/services/executors/direct_executor.py           │
│                                                              │
│  DirectExecutor._read_results():                             │
│  ├─ Load summary.json                                        │
│  ├─ Extract AUROC scores                                     │
│  ├─ Extract eval sizes                                       │
│  └─ Return TrainingResult ──────────────────────────────────┐│
└────────────────────────────────────────────────────────────┼─┘
                                                              │
                                                              │ Return result
                                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (Storage)                  │
│  backend/app/api/routes/experiments.py                       │
│                                                              │
│  ├─ Update UncertaintyExperiment status = "completed"        │
│  ├─ Store AUROC scores in database                           │
│  └─ Return experiment ID to frontend ───────────────────────┐│
└────────────────────────────────────────────────────────────┼─┘
                                                              │
                                                              │ HTTP Response
                                                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (Results Display)            │
│  streamlit_app_progressive.py                                │
│                                                              │
│  ├─ Poll GET /api/v1/experiments/{id}                        │
│  ├─ Display status: "Running..." → "Completed"               │
│  ├─ Fetch results: GET /api/v1/experiments/{id}/results      │
│  └─ Render plots:                                            │
│     ├─ AUROC bar charts                                      │
│     ├─ Signal comparison plots                               │
│     └─ Uncertainty distribution plots                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 KEY INTERFACE POINTS

### 1. **UI → Backend** (HTTP POST)

**File:** `streamlit_app_progressive.py` (or `streamlit_app.py`)

```python
# User submits form
response = requests.post(
    f"{API_BASE_URL}/api/v1/experiments",
    json={
        "name": "exp_20240115_143022",
        "config": {
            "data": {
                "noise_type": "worse_label",
                "aleatoric_noise_percentage": 20.0,
                "under_supported_classes": [3, 5],
                "under_train_per_class": 50,
                "regular_train_per_class": 300,
                "eval_per_group": 500
            },
            "model": {
                "architecture": "dinov2_mlp",
                "dinov2_model": "small",
                "hidden_dim": 256,
                "dropout": 0.3
            },
            "training": {
                "epochs": 12,
                "learning_rate": 0.001,
                "train_batch_size": 256
            },
            "evaluation": {
                "mc_passes": 20,
                "top_k": 10
            }
        }
    }
)
```

---

### 2. **Backend → Script** (Python Import)

**File:** `backend/app/services/executors/direct_executor.py`

```python
def _run_training_sync(self, config_path: Path, output_dir: Path, progress_callback):
    """Execute training script IN-PROCESS (not subprocess)"""
    
    # Import the script as a Python module
    import run_fast_uncertainty_classification
    importlib.reload(run_fast_uncertainty_classification)
    from run_fast_uncertainty_classification import main
    
    # Set command-line arguments
    sys.argv = [
        str(self.script_path),
        "--config", str(config_path),
        "--output_dir", str(output_dir)
    ]
    
    # Call the main function directly
    main()  # ← This runs the entire experiment
```

**Key Point:** The script is **NOT** run as a subprocess. It's imported and called directly as a Python function.

---

### 3. **Script → Disk** (File I/O)

**File:** `scripts/run_fast_uncertainty_classification.py`

```python
def main():
    # ... training and evaluation ...
    
    # Save results to disk
    summary = {
        "config": {...},
        "one_vs_rest_auroc": [
            {"signal": "mutual_info", "aleatoric": 0.85, "epistemic": 0.72},
            {"signal": "inverse_coherence", "aleatoric": 0.78, "epistemic": 0.81},
            # ... more signals
        ],
        "macro_f1": [
            {"signal_set": "all_signals", "macro_f1": 0.73},
            # ... more signal sets
        ]
    }
    
    # Write summary.json (backend reads this)
    with (results_dir / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)
    
    # Write per-sample data (for debugging)
    save_per_sample_csv(
        output_path=results_dir / "per_sample_signals.csv",
        signal_table=signal_table,
        eval_group_labels=eval_group_labels,
        # ... more data
    )
    
    # Save model checkpoint
    torch.save(checkpoint, results_dir / "checkpoint.pt")
```

---

### 4. **Disk → Backend** (Result Parsing)

**File:** `backend/app/services/executors/direct_executor.py`

```python
def _read_results(self, output_dir: Path) -> TrainingResult:
    """Parse summary.json and extract metrics"""
    
    summary_path = output_dir / "summary.json"
    with summary_path.open() as f:
        summary = json.load(f)
    
    # Extract AUROC scores
    auroc_data = {}
    for item in summary.get("one_vs_rest_auroc", []):
        signal = item["signal"]
        auroc_data[signal] = {
            "aleatoric": item.get("aleatoric"),
            "epistemic": item.get("epistemic")
        }
    
    # Extract eval sizes
    eval_sizes = summary.get("eval_sizes", {})
    
    return TrainingResult(
        status="completed",
        auroc_scores=auroc_data,
        eval_sizes=eval_sizes,
        # ... more fields
    )
```

---

### 5. **Backend → UI** (HTTP Response)

**File:** `backend/app/api/routes/experiments.py`

```python
@router.get("/{experiment_id}")
def get_experiment(experiment_id: int):
    """Return experiment status and results"""
    
    experiment = db.query(UncertaintyExperiment).get(experiment_id)
    
    return {
        "id": experiment.id,
        "name": experiment.name,
        "status": experiment.status,  # "pending", "running", "completed"
        "auroc_scores": experiment.auroc_scores,  # From summary.json
        "eval_sizes": experiment.eval_sizes,
        "created_at": experiment.created_at,
        "completed_at": experiment.completed_at
    }
```

---

## 📚 DETAILED DOCUMENTATION

For the **complete, line-by-line flow** of how a label noise sweep works, see:

**[`backend/RUN_LABEL_NOISE_SWEEP_FLOW.md`](backend/RUN_LABEL_NOISE_SWEEP_FLOW.md)**

This 912-line document explains:
- ✅ Exact HTTP routes and handlers
- ✅ How batch experiments expand into multiple runs
- ✅ How `aleatoric_noise_percentage` drives the sweep
- ✅ How the script injects custom noise
- ✅ How AUROC is calculated
- ✅ How results are aggregated
- ✅ Debugging workflow for suspicious plots

---

## 🎯 QUICK REFERENCE

### Where is the logic implemented?

| Component | File | Purpose |
|-----------|------|---------|
| **UI Form** | `streamlit_app_progressive.py` | User input collection |
| **API Endpoint** | `backend/app/api/routes/experiments.py` | HTTP interface |
| **Orchestrator** | `backend/app/services/executors/direct_executor.py` | Script execution |
| **Core Logic** | `scripts/run_fast_uncertainty_classification.py` | Training & evaluation |
| **Result Parser** | `backend/app/services/executors/direct_executor.py` | Extract metrics from disk |

### Key Configuration Fields

```yaml
# config.yaml (generated by backend, read by script)
data:
  aleatoric_noise_percentage: 20.0  # ← Drives label noise sweep
  under_supported_classes: [3, 5]   # ← Drives epistemic uncertainty
  eval_per_group: 500               # ← Samples per uncertainty group

model:
  architecture: "dinov2_mlp"        # ← DINOv2 + MLP or ResNet
  training_mode: "feature_space"    # ← Fast (embeddings) or slow (images)

evaluation:
  mc_passes: 20                     # ← MC Dropout passes (0 to disable)
  top_k: 10                         # ← Top-k training samples for attribution
```

### Output Files (Script → Backend)

```
results/exp_20240115_143022/
├── summary.json              ← Backend reads this (AUROC, eval sizes)
├── per_sample_signals.csv    ← Debugging (all signals per sample)
├── checkpoint.pt             ← Model weights
└── results.pt                ← Complete results (predictions, embeddings)
```

---

## 🚨 IMPORTANT NOTES

### 1. **No Subprocess** ❌
The script is **NOT** run via `subprocess.run()` or shell commands. It's imported and called directly as a Python function.

### 2. **In-Process Execution** ✅
```python
# This is what happens:
import run_fast_uncertainty_classification
from run_fast_uncertainty_classification import main
main()  # Direct function call
```

### 3. **Config via YAML** 📄
The backend generates a YAML file, and the script reads it:
```python
# In run_fast_uncertainty_classification.py
config = ExperimentConfig.from_yaml(args.config)
```

### 4. **Results via JSON** 📊
The script writes `summary.json`, and the backend parses it:
```python
# In direct_executor.py
with (output_dir / "summary.json").open() as f:
    summary = json.load(f)
```

---

## 🔍 DEBUGGING WORKFLOW

If you want to understand what data a plot is based on:

1. **Find the experiment ID** in the UI
2. **Locate the results directory**: `results/exp_{id}/`
3. **Open `summary.json`** to see AUROC scores
4. **Open `per_sample_signals.csv`** to see raw data
5. **Verify** the eval group sizes and signal values
6. **Only then** check the UI plots

**Rule:** Start from the files on disk, not from the UI.

---

## 📖 RELATED DOCUMENTATION

- **Complete Flow:** [`backend/RUN_LABEL_NOISE_SWEEP_FLOW.md`](backend/RUN_LABEL_NOISE_SWEEP_FLOW.md) (912 lines)
- **System Architecture:** [`SYSTEM_FLOW.md`](SYSTEM_FLOW.md)
- **Script Implementation:** [`RUN_FAST_UQ_IMPLEMENTATION_GUIDE.md`](RUN_FAST_UQ_IMPLEMENTATION_GUIDE.md)
- **UI Components:** [`src/uqlab/ui_components/README.md`](src/uqlab/ui_components/README.md)

---

**Summary:** The Streamlit UI sends config to FastAPI, which calls `run_fast_uncertainty_classification.py` via `DirectExecutor`, which saves results to disk, which the backend reads and returns to the UI. No subprocess, no shell commands—just Python imports and function calls. 🚀