# Launch to Visualization Flow (Paper Sweeps Mode)

Complete UX and code execution path from "Confirm Launch" button to results visualization in the **current paper sweeps implementation**.

---

## 🎯 Quick Overview

```text
USER CLICKS "Confirm Launch"
  ↓
UI: Collect workflow dict (Steps 1-5)
  ↓
Orchestrator: Generate sweep configs (5-10 runs)
  ↓
API: Create DB records + start jobs
  ↓
Executor: Run pipeline.run() for each config
  ↓
Pipeline: Train model + evaluate + write artifacts
  ↓
Artifacts: results.pt, summary.json, per_sample_signals.csv
  ↓
UI: Poll API every 5s + load artifacts
  ↓
UI: Render AUROC tables + signal plots
```

---

## 📋 Current Config Structure (Paper Sweeps)

### What User Configures in UI

```python
workflow = {
    "dataset_config": {
        "dataset_name": "cifar10n",
        "noise_type": "worse_label"
    },
    "uncertainty_config": {
        "under_supported": "4,5",           # Classes with sparse training
        "under_train_per_class": 50,        # Samples per sparse class
        "regular_train_per_class": 300,     # Samples per regular class
    },
    "training_config": {
        "model_architecture": "resnet18",
        "epochs": 12,
        "learning_rate": 0.001,
        # ...
    },
    "evaluation_config": {
        "mc_passes": 20,
        "signals": ["predictive_entropy", "mutual_info"],
        "eval_per_group": 100  # Samples per eval pool
    },
    "sweep_config": {
        "sweep_mode": "epistemic",  # or "aleatoric" or "none"
        "epistemic_values": [25, 50, 100, 150, 200],  # For Fig. 3
        "aleatoric_values": [0, 25, 50, 75, 100],     # For Fig. 4
    }
}
```

### How It Maps to Training Data

**Global class assignment:**
```python
under_supported_classes = [4, 5]  # 2 classes with sparse training
regular_classes = [0, 1, 2, 3, 6, 7, 8, 9]  # 8 classes with full training

# Training samples per class
class_4: 50 samples (sparse)
class_5: 50 samples (sparse)
class_0: 300 samples (regular)
class_1: 300 samples (regular)
# ... etc for all regular classes

# Label noise applied GLOBALLY to regular classes only
# If aleatoric_noise_percentage = 30:
#   - 30% of samples from classes [0,1,2,3,6,7,8,9] get wrong labels
#   - Classes [4,5] keep clean labels
```

### Evaluation Pools (3 pools)

Each run creates **3 evaluation pools** from held-out test data:

| Pool | Classes | Condition | Size |
|------|---------|-----------|------|
| **Clean** | Regular classes | Clean labels | `eval_per_group` samples |
| **Aleatoric-like** | Regular classes | Noisy labels | `eval_per_group` samples (if noise > 0) |
| **Epistemic-like** | Under-supported classes | Clean labels | `eval_per_group` samples (if under < regular) |

**Key insight:** In Fig. 3 sweeps (epistemic), aleatoric pool may be empty. In Fig. 4 sweeps (aleatoric), epistemic pool is small but fixed.

---

## 🔄 Complete Execution Flow

### PHASE 1: UI Layer - User Interaction

**File:** [`streamlit_app_progressive.py`](../streamlit_app_progressive.py:160-180)

```python
# User fills 5-step wizard
st.header("Step 1: Dataset")
dataset_name, noise_type = render_step1_dataset(workflow)

st.header("Step 2: Model & Training")
render_step2_training(workflow)

st.header("Step 3: Uncertainty Configuration")
render_step3_uncertainty(workflow)

st.header("Step 4: Evaluation")
render_step4_evaluation(workflow)

st.header("Step 5: Review & Launch")
render_step5_review(workflow)

# Launch cards with sweep preview
if st.button("🚀 Confirm Launch - Fig. 3 (Epistemic Sweep)"):
    result = launch_benchmark_primary(
        workflow,
        auto_start=True,
        highlight_callback=_set_highlight_experiment
    )
    render_launch_result(result)
```

**What happens:**
1. User configures dataset, model, uncertainty, evaluation
2. UI shows preview: "5 runs sweeping under_train_per_class: [25, 50, 100, 150, 200]"
3. User clicks "Confirm Launch"
4. UI calls orchestrator function

---

### PHASE 2: Orchestrator - Config Generation

**File:** [`src/uqlab_orchestrator/experiment_launcher.py`](../src/uqlab_orchestrator/experiment_launcher.py:89-120)

