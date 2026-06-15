# Streamlit Architecture - Clarified Design

## Your Vision (Concretized)

> "I think it would be actually not bad if most things are just for config creation, and for every type of experiment we have a file or smth and then the run_fast_ script is ran, is good for readability"

**YES! This is the right approach.** Here's the concrete architecture:

## Folder Structure & Responsibilities

```
walaris-cen/
├── src/uqlab/
│   ├── 6_ui/                    # UI Layer (Streamlit apps)
│   │   ├── api_client.py        # ✅ HTTP communication only
│   │   ├── sweep_planner.py     # ✅ Config generation only
│   │   ├── experiment_builder.py # Config creation UI
│   │   ├── batch_builder.py     # Batch config creation UI
│   │   ├── results_viewer.py    # Results display only
│   │   ├── signal_viewer.py     # Signal plots only
│   │   ├── correlation_viz.py   # Correlation plots only
│   │   └── visualizations.py    # ✅ VIZ COMPONENTS HERE
│   │
│   ├── 7_orchestration/         # Execution Layer
│   │   ├── experiment_runner.py # Runs experiments (calls scripts)
│   │   ├── batch_runner.py      # Runs batches
│   │   └── storage.py           # Saves results
│   │
│   └── ui_components/           # Shared UI components
│       ├── signal_sweep_paper_viz.py  # ✅ Paper-style plots
│       ├── per_sample_signals_viz.py  # ✅ Per-sample viz
│       └── smart_experiment_selector.py # ✅ Experiment selector
│
├── scripts/
│   ├── run_fast_uncertainty_classification.py  # ✅ MAIN EXECUTOR
│   ├── run_epistemic_sweep.py                  # Epistemic-specific
│   ├── run_aleatoric_sweep.py                  # Aleatoric-specific
│   └── run_2d_grid_sweep.py                    # 2D grid-specific
│
└── streamlit_app_progressive.py  # Main UI entry point
```

## Clear Separation of Concerns

### 1. UI Layer (6_ui/) - CONFIG CREATION ONLY ✅

**Purpose**: Build experiment configurations, NO execution

**What it does**:
- Render forms for user input
- Validate inputs
- Generate config dicts/JSON
- Display results (read-only)
- Show visualizations

**What it does NOT do**:
- ❌ Train models
- ❌ Load datasets
- ❌ Compute metrics
- ❌ Run experiments directly

**Example** (`6_ui/experiment_builder.py`):
```python
def build_epistemic_experiment_config():
    """Build config for epistemic uncertainty experiment"""
    st.header("Epistemic Uncertainty Experiment")
    
    # User inputs
    under_train = st.slider("Under-supported samples", 25, 500, 50)
    regular_train = st.slider("Regular samples", 100, 1000, 300)
    
    # Build config (NO EXECUTION)
    config = {
        "experiment_type": "epistemic",
        "under_train_per_class": under_train,
        "regular_train_per_class": regular_train,
        "noise_type": "clean_label",  # Fixed for epistemic
        ...
    }
    
    # Save config to file or send to API
    if st.button("Create Experiment"):
        save_config(config, "epistemic_exp.json")
        st.success("Config saved! Run with: python scripts/run_epistemic_sweep.py")
    
    return config
```

### 2. Visualization (6_ui/visualizations.py + ui_components/) ✅

**Purpose**: Display results, NO computation

**What it does**:
- Load results from disk/API
- Render plots (matplotlib, plotly)
- Show tables (pandas)
- Interactive widgets

**What it does NOT do**:
- ❌ Compute metrics
- ❌ Train models
- ❌ Process data

**Files**:
- `6_ui/visualizations.py` - Generic viz utilities
- `6_ui/signal_viewer.py` - Signal-specific plots
- `6_ui/correlation_viz.py` - Correlation matrices
- `ui_components/signal_sweep_paper_viz.py` - Paper Figure 3/4 style
- `ui_components/per_sample_signals_viz.py` - Per-sample analysis

### 3. Execution Layer (scripts/) - ONE SCRIPT PER EXPERIMENT TYPE ✅

**Purpose**: Execute experiments, compute metrics, save results

**Your idea concretized**:

#### `scripts/run_epistemic_sweep.py`
```python
"""
Epistemic Uncertainty Sweep
Varies dataset size, fixes noise at 0%
"""

def main():
    # Load config
    config = load_config("epistemic_exp.json")
    
    # Sweep dataset sizes
    for size in [25, 50, 100, 150, 200]:
        config["under_train_per_class"] = size
        
        # Run experiment
        results = run_experiment(config)
        
        # Save results
        save_results(results, f"epistemic_{size}.json")

if __name__ == "__main__":
    main()
```

#### `scripts/run_aleatoric_sweep.py`
```python
"""
Aleatoric Uncertainty Sweep
Varies label noise, fixes dataset size
"""

def main():
    config = load_config("aleatoric_exp.json")
    
    # Sweep noise levels
    for noise in [0, 25, 50, 75, 100]:
        config["aleatoric_noise_percentage"] = noise
        
        results = run_experiment(config)
        save_results(results, f"aleatoric_{noise}.json")

if __name__ == "__main__":
    main()
```

#### `scripts/run_2d_grid_sweep.py`
```python
"""
2D Grid Sweep
Varies both dataset size AND label noise
"""

def main():
    config = load_config("2d_grid_exp.json")
    
    # 2D sweep
    for size in [25, 50, 100, 150, 200]:
        for noise in [0, 25, 50, 75, 100]:
            config["under_train_per_class"] = size
            config["aleatoric_noise_percentage"] = noise
            
            results = run_experiment(config)
            save_results(results, f"grid_{size}_{noise}.json")

if __name__ == "__main__":
    main()
```

### 4. Orchestration (7_orchestration/) - COORDINATES SCRIPTS ✅

**Purpose**: Manage script execution, handle errors, track progress

**What it does**:
- Call scripts with configs
- Monitor progress
- Handle failures
- Aggregate results

**Example** (`7_orchestration/experiment_runner.py`):
```python
class ExperimentRunner:
    """Runs experiment scripts and tracks progress"""
    
    def run_epistemic_sweep(self, config: Dict) -> List[Dict]:
        """Run epistemic sweep by calling script"""
        # Save config
        config_path = save_temp_config(config)
        
        # Call script
        result = subprocess.run([
            "python", "scripts/run_epistemic_sweep.py",
            "--config", config_path
        ], capture_output=True)
        
        # Load results
        return load_results("results/epistemic_*.json")
```

## State Management - ONLY FOR CONFIG ✅

**You're right!** State management should ONLY track:
1. **Config creation progress** (Step 1/4 complete, etc.)
2. **User inputs** (form values, selections)
3. **UI state** (expanded sections, selected tabs)

**NOT for**:
- ❌ Training progress (that's in the script)
- ❌ Metric computation (that's in the script)
- ❌ Data loading (that's in the script)

**Example** (Streamlit session state):
```python
# ✅ GOOD - Config state
st.session_state.config = {
    "dataset_selected": True,
    "model_configured": True,
    "sweep_planned": False,
    "current_config": {...}
}

# ❌ BAD - Execution state (belongs in script)
st.session_state.training_progress = 0.75  # NO!
st.session_state.current_epoch = 8  # NO!
st.session_state.loaded_data = dataset  # NO!
```

## Complete Workflow

### User Journey

```
1. Open Streamlit App
   ↓
2. Select Experiment Type
   ├─ Epistemic Sweep
   ├─ Aleatoric Sweep
   └─ 2D Grid Sweep
   ↓
3. Configure Parameters (UI forms)
   ├─ Dataset settings
   ├─ Model architecture
   ├─ Training params
   └─ Sweep ranges
   ↓
4. Generate Config (JSON file)
   ↓
5. Click "Run Experiment"
   ↓
6. Streamlit calls appropriate script:
   ├─ run_epistemic_sweep.py
   ├─ run_aleatoric_sweep.py
   └─ run_2d_grid_sweep.py
   ↓
7. Script executes (shows progress)
   ↓
8. Results saved to disk
   ↓
9. Streamlit loads & visualizes results
```

### Code Flow

```python
# streamlit_app_progressive.py
def main():
    # Step 1: Config Creation
    exp_type = st.selectbox("Experiment Type", [
        "Epistemic Sweep",
        "Aleatoric Sweep",
        "2D Grid"
    ])
    
    # Step 2: Build Config (NO EXECUTION)
    if exp_type == "Epistemic Sweep":
        config = build_epistemic_config()  # Just forms
    elif exp_type == "Aleatoric Sweep":
        config = build_aleatoric_config()  # Just forms
    else:
        config = build_2d_grid_config()  # Just forms
    
    # Step 3: Save & Run
    if st.button("Run Experiment"):
        # Save config
        config_path = save_config(config)
        
        # Call appropriate script
        if exp_type == "Epistemic Sweep":
            runner.run_script("run_epistemic_sweep.py", config_path)
        elif exp_type == "Aleatoric Sweep":
            runner.run_script("run_aleatoric_sweep.py", config_path)
        else:
            runner.run_script("run_2d_grid_sweep.py", config_path)
    
    # Step 4: Visualize Results (read-only)
    if results_exist():
        results = load_results()
        visualize_results(results)  # Just plotting
```

## Benefits of This Architecture

### 1. Readability ✅
- One script per experiment type
- Clear file names (`run_epistemic_sweep.py`)
- Easy to find relevant code

### 2. Maintainability ✅
- Changes to epistemic logic → edit `run_epistemic_sweep.py`
- Changes to UI → edit `6_ui/experiment_builder.py`
- No mixing of concerns

### 3. Testability ✅
- Test scripts independently (no UI needed)
- Test UI independently (mock script calls)
- Test visualizations independently (use sample data)

### 4. Reusability ✅
- Scripts callable from:
  - Streamlit UI
  - Command line
  - Jupyter notebooks
  - CI/CD pipelines
- Configs portable (JSON files)

### 5. Debugging ✅
- Script crashes → check script logs
- UI bugs → check Streamlit code
- Viz issues → check viz components
- Clear error boundaries

## Summary

**Your idea is PERFECT!** Here's the concrete implementation:

1. **Streamlit = Config Builder** (forms, validation, save JSON)
2. **Scripts = Executors** (one per experiment type)
3. **Visualizations = Results Display** (load & plot, no computation)
4. **State Management = Config Progress Only** (not execution state)

This gives you:
- ✅ Clear separation
- ✅ Easy to read
- ✅ Easy to maintain
- ✅ Easy to test
- ✅ Easy to extend

The key insight: **Streamlit orchestrates, scripts execute, visualizations display.**