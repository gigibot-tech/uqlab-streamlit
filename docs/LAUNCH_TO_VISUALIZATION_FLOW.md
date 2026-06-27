# Launch to Visualization Flow

Complete UX and code execution path from "Confirm Launch" button to results visualization.

**Context:** This documents the CURRENT paper sweep implementation. See [`PAPER_SWEEPS_VS_FOUR_REGION_EXPLAINED.md`](../PAPER_SWEEPS_VS_FOUR_REGION_EXPLAINED.md) for experimental design details.

---

## 🎯 Simple Mental Model

```text
USER CLICKS "Confirm Launch"
  ↓
UI collects workflow dict (Steps 1-5)
  ↓
Orchestrator validates & builds YAML configs
  ↓
API creates DB records (one per sweep point)
  ↓
Executor runs pipeline.run() for each
  ↓
Pipeline writes artifacts to disk
  ↓
UI polls API & loads artifacts
  ↓
UI renders charts & tables
```

---

## 📋 Current Config Flow (Paper Sweeps)

### What User Sees in UI

```python
# Step 3: Uncertainty Configuration
under_supported = "0,1"           # Which classes get sparse training
under_train_per_class = 50        # Samples per sparse class
regular_train_per_class = 300     # Samples per regular class

# Step 3: Aleatoric Configuration  
aleatoric_noise_percentage = 30   # Label flip % for regular classes
```

### What Actually Happens

**For a single experiment:**
- Classes 0-1: Get 50 samples each, clean labels
- Classes 2-9: Get 300 samples each, 30% noisy labels

**For Fig. 3 sweep (epistemic):**
- 5 runs varying `under_train_per_class`: [25, 50, 100, 150, 200]
- Fixed `aleatoric_noise_percentage`: 0

**For Fig. 4 sweep (aleatoric):**
- 5 runs varying `aleatoric_noise_percentage`: [0, 25, 50, 75, 100]
- Fixed `under_train_per_class`: 30

---

## 🔍 Detailed Flow (7 Phases)

### PHASE 1: UI Collection (Streamlit)

**File:** [`streamlit_app_progressive.py`](../streamlit_app_progressive.py:100-200)

```python
# User fills 5-step wizard
workflow = {
    "dataset_config": {
        "dataset_name": "cifar10n",
        "noise_type": "worse_label"
    },
    "uncertainty_config": {
        "under_supported": "0,1",
        "under_train_per_class": 50,
        "regular_train_per_class": 300,
    },
    "training_config": {
        "model_architecture": "resnet18",
        "epochs": 12,
        "learning_rate": 0.001,
    },
    "evaluation_config": {
        "mc_passes": 20,
        "signals": ["predictive_entropy", "mutual_info"],
        "eval_per_group": 100
    }
}

# User clicks "🚀 Confirm Launch"
result = launch_workflow_experiments(
    workflow,
    auto_start=True,
    highlight_callback=_set_highlight_experiment
)
```

**Key Point:** `workflow` is a flat dict with UI-friendly keys. It gets transformed into nested YAML.

---

### PHASE 2: Config Generation (Orchestrator)

**File:** [`src/uqlab_orchestrator/experiment_launcher.py`](../src/uqlab_orchestrator/experiment_launcher.py:89-120)

```python
def launch_workflow_experiments(workflow, *, auto_start):
    # 1. Determine sweep type
    sweep_axis, runs = generate_sweep_configs(workflow)
    # Returns: LaunchSweepAxis.EPISTEMIC_1D or ALEATORIC_1D or SINGLE_POINT
    
    # 2. For each sweep point, build YAML
    experiments = []
    for sweep_kind, config_dict in runs:
        yaml_config = build_run_yaml(workflow, sweep_point=config_dict)
        
        # 3. POST to API
        response = requests.post(
            f"{API_BASE_URL}/api/v1/experiments/no-auth",
            json={
                "name": f"exp_{timestamp}_{sweep_kind}_{value}",
                "config": yaml_config
            }
        )
        experiments.append(response.json())
    
    return {"experiments": experiments, "sweep_axis": sweep_axis}
```

**File:** [`src/uqlab_orchestrator/run_spec.py`](../src/uqlab_orchestrator/run_spec.py:100-200)