```python
def launch_workflow_experiments(workflow, *, auto_start, timestamp=None):
    """Generate sweep configs and submit to API."""
    
    # 1. Generate campaign timestamp
    if timestamp is None:
        timestamp = new_campaign_timestamp()  # e.g., "20260623_143000"
    
    # 2. Generate sweep configs
    sweep_axis, runs = generate_sweep_configs(workflow)
    # Returns: LaunchSweepAxis.EPISTEMIC_1D, [
    #   ("under_train", {config with under_train=25}),
    #   ("under_train", {config with under_train=50}),
    #   ...
    # ]
    
    # 3. Submit each run to API
    experiment_ids = []
    for sweep_kind, config_dict in runs:
        # Build experiment name
        name = f"epistemic_{timestamp}_{sweep_kind}_25"  # e.g., "epistemic_20260623_143000_under_train_25"
        
        # POST to API
        response = requests.post(
            f"{API_BASE_URL}/api/v1/experiments/no-auth",
            json={"name": name, "config": config_dict},
            headers=get_headers()
        )
        experiment_ids.append(response.json()["id"])
    
    return {
        "sweep_axis": sweep_axis,
        "experiment_ids": experiment_ids,
        "campaign_id": timestamp
    }
```

**File:** [`src/uqlab_orchestrator/run_spec.py`](../src/uqlab_orchestrator/run_spec.py:150-250)

```python
def generate_sweep_runs(workflow):
    """Generate list of (sweep_kind, config) tuples."""
    sweep_mode = workflow.get("sweep_config", {}).get("sweep_mode", "none")
    
    if sweep_mode == "epistemic":
        # Fig. 3: Sweep under_train_per_class
        values = workflow["sweep_config"]["epistemic_values"]  # [25, 50, 100, 150, 200]
        runs = []
        for val in values:
            # Clone workflow and override
            sweep_workflow = copy.deepcopy(workflow)
            sweep_workflow["uncertainty_config"]["under_train_per_class"] = val
            sweep_workflow["uncertainty_config"]["aleatoric_noise_percentage"] = 0  # FIXED
            
            # Build YAML config
            config = build_run_yaml(sweep_workflow)
            runs.append((f"under_train_{val}", config))
        return runs
    
    elif sweep_mode == "aleatoric":
        # Fig. 4: Sweep aleatoric_noise_percentage
        values = workflow["sweep_config"]["aleatoric_values"]  # [0, 25, 50, 75, 100]
        runs = []
        for val in values:
            sweep_workflow = copy.deepcopy(workflow)
            sweep_workflow["uncertainty_config"]["under_train_per_class"] = 30  # FIXED
            sweep_workflow["uncertainty_config"]["aleatoric_noise_percentage"] = val
            
            config = build_run_yaml(sweep_workflow)
            runs.append((f"noise_{val}", config))
        return runs
    
    else:
        # Single run (no sweep)
        config = build_run_yaml(workflow)
        return [("single", config)]

def build_run_yaml(workflow):
    """Transform workflow dict → nested ExperimentConfig YAML."""
    return {
        "data": {
            "dataset_name": workflow["dataset_config"]["dataset_name"],
            "noise_type": workflow["dataset_config"]["noise_type"],
            "under_supported_classes": parse_under_supported(workflow["uncertainty_config"]["under_supported"]),
            "under_train_per_class": workflow["uncertainty_config"]["under_train_per_class"],
            "regular_train_per_class": workflow["uncertainty_config"]["regular_train_per_class"],
            "aleatoric_noise_percentage": workflow["uncertainty_config"].get("aleatoric_noise_percentage", 0),
            "eval_per_group": workflow["evaluation_config"]["eval_per_group"],
        },
        "model": {
            "architecture": f"{workflow['training_config']['model_architecture']}_mcdropout",
            "dropout": workflow["training_config"].get("dropout", 0.3),
            "hidden_dim": workflow["training_config"].get("hidden_dim", 256),
        },
        "training": {
            "epochs": workflow["training_config"]["epochs"],
            "learning_rate": workflow["training_config"]["learning_rate"],
            "batch_size": workflow["training_config"]["batch_size"],
        },
        "evaluation": {
            "mc_passes": workflow["evaluation_config"]["mc_passes"],
            "signals": workflow["evaluation_config"]["signals"],
        },
        "seed": 42,
        "device": "auto"
    }
```

---

### PHASE 3: API Layer - Database & Job Management

**File:** [`backend/app/api/routes/experiments.py`](../backend/app/api/routes/experiments.py:90-120)

