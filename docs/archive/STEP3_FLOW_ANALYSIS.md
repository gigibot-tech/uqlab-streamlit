# Step 3 Flow Analysis: UI → Pipeline → Runner

**Date**: 2026-06-24  
**Question**: Is the flow from Step 3 UI components through pipeline to runners clean and linear?

---

## Executive Summary

**Answer**: ✅ **YES, the flow is mostly linear and clean**, but there are **3 architectural issues**:

1. ❌ **per_class_launcher.py** - Unnecessary abstraction layer (see [`PER_CLASS_LAUNCHER_SIMPLIFICATION.md`](PER_CLASS_LAUNCHER_SIMPLIFICATION.md:1))
2. ⚠️ **step3_uncertainty.py** - Imports from both UI and orchestrator (minor coupling)
3. ✅ **Core pipeline** - Clean linear flow from workflow → run_spec → experiments

---

## Complete Flow Diagram

### Current Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────────┐
│ streamlit_app_progressive.py (Main App)                         │
│  - Initializes workflow in session_state                        │
│  - Renders step-by-step UI                                      │
│  - Calls launch functions                                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├─ Step 1: Dataset Selection
                 ├─ Step 2: Training Config
                 ├─ Step 3: Uncertainty Config ← FOCUS
                 ├─ Step 4: Evaluation Config
                 └─ Step 5: Review & Launch
                 
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Uncertainty Configuration                               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌─────────────────┐    ┌──────────────────────┐
│ step3_          │    │ step3_per_class_     │
│ uncertainty.py  │    │ table.py             │
│                 │    │                      │
│ - Main UI       │    │ - Per-class table    │
│ - Mode selector │    │ - Preset buttons     │
│ - Epistemic     │    │ - Sweep checkboxes   │
│ - Aleatoric     │    │                      │
└────────┬────────┘    └──────────┬───────────┘
         │                        │
         │ Stores in              │ Stores in
         │ workflow dict          │ workflow["per_class_config"]
         │                        │
         └────────┬───────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │ session_state      │
         │ .workflow          │
         │                    │
         │ {                  │
         │   "per_class_      │
         │    config": {...}, │
         │   "epistemic_      │
         │    sweep_preset":  │
         │    "quick",        │
         │   ...              │
         │ }                  │
         └────────┬───────────┘
                  │
                  │ User clicks "Launch" in Step 5
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAUNCH PHASE                                                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ launch_benchmark_primary()  │
    │ (from disentanglement_      │
    │  launcher.py)               │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ launch_workflow_            │
    │ experiments()               │
    │ (from experiment_           │
    │  launcher.py)               │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ generate_sweep_runs()       │
    │ (from run_spec.py)          │
    │                             │
    │ Checks workflow for:        │
    │ - per_class_config?         │
    │ - Legacy mode?              │
    │ - Sweep enabled?            │
    └─────────────┬───────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
    ┌─────────┐      ┌──────────────────┐
    │ Legacy  │      │ Per-Class Mode   │
    │ Mode    │      │                  │
    │         │      │ Calls:           │
    │ Uses:   │      │ generate_per_    │
    │ - under_│      │ class_           │
    │   train │      │ experiments()    │
    │ - noise │      │ (per_class_      │
    │   rate  │      │  sweep.py)       │
    └────┬────┘      └────────┬─────────┘
         │                    │
         └────────┬───────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ build_run_yaml()            │
    │ (from run_spec.py)          │
    │                             │
    │ Creates YAML config for     │
    │ run_fast_uncertainty_       │
    │ classification.py           │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ POST /api/v1/experiments    │
    │ (FastAPI backend)           │
    │                             │
    │ Stores in database          │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ DirectExecutor              │
    │ (backend/app/core/          │
    │  direct_executor.py)        │
    │                             │
    │ Runs: run_fast_             │
    │ uncertainty_                │
    │ classification.py           │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ Training & Evaluation       │
    │ (uqlab core library)        │
    └─────────────────────────────┘
```

---

## Step 3 File Structure

### UI Components (Frontend)

```
src/uqlab/ui_components/workflow/
├── step3_uncertainty.py          ← Main Step 3 UI coordinator
├── step3_per_class_table.py      ← Per-class configuration table
├── step3_four_region.py          ← Four-region partition editor (legacy)
└── step3_sweep_presets.py        ← Sweep preset selector (NEW, in progress)
```

### Orchestrator (Backend Logic)

```
src/uqlab_orchestrator/
├── experiment_launcher.py        ← Main launch coordinator
├── run_spec.py                   ← YAML generation & validation
├── per_class_sweep.py            ← Per-class sweep generation
├── per_class_launcher.py         ← ❌ UNNECESSARY (to be deleted)
└── disentanglement_launcher.py   ← Benchmark-specific launchers
```

---

## Flow Analysis by Phase

### Phase 1: UI Configuration (Step 3)

**File**: [`step3_uncertainty.py`](uqlab-streamlit/src/uqlab/ui_components/workflow/step3_uncertainty.py:1)

**Responsibility**: Render UI, collect user input, store in `workflow` dict

**Flow**:
```python
# User interacts with UI
render_step3_uncertainty(workflow)
    ↓