```python
def build_run_yaml(workflow: Dict) -> Dict:
    """Transform UI workflow → nested ExperimentConfig YAML."""
    
    # Parse under_supported
    under_supported = workflow["uncertainty_config"]["under_supported"]
    if under_supported.startswith("random:"):
        num = int(under_supported.split(":")[1])
        under_classes = list(range(num))  # Will be randomized at runtime
    else:
        under_classes = [int(x) for x in under_supported.split(",")]
    
    # Build nested structure
    return {
        "data": {
            "dataset_name": workflow["dataset_config"]["dataset_name"],
            "noise_type": workflow["dataset_config"]["noise_type"],
            "under_supported_classes": under_classes,
            "under_train_per_class": workflow["uncertainty_config"]["under_train_per_class"],
            "regular_train_per_class": workflow["uncertainty_config"]["regular_train_per_class"],
            "aleatoric_noise_percentage": workflow.get("aleatoric_noise_percentage", 0),
        },
        "model": {
            "architecture": f"{workflow['training_config']['model_architecture']}_mcdropout",
            "dropout": 0.3,
            "hidden_dim": 256,
        },
        "training": {
            "epochs": workflow["training_config"]["epochs"],
            "learning_rate": workflow["training_config"]["learning_rate"],
            "batch_size": 256,
        },
        "evaluation": {
            "mc_passes": workflow["evaluation_config"]["mc_passes"],
            "signals": workflow["evaluation_config"]["signals"],
            "eval_per_group": workflow["evaluation_config"]["eval_per_group"],
        },
        "seed": 42,
        "device": "auto"
    }
```

**Key Point:** Transformation from flat `workflow` to nested `ExperimentConfig` YAML happens here.

---

### PHASE 3: API Layer (FastAPI)

**File:** [`backend/app/api/routes/experiments.py`](../backend/app/api/routes/experiments.py:90-120)

```python
@router.post("/no-auth")
async def create_experiment_no_auth(experiment: ExperimentCreate, session: SessionDep):
    # 1. Create DB record
    db_experiment = UncertaintyExperiment(
        id=uuid.uuid4(),
        name=experiment.name,
        config_yaml=experiment.config,  # Store nested YAML
        status=JobStatus.PENDING,
        progress=0.0,
        created_at=datetime.utcnow()
    )
    session.add(db_experiment)
    session.commit()
    
    # 2. Start training asynchronously
    orchestrator = get_orchestrator(session)
    await orchestrator.start_training(db_experiment.id)
    
    return ExperimentResponse(
        id=db_experiment.id,
        name=db_experiment.name,
        status=db_experiment.status,
        progress=0.0
    )
```

**Key Point:** Each sweep point gets its own DB record and runs independently.

---

### PHASE 4: Execution Orchestration

**File:** [`backend/app/services/training_orchestrator.py`](../backend/app/services/training_orchestrator.py:32-100)

```python
class TrainingOrchestrator:
    async def _run_training(self, experiment_id: UUID):
        # 1. Load config from DB
        experiment = repo.get(experiment_id)
        config_yaml = experiment.config_yaml
        
        # 2. Write YAML to disk
        config_path = results_dir / "config.yaml"
        output_dir = results_dir / experiment.name
        with open(config_path, 'w') as f:
            yaml.dump(config_yaml, f)
        
        # 3. Execute via DirectExecutor
        def progress_callback(update: ProgressUpdate):
            # Update DB
            repo.update_status(experiment_id, JobStatus.RUNNING, update.progress)
            # Broadcast via WebSocket
            broadcast_progress(str(experiment_id), update.dict())
        
        result = await self.executor.execute(
            config_path,
            output_dir,
            progress_callback
        )
        
        # 4. Update DB with results
        repo.update_status(experiment_id, JobStatus.COMPLETED, 1.0)
        repo.update_results(experiment_id, result)
```

**File:** [`backend/app/services/executors/direct_executor.py`](../backend/app/services/executors/direct_executor.py:69-120)

```python
class DirectExecutor:
    async def execute(self, config_path, output_dir, progress_callback):
        # Import canonical runner
        from uqlab.runner.execute import run_from_yaml as pipeline_run
        
        # Run in thread pool (non-blocking)
        result = await asyncio.to_thread(
            pipeline_run,
            config_path,
            output_dir,
            progress_callback=progress_callback
        )
        return result
```

**Key Point:** Executor calls the canonical ML pipeline in a thread pool.

---

### PHASE 5: ML Pipeline Execution

**File:** [`src/uqlab/runner/execute.py`](../src/uqlab/runner/execute.py)

```python
def run(config_path: Path, output_dir: Path, progress_callback=None):
    """Single entry point for all experiment execution."""
    
    # 1. Load & validate config
    config = ExperimentConfig.from_yaml(config_path)
    validate_config(config)
    
    # 2. Execute core logic
    summary = run_experiment_core(
        config,
        output_dir,
        seed=config.seed or 42,
        device_str=config.device or "auto",
        progress_callback=progress_callback
    )
    
    return summary
```

**File:** [`src/uqlab/runner/experiment_core.py`](../src/uqlab/runner/experiment_core.py)

```python
def run_experiment_core(config, results_dir, seed, device_str, progress_callback=None):
    """The actual ML experiment logic."""
    
    # 1. Load dataset
    dataset = load_classification_dataset(
        config.data.dataset_name,
        config.data.noise_type
    )
    
    # 2. Sample training data
    train_indices = sample_indices_for_fast_pilot(
        dataset,
        under_supported_classes=config.data.under_supported_classes,  # [0, 1]
        under_train_per_class=config.data.under_train_per_class,      # 50
        regular_train_per_class=config.data.regular_train_per_class,  # 300
        seed=seed
    )
    # Result: 2*50 + 8*300 = 2,500 training samples
    
    # 3. Apply label noise to regular classes
    if config.data.aleatoric_noise_percentage > 0:
        regular_classes = [c for c in range(10) if c not in config.data.under_supported_classes]
        # Flip labels for samples from classes 2-9
        apply_label_noise(train_indices, regular_classes, config.data.aleatoric_noise_percentage)
    
    # 4. Build model
    model = build_model(config.model, num_classes=10)
    
    # 5. Train
    if progress_callback:
        progress_callback(ProgressUpdate(stage="training", progress=0.2))
    
    train_model(model, train_loader, config.training, progress_callback)
    
    # 6. Evaluate with MC Dropout
    if progress_callback:
        progress_callback(ProgressUpdate(stage="evaluation", progress=0.8))
    
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

**Key Point:** This is where actual training and evaluation happens.

---

### PHASE 6: Artifacts Written

**Directory structure:**
```
results/exp_20260622_143000_epistemic_50/
├── config.yaml              # Copy of input config
├── experiment.log           # Full stdout/stderr
├── summary.json             # AUROC scores, eval sizes
├── per_sample_signals.csv   # One row per eval sample
└── results.pt               # PyTorch tensors
```

**File:** [`src/uqlab/run_artifacts.py`](../src/uqlab/run_artifacts.py:65-100)

```python
@dataclass
class RunArtifacts:
    """Normalized view of experiment outputs."""
    run_dir: Path
    summary_path: Path | None
    results_pt_path: Path | None
    per_sample_path: Path | None
    
    # Parsed from summary.json
    eval_sizes: dict[str, int]           # {"clean": 100, "aleatoric": 200, "epistemic": 100}
    one_vs_rest_auroc: list[dict]        # [{"signal": "entropy", "aleatoric_auroc": 0.75, ...}]
    
    def auroc_by_signal(self) -> dict[str, dict[str, float]]:
        """Extract AUROC scores per signal."""
        return {
            "predictive_entropy": {
                "aleatoric": 0.75,
                "epistemic": 0.82
            },
            "mutual_info": {
                "aleatoric": 0.68,
                "epistemic": 0.88
            },
            # ... all enabled signals
        }
```

**Key Point:** Artifacts are the source of truth for visualization.

---

### PHASE 7: UI Polling & Visualization

**File:** [`src/uqlab/ui_components/results/experiment_results_panel.py`](../src/uqlab/ui_components/results/experiment_results_panel.py:40-100)

```python
def render_progressive_results_section(api_base_url, get_headers_func):
    """Poll API every 5s and render results."""
    
    # 1. Fetch all experiments
    response = requests.get(f"{api_base_url}/api/v1/experiments/no-auth")
    experiments = response.json()
    
    # 2. Group by sweep (name-based detection)
    groups = group_experiments_intelligently(experiments)
    # Detects patterns like: exp_20260622_143000_epistemic_25, _50, _100, etc.
    
    # 3. For each group, render sweep summary
    for group in groups:
        with st.expander(f"📊 {group['campaign_name']} ({group['n_runs']} runs)"):
            # Show sweep parameter and values
            st.markdown(f"**Swept:** {group['swept_parameter']}")
            st.markdown(f"**Values:** {', '.join(map(str, group['sweep_values']))}")
            
            # For each experiment in group
            for exp in group['experiments']:
                if exp["status"] == "completed":
                    # Load artifacts
                    artifacts = load_run_directory(exp["results_path"])
                    
                    # Render AUROC table
                    auroc_scores = artifacts.auroc_by_signal()
                    st.dataframe(pd.DataFrame(auroc_scores).T)
                    
                    # Render signal distributions
                    if artifacts.per_sample_path:
                        df = pd.read_csv(artifacts.per_sample_path)
                        plot_signal_distributions(df)
```

**Key Point:** UI polls API, loads artifacts from disk, renders charts.

---

## 📊 Data Artifacts Used in Visualization

### 1. `summary.json`

```json
{
  "eval_sizes": {
    "clean": 100,
    "aleatoric_like": 200,
    "epistemic_like": 100
  },
  "one_vs_rest_auroc": [
    {
      "signal": "predictive_entropy",
      "aleatoric_auroc": 0.7523,
      "epistemic_auroc": 0.8234
    },
    {
      "signal": "mutual_info",
      "aleatoric_auroc": 0.6812,
      "epistemic_auroc": 0.8756
    }
  ],
  "train_size": 2500,
  "config_snapshot": { ... }
}
```

**Used for:** AUROC tables, eval pool sizes, quick metrics

### 2. `per_sample_signals.csv`

```csv
group,dataset_index,clean_label,noisy_label,is_noisy,predictive_entropy,mutual_info,...
0,1234,3,3,False,0.234,0.123,...
1,5678,7,2,True,0.876,0.654,...
2,9012,4,4,False,0.456,0.789,...
```

**Used for:** Signal distribution plots, per-sample analysis

### 3. `results.pt`

```python
{
    "signal_table": {
        "predictive_entropy": tensor([0.234, 0.876, ...]),  # Per-sample
        "mutual_info": tensor([0.123, 0.654, ...]),
        # ... all enabled signals
    },
    "predictions": tensor([[0.1, 0.2, ...], ...]),  # Softmax outputs
    "eval_packs": {
        "clean": {...},
        "aleatoric": {...},
        "epistemic": {...}
    }
}
```

**Used for:** Advanced analysis, re-computation, debugging

---

## 🔗 Key Files Reference

| Phase | File | Purpose |
|-------|------|---------|
| 1. UI | `streamlit_app_progressive.py` | Collect workflow dict |
| 2. Orchestrator | `src/uqlab_orchestrator/experiment_launcher.py` | API calls |
| 2. Orchestrator | `src/uqlab_orchestrator/run_spec.py` | Workflow → YAML |
| 3. API | `backend/app/api/routes/experiments.py` | HTTP endpoints |
| 4. Execution | `backend/app/services/training_orchestrator.py` | Job management |
| 4. Execution | `backend/app/services/executors/direct_executor.py` | Pipeline invocation |
| 5. ML | `src/uqlab/runner/execute.py` | Entry point |
| 5. ML | `src/uqlab/runner/experiment_core.py` | Core training/eval |
| 6. Artifacts | `src/uqlab/run_artifacts.py` | Result loading |
| 7. Visualization | `src/uqlab/ui_components/results/` | Charts & tables |

---

## 🎯 Summary

---

### PHASE 5: Artifacts Written to Disk

**Directory structure:**
```
results/
└── <experiment_id>/
    ├── config.yaml              # Input config (copy)
    ├── experiment.log           # Full stdout/stderr
    ├── summary.json             # AUROC scores + eval sizes
    ├── per_sample_signals.csv   # Flat table (one row per eval sample)
    └── results.pt               # PyTorch checkpoint
```

**`summary.json` example:**
```json
{
  "eval_sizes": {
    "clean": 100,
    "aleatoric_like": 100,
    "epistemic_like": 100
  },
  "one_vs_rest_auroc": [
    {
      "signal": "predictive_entropy",
      "aleatoric_auroc": 0.7523,
      "epistemic_auroc": 0.8234
    },
    {
      "signal": "mutual_info",
      "aleatoric_auroc": 0.6812,
      "epistemic_auroc": 0.8756
    }
  ],
  "train_size": 2500,
  "config": { ... }
}
```

**`per_sample_signals.csv` example:**
```csv
group,dataset_index,clean_label,noisy_label,is_noisy,predictive_entropy,mutual_info
0,1234,3,3,False,0.523,0.234
0,5678,7,7,False,0.312,0.156
1,2345,2,8,True,0.876,0.543
1,6789,4,1,True,0.923,0.678
2,3456,4,4,False,0.734,0.456
2,7890,5,5,False,0.812,0.523
```

**`results.pt` structure:**
```python
{
    "signal_table": {
        "predictive_entropy": tensor([...]),  # Shape: (300,)
        "mutual_info": tensor([...]),
        "group_labels": tensor([...]),
        "clean_labels": tensor([...]),
        "is_noisy": tensor([...]),
    },
    "mc_predictions": tensor([...]),  # Shape: (20, 300, 10) - MC passes × samples × classes
    "eval_packs": {
        "clean": {...},
        "aleatoric": {...},
        "epistemic": {...}
    },
    "metadata": {
        "mc_passes": 20,
        "signals": ["predictive_entropy", "mutual_info"],
        "timestamp": "2026-06-23T14:30:00"
    }
}
```

---

### PHASE 6: UI Polling & Visualization

**File:** [`src/uqlab/ui_components/results/experiment_results_panel.py`](../src/uqlab/ui_components/results/experiment_results_panel.py:40-150)

```python
def render_progressive_results_section(api_base_url, get_headers_func):
    """Poll API and render results with auto-refresh."""
    
    # 1. Fetch experiments from API
    response = requests.get(
        f"{api_base_url}/api/v1/experiments/no-auth",
        headers=get_headers_func()
    )
    experiments = response.json()
    
    # 2. Group by sweep campaign
    groups = group_experiments_intelligently(experiments)
    # groups = {
    #     "epistemic_20260623_143000": [exp1, exp2, exp3, exp4, exp5],
    #     "standalone": [exp6, exp7]
    # }
    
    # 3. Render each group
    for campaign_id, exps in groups.items():
        if campaign_id != "standalone":
            # Sweep group
            with st.expander(f"📊 {campaign_id} ({len(exps)} runs)", expanded=False):
                render_sweep_group_summary(exps, api_base_url)
        else:
            # Standalone experiments
            with st.expander(f"📋 Standalone Experiments ({len(exps)})", expanded=False):
                for exp in exps:
                    render_single_experiment(exp, api_base_url)
    
    # 4. Auto-refresh if any running
    has_running = any(exp["status"] in ["pending", "running"] for exp in experiments)
    if has_running:
        st.caption("🔄 Auto-refresh every 5s while experiments are running")
        time.sleep(5)
        st.rerun()

def render_sweep_group_summary(experiments, api_base_url):
    """Render AUROC table and line plots for sweep group."""
    
    # 1. Load artifacts for completed experiments
    results = []
    for exp in experiments:
        if exp["status"] == "completed":
            artifacts = load_run_directory(exp["results_path"])
            results.append({
                "name": exp["name"],
                "swept_value": extract_swept_value(exp["name"]),  # e.g., 25, 50, 100
                "auroc_scores": artifacts.auroc_by_signal(),
                "eval_sizes": artifacts.eval_sizes
            })
    
    # 2. Render AUROC table
    st.subheader("AUROC Scores")
    df = pd.DataFrame([
        {
            "Swept Value": r["swept_value"],
            "Predictive Entropy (Aleatoric)": r["auroc_scores"]["predictive_entropy"]["aleatoric"],
            "Predictive Entropy (Epistemic)": r["auroc_scores"]["predictive_entropy"]["epistemic"],