```python
@router.post("/no-auth")
async def create_experiment_no_auth(experiment: ExperimentCreate, session: SessionDep):
    """Create experiment in database and optionally start training."""
    
    # 1. Create DB record
    db_experiment = UncertaintyExperiment(
        id=uuid.uuid4(),
        name=experiment.name,  # e.g., "epistemic_20260623_143000_under_train_25"
        config_yaml=experiment.config,  # Nested YAML dict
        status=JobStatus.PENDING,
        progress=0.0,
        created_at=datetime.utcnow(),
        user_id=get_or_create_test_user(session).id
    )
    session.add(db_experiment)
    session.commit()
    session.refresh(db_experiment)
    
    # 2. Start training asynchronously
    orchestrator = get_orchestrator(session)
    await orchestrator.start_training(db_experiment.id)
    
    # 3. Return response
    return ExperimentResponse(
        id=db_experiment.id,
        name=db_experiment.name,
        status=db_experiment.status,
        progress=db_experiment.progress,
        created_at=db_experiment.created_at,
        # ... other fields
    )
```

    )
    
    # 2. Sample training data (FINALLY!)
    train_indices = sample_indices_for_fast_pilot(
        dataset,
        under_supported_classes=config.data.under_supported_classes,  # ← [0, 1]
        under_train_per_class=config.data.under_train_per_class,      # ← 50
        regular_train_per_class=config.data.regular_train_per_class,  # ← 300
        seed=seed
    )
    
    # 3. Apply label noise
    if config.data.aleatoric_noise_percentage > 0:
        # Flip labels for "regular" classes only
        # But which are regular? Classes NOT in under_supported_classes!
        regular_classes = [c for c in range(10) if c not in config.data.under_supported_classes]
        # Apply noise to samples from regular_classes...
        # (Complex logic here)
    
    # 4. Build model
    model = build_model(config.model, num_classes=10)
    
    # 5. Train
    train_model(model, train_loader, config.training)
    
    # 6. Evaluate with MC Dropout
    signal_table = evaluate_with_mc_dropout(
        model,
        eval_loader,
        mc_passes=config.evaluation.mc_passes,
        signals=config.evaluation.signals
    )
    
    # 7. Write artifacts
    write_artifacts(results_dir, signal_table, config)
    
    return summary
```

**Problem:** The actual sampling logic is buried deep and depends on implicit rules!

### PHASE 6: Artifacts Written

**Directory structure:**
```
results/exp_20260622_143000/
├── config.yaml              # Copy of input config
├── experiment.log           # Full stdout/stderr
├── summary.json             # AUROC scores, eval sizes
├── per_sample_signals.csv   # One row per eval sample
└── results.pt               # PyTorch tensors (signal_table, predictions)
```

**File:** [`src/uqlab/run_artifacts.py`](../src/uqlab/run_artifacts.py)

```python
@dataclass
class RunArtifacts:
    """Normalized view of experiment outputs."""
    run_dir: Path
    summary_path: Path | None
    results_pt_path: Path | None
    eval_sizes: dict[str, int]           # {"clean": 100, "aleatoric": 200, ...}
    one_vs_rest_auroc: list[dict]        # [{"signal": "entropy", "aleatoric_auroc": 0.75, ...}]
    
    def auroc_by_signal(self) -> dict[str, dict[str, float]]:
        """Extract AUROC scores per signal."""
        return {
            "predictive_entropy": {"aleatoric": 0.75, "epistemic": 0.82},
            "mutual_info": {"aleatoric": 0.68, "epistemic": 0.88},
            # ...
        }
```

### PHASE 7: UI Polling & Visualization

**File:** [`src/uqlab/ui_components/results/experiment_results_panel.py`](../src/uqlab/ui_components/results/experiment_results_panel.py)

```python
def render_progressive_results_section(api_base_url, get_headers_func):
    """Poll API every 5s and render results."""
    
    # 1. Fetch experiments from API
    response = requests.get(f"{api_base_url}/api/v1/experiments/no-auth")
    experiments = response.json()
    
    # 2. Group by sweep (if applicable)
    groups = group_experiments_intelligently(experiments)
    
    # 3. For each experiment, render results
    for exp in experiments:
        if exp["status"] == "completed":
            # Load artifacts
            artifacts = load_run_directory(exp["results_path"])
            
            # Render AUROC table
            auroc_scores = artifacts.auroc_by_signal()
            st.dataframe(auroc_scores)
            
            # Render signal plots
            if artifacts.per_sample_path:
                df = pd.read_csv(artifacts.per_sample_path)
                plot_signal_distributions(df)
```

---

## 🎯 Proposed Simplified Flow

### New Config Structure

```yaml
# config.yaml (EXPLICIT per-class)
data:
  dataset_name: cifar10n
  noise_type: worse_label
  
  # EXPLICIT per-class configuration
  class_configs:
    - class_id: 0
      train_samples: 50
      label_noise_pct: 0
    - class_id: 1
      train_samples: 50
      label_noise_pct: 0
    - class_id: 2
      train_samples: 300
      label_noise_pct: 30
    - class_id: 3
      train_samples: 300
      label_noise_pct: 30
    - class_id: 4
      train_samples: 300
      label_noise_pct: 30
    - class_id: 5
      train_samples: 300
      label_noise_pct: 30
    - class_id: 6
      train_samples: 300
      label_noise_pct: 30
    - class_id: 7
      train_samples: 300
      label_noise_pct: 30
    - class_id: 8
      train_samples: 300
      label_noise_pct: 30
    - class_id: 9
      train_samples: 300
      label_noise_pct: 30

model:
  architecture: resnet18_mcdropout
  dropout: 0.3

training:
  epochs: 12
  learning_rate: 0.001

evaluation:
  mc_passes: 20
  signals: [predictive_entropy, mutual_info]
```

### Validation

```python
def validate_class_configs(class_configs, dataset):
    """Validate that requested samples are available."""
    for cfg in class_configs:
        class_id = cfg["class_id"]
        requested = cfg["train_samples"]
        available = len(dataset.get_class_indices(class_id))
        
        if requested > available:
            raise ValueError(
                f"Class {class_id}: requested {requested} samples "
                f"but only {available} available"
            )
        
        if cfg["label_noise_pct"] < 0 or cfg["label_noise_pct"] > 100:
            raise ValueError(
                f"Class {class_id}: noise_pct must be 0-100, "
                f"got {cfg['label_noise_pct']}"
            )
```

### Sampling Logic (SIMPLE!)

```python
def sample_training_data(dataset, class_configs, seed):
    """Sample exactly what config specifies."""
    rng = np.random.RandomState(seed)
    train_indices = []
    
    for cfg in class_configs:
        class_id = cfg["class_id"]
        n_samples = cfg["train_samples"]
        noise_pct = cfg["label_noise_pct"]
        
        # Get all indices for this class
        class_indices = dataset.get_class_indices(class_id)
        
        # Sample requested number
        sampled = rng.choice(class_indices, size=n_samples, replace=False)
        
        # Apply label noise
        if noise_pct > 0:
            n_flip = int(n_samples * noise_pct / 100)
            flip_indices = rng.choice(len(sampled), size=n_flip, replace=False)
            for idx in flip_indices:
                # Flip to random wrong class
                wrong_classes = [c for c in range(10) if c != class_id]
                dataset.labels[sampled[idx]] = rng.choice(wrong_classes)
        
        train_indices.extend(sampled)
    
    return train_indices
```

**Benefits:**
- ✅ No hidden transformations
- ✅ Exact reproducibility
- ✅ Easy to debug
- ✅ Clear validation errors
- ✅ Matches paper methodology exactly

---

## 📋 Summary

**Current system:** 5+ transformation layers, implicit rules, unpredictable results

**Proposed system:** 1 explicit config → 1 deterministic result

**Next steps:**
1. Add `class_configs` to `ExperimentConfig.data`
2. Update UI to generate explicit configs
3. Simplify sampling logic
4. Remove `under_supported`, `under_train_per_class`, etc.
5. Update documentation

**Migration:** Keep old config format working, add new format, deprecate old over time.

---

## 🔗 Key Files Reference

| Layer | File | Purpose |
|-------|------|---------|
| UI | `streamlit_app_progressive.py` | User interaction |
| Orchestrator | `src/uqlab_orchestrator/experiment_launcher.py` | API calls |
| Orchestrator | `src/uqlab_orchestrator/run_spec.py` | Config transformation |
| API | `backend/app/api/routes/experiments.py` | HTTP endpoints |
| Execution | `backend/app/services/training_orchestrator.py` | Job management |
| Execution | `backend/app/services/executors/direct_executor.py` | Pipeline invocation |
| ML | `src/uqlab/runner/pipeline.py` | Entry point |
| ML | `src/uqlab/runner/fast_pilot_core.py` | Core logic |
| Artifacts | `src/uqlab/run_artifacts.py` | Result loading |
| Visualization | `src/uqlab/ui_components/results/` | Charts & tables |