# Calls sub-components
render_per_class_table(workflow)  # Per-class mode
render_four_region_panel(workflow)  # Legacy mode
    ↓
# Stores configuration in session_state
workflow["per_class_config"] = {...}
workflow["epistemic_sweep_preset"] = "quick"
workflow["aleatoric_sweep_preset"] = "full"
```

**Status**: ✅ **Clean** - UI components only modify `workflow` dict

**Minor Issue**: [`step3_uncertainty.py:23`](uqlab-streamlit/src/uqlab/ui_components/workflow/step3_uncertainty.py:23) imports from `uqlab_orchestrator.per_class_sweep`:
```python
from uqlab_orchestrator.per_class_sweep import generate_per_class_experiments, get_sweep_summary
```

This is **acceptable** because it's only used for **preview/summary** display, not execution. The UI needs to show "You will generate N experiments" before launch.

---

### Phase 2: Launch Trigger (Step 5)

**File**: [`streamlit_app_progressive.py`](uqlab-streamlit/streamlit_app_progressive.py:146-151)

**Responsibility**: User clicks "Launch", trigger experiment creation

**Flow**:
```python
# User clicks "Launch" button in Step 5
_apply_launch_workflow(workflow, auto_start=True)
    ↓
launch_benchmark_primary(workflow, auto_start=True)
    ↓
# Delegates to experiment_launcher
launch_workflow_experiments(workflow, auto_start=True)
```

**Status**: ✅ **Clean** - Linear delegation

---

### Phase 3: Experiment Generation (Orchestrator)

**File**: [`experiment_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/experiment_launcher.py:89-114)

**Responsibility**: Convert `workflow` dict to experiment configs

**Flow**:
```python
launch_workflow_experiments(workflow)
    ↓
generate_sweep_configs(workflow)  # Returns (SweepType, List[configs])
    ↓
generate_sweep_runs(workflow)  # From run_spec.py
    ↓
# Check mode
if workflow.get("per_class_config"):
    # Per-class mode
    generate_per_class_experiments(...)  # From per_class_sweep.py
    ↓
    Returns List[DataConfig]
    ↓
    Convert to YAML dicts via build_run_yaml()
else:
    # Legacy mode
    build_run_yaml(workflow)  # Direct YAML generation
```

**Status**: ✅ **Clean** - Clear branching logic

**Problem**: [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) tries to insert itself here but adds no value (see [`PER_CLASS_LAUNCHER_SIMPLIFICATION.md`](PER_CLASS_LAUNCHER_SIMPLIFICATION.md:1))

---

### Phase 4: YAML Generation (Run Spec)

**File**: [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1)

**Responsibility**: Create validated YAML configs for runner script

**Flow**:
```python
build_run_yaml(workflow)
    ↓
# Extract all config sections
data_config = workflow["dataset_config"]
model_config = workflow["training_config"]
eval_config = workflow["evaluation_config"]
    ↓
# Build YAML structure
yaml_dict = {
    "data": {...},
    "model": {...},
    "training": {...},
    "evaluation": {...},
    "paths": {...}
}
    ↓
validate_run_yaml(yaml_dict)  # Fail-fast validation
    ↓
return yaml_dict
```

**Status**: ✅ **Clean** - Pure transformation function

---

### Phase 5: API Submission (Backend)

**File**: [`experiment_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/experiment_launcher.py:124-163)

**Responsibility**: Submit experiments to FastAPI backend

**Flow**:
```python
for (sweep_kind, config) in runs:
    name = run_name(sweep_kind, config, timestamp)
    ↓
    POST /api/v1/experiments/no-auth
    {
        "name": name,
        "config": config  # YAML dict
    }
    ↓
    if auto_start:
        POST /api/v1/experiments/{id}/start
```

**Status**: ✅ **Clean** - Standard REST API calls

---

### Phase 6: Execution (Runner)

**File**: `backend/app/core/direct_executor.py`

**Responsibility**: Execute `run_fast_uncertainty_classification.py`

**Flow**:
```python
DirectExecutor.execute(experiment_id)
    ↓
# Load config from database
config = experiment.config  # YAML dict
    ↓
# Save to temp file
yaml_path = f"/tmp/exp_{experiment_id}.yaml"
    ↓
# Run script
subprocess.run([
    "python",
    "scripts/run_fast_uncertainty_classification.py",
    "--config", yaml_path
])
```

**Status**: ✅ **Clean** - Standard subprocess execution

---

## Linearity Assessment

### ✅ Linear Flows (Good)

1. **UI → Workflow Dict**
   ```
   step3_uncertainty.py → workflow["per_class_config"]
   ```
   Clean one-way data flow.

2. **Workflow → YAML**
   ```
   workflow → generate_sweep_runs() → build_run_yaml() → YAML dict
   ```
   Pure transformation pipeline.

3. **YAML → Execution**
   ```
   YAML dict → API → Database → DirectExecutor → Runner script
   ```
   Standard request/response flow.

### ❌ Non-Linear Issues (Bad)

1. **per_class_launcher.py Circular Flow**
   ```
   workflow → generate_per_class_data_configs() → List[DataConfig]
       ↓ (DISCARDED!)
   workflow → launch_workflow_experiments() → generate_sweep_runs()
       ↓
   DataConfig.from_per_class_config() AGAIN
   ```
   **Solution**: Delete [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1)

2. **UI Imports Orchestrator Logic**
   ```
   step3_uncertainty.py imports per_class_sweep.generate_per_class_experiments()
   ```
   **Impact**: Minor - only for preview, not execution
   **Solution**: Acceptable as-is, or extract preview logic to separate module

---

## Dependency Graph

### Clean Dependencies (✅)

```
streamlit_app_progressive.py
    ↓ imports
uqlab.ui_components.workflow.step3_uncertainty
    ↓ imports
uqlab.ui_components.workflow.step3_per_class_table
    ↓ stores data in
session_state.workflow
    ↓ passed to
uqlab_orchestrator.experiment_launcher
    ↓ calls
uqlab_orchestrator.run_spec
    ↓ calls
uqlab_orchestrator.per_class_sweep (for sweep generation)
```

**Direction**: Top-down, no circular dependencies

### Problematic Dependencies (❌)

```
uqlab_orchestrator.per_class_launcher
    ↓ imports
uqlab_orchestrator.per_class_sweep
    ↓ imports
uqlab_orchestrator.experiment_launcher
    ↓ imports
uqlab_orchestrator.run_spec
    ↓ imports (should import)
uqlab_orchestrator.per_class_sweep
```

**Problem**: `per_class_launcher` sits between UI and `experiment_launcher`, creating unnecessary indirection.

---

## Recommendations

### 1. Delete per_class_launcher.py (High Priority)

**Reason**: Adds no value, creates circular flow

**Impact**: -132 lines of code, simpler architecture

**See**: [`PER_CLASS_LAUNCHER_SIMPLIFICATION.md`](PER_CLASS_LAUNCHER_SIMPLIFICATION.md:1)

### 2. Add Per-Class Sweep Detection to run_spec.py (Medium Priority)

**Current**: `run_spec.py` doesn't detect per-class sweeps

**Needed**: Add logic to check `workflow["per_class_config"]` for sweep flags

**Pseudocode**:
```python
def generate_sweep_runs(workflow):
    per_class_config = workflow.get("per_class_config")
    if per_class_config:
        has_sweeps = any(
            cfg.sweep_epistemic or cfg.sweep_aleatoric
            for cfg in per_class_config.values()
        )
        if has_sweeps:
            return _generate_per_class_sweep_runs(workflow)
    
    # Fall back to legacy mode
    return _generate_legacy_sweep_runs(workflow)
```

### 3. Optional: Extract Preview Logic (Low Priority)

**Current**: UI imports `per_class_sweep.generate_per_class_experiments()` for preview

**Alternative**: Create `per_class_preview.py` with lightweight preview functions

**Benefit**: Cleaner separation between UI and execution logic

**Cost**: Additional module, more complexity

**Recommendation**: Keep as-is unless preview logic grows significantly

---

## Conclusion

### Overall Assessment: ✅ **Mostly Linear and Clean**

**Strengths**:
- Clear step-by-step UI flow
- Pure transformation functions (workflow → YAML)
- Standard REST API integration
- No circular imports in core pipeline

**Weaknesses**:
- [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) adds unnecessary abstraction
- Minor UI/orchestrator coupling for preview display

**Action Items**:
1. ✅ **Delete** [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) (see [`PER_CLASS_LAUNCHER_SIMPLIFICATION.md`](PER_CLASS_LAUNCHER_SIMPLIFICATION.md:1))
2. ⚠️ **Add** per-class sweep detection to [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1)
3. ℹ️ **Optional**: Extract preview logic (low priority)

**Timeline**: ~65 minutes to implement recommendations

---

**Made with Bob**