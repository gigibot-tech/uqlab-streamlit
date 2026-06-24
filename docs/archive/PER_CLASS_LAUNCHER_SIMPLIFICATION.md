# Per-Class Launcher Simplification Analysis

**Date**: 2026-06-24  
**Issue**: Overcomplicated integration between per-class config and pipeline execution

---

## Executive Summary

The [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) module adds **unnecessary abstraction layers** that duplicate existing functionality. The current implementation:

1. ❌ **Generates DataConfig objects** then **discards them**
2. ❌ **Calls existing launcher** which **regenerates the same configs**
3. ❌ **Adds wrapper functions** that provide no value
4. ❌ **Creates circular data flow** (workflow → DataConfig → workflow → DataConfig)

**Recommendation**: **DELETE** [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) entirely and integrate directly with existing infrastructure.

---

## Current Architecture Problems

### Problem 1: Redundant DataConfig Generation

**Current Flow** (WASTEFUL):
```
workflow (session state)
    ↓
per_class_launcher.generate_per_class_data_configs()
    ↓
List[DataConfig] objects created
    ↓
per_class_launcher.launch_per_class_experiments()
    ↓
experiment_launcher.launch_workflow_experiments(workflow)  ← IGNORES DataConfigs!
    ↓
run_spec.generate_sweep_runs(workflow)
    ↓
DataConfig.from_per_class_config() called AGAIN  ← DUPLICATE WORK!
```

**Evidence from code**:

[`per_class_launcher.py:128-129`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:128-129):
```python
# Generate DataConfig list from per-class settings
data_configs = generate_per_class_data_configs(workflow)
```

[`per_class_launcher.py:149-154`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:149-154):
```python
result = launch_workflow_experiments(
    workflow,  # ← Passes workflow, NOT data_configs!
    auto_start=auto_start,
    timestamp=timestamp,
    highlight_callback=highlight_callback,
)
```

**The `data_configs` variable is NEVER USED!** It's generated, then thrown away.

---

### Problem 2: Wrapper Functions Add No Value

#### 2.1 `is_per_class_mode()` - Trivial Getter

[`per_class_launcher.py:19-28`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:19-28):
```python
def is_per_class_mode(workflow: Dict[str, Any]) -> bool:
    """Check if workflow is using per-class configuration mode."""
    return workflow.get("use_per_class_mode", False)
```

**Simplification**: Just use `workflow.get("use_per_class_mode", False)` directly.

#### 2.2 `get_per_class_config()` - Trivial Getter

[`per_class_launcher.py:31-40`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:31-40):
```python
def get_per_class_config(workflow: Dict[str, Any]) -> Optional[Dict[int, Any]]:
    """Extract per-class configuration from workflow."""
    return workflow.get("per_class_config")
```

**Simplification**: Just use `workflow.get("per_class_config")` directly.

#### 2.3 `get_sweep_presets()` - Trivial Getter

[`per_class_launcher.py:43-54`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:43-54):
```python
def get_sweep_presets(workflow: Dict[str, Any]) -> tuple[str, str]:
    """Extract sweep presets from workflow."""
    epistemic = workflow.get("epistemic_sweep_preset", "quick")
    aleatoric = workflow.get("aleatoric_sweep_preset", "quick")
    return epistemic, aleatoric
```

**Simplification**: Just access `workflow` dict directly where needed.

---

### Problem 3: Circular Data Flow

The current architecture creates a circular dependency:

```
UI (step3_per_class_table.py)
    ↓ stores in session_state
workflow["per_class_config"]
    ↓ passed to
per_class_launcher.generate_per_class_data_configs()
    ↓ calls
per_class_sweep.generate_per_class_experiments()
    ↓ calls
DataConfig.from_per_class_config()
    ↓ returns
List[DataConfig]
    ↓ DISCARDED, then
experiment_launcher.launch_workflow_experiments(workflow)
    ↓ calls
run_spec.generate_sweep_runs(workflow)
    ↓ calls
DataConfig.from_per_class_config() AGAIN  ← CIRCULAR!
```

**Root Cause**: The launcher tries to be "smart" by pre-generating configs, but the existing infrastructure already does this correctly.

---

## Existing Infrastructure (CORRECT)

The existing [`experiment_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/experiment_launcher.py:1) already handles everything correctly:

### Flow 1: Legacy Mode (under_supported_classes)

```
workflow (with under_supported_classes)
    ↓
experiment_launcher.launch_workflow_experiments()
    ↓
run_spec.generate_sweep_runs()
    ↓
run_spec.build_run_yaml()
    ↓
DataConfig created from legacy fields
    ↓
Experiments launched
```

### Flow 2: Per-Class Mode (per_class_config)

```
workflow (with per_class_config)
    ↓
experiment_launcher.launch_workflow_experiments()
    ↓
run_spec.generate_sweep_runs()
    ↓
run_spec.build_run_yaml()
    ↓
DataConfig.from_per_class_config() called
    ↓
Experiments launched
```

**The existing infrastructure ALREADY supports per-class mode!**

See [`classification.py:166-195`](uqlab-streamlit/src/uqlab/shared/config/classification.py:166-195):
```python
@classmethod
def from_per_class_config(
    cls,
    per_class_config: Dict[int, PerClassConfig],
    dataset_name: str = "cifar10",
    noise_type: str = "worse_label",
    eval_per_group: int = 600,
) -> "DataConfig":
    """Create DataConfig from per-class configuration."""
    return cls(
        dataset_name=dataset_name,
        noise_type=noise_type,
        per_class_config=per_class_config,
        eval_per_group=eval_per_group,
        # Legacy fields set to None/defaults
        under_supported_classes=None,
        under_train_per_class=10,
        regular_train_per_class=500,
        aleatoric_noise_percentage=0.0,
    )
```

---

## Recommended Simplification

### Step 1: DELETE per_class_launcher.py

**File to delete**: [`src/uqlab_orchestrator/per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) (172 lines)

**Reason**: Adds no value, duplicates existing functionality.

### Step 2: Update UI to Call Existing Infrastructure Directly

**File**: [`src/uqlab/ui_components/workflow/step4_launch.py`](uqlab-streamlit/src/uqlab/ui_components/workflow/step4_launch.py:1)

**Current (WRONG)**:
```python
from uqlab_orchestrator.per_class_launcher import (
    is_per_class_mode,
    launch_per_class_experiments,
)

if is_per_class_mode(workflow):
    result = launch_per_class_experiments(
        workflow,
        auto_start=auto_start,
        highlight_callback=lambda exp_id: st.session_state.update({"highlighted_experiment": exp_id}),
    )
```

**Simplified (CORRECT)**:
```python
from uqlab_orchestrator.experiment_launcher import launch_workflow_experiments

# Works for BOTH legacy and per-class modes!
result = launch_workflow_experiments(
    workflow,
    auto_start=auto_start,
    highlight_callback=lambda exp_id: st.session_state.update({"highlighted_experiment": exp_id}),
)
```

**Why this works**:
- [`experiment_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/experiment_launcher.py:89-114) calls [`run_spec.generate_sweep_runs()`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1)
- [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1) checks if `workflow["per_class_config"]` exists
- If it exists, uses [`DataConfig.from_per_class_config()`](uqlab-streamlit/src/uqlab/shared/config/classification.py:166-195)
- If not, uses legacy mode with `under_supported_classes`

### Step 3: Keep per_class_sweep.py (USEFUL)

**File**: [`src/uqlab_orchestrator/per_class_sweep.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_sweep.py:1)

**Keep these functions** (they provide value):
- [`generate_epistemic_sweep_values()`](uqlab-streamlit/src/uqlab_orchestrator/per_class_sweep.py:29-57) - Generates sweep ranges
- [`generate_aleatoric_sweep_values()`](uqlab-streamlit/src/uqlab_orchestrator/per_class_sweep.py:60-84) - Generates sweep ranges
- [`generate_per_class_experiments()`](uqlab-streamlit/src/uqlab_orchestrator/per_class_sweep.py:87-177) - Creates experiment configs
- [`get_sweep_summary()`](uqlab-streamlit/src/uqlab_orchestrator/per_class_sweep.py:180-224) - Provides UI metadata

**These are called by [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1) during sweep generation.**

---

## Integration with run_spec.py

The existing [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1) needs ONE small update to support per-class sweeps:

**Current**: Only handles legacy sweeps (under_train, noise_rate)

**Needed**: Add per-class sweep detection

**Location**: [`run_spec.py:generate_sweep_runs()`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1)

**Pseudocode**:
```python
def generate_sweep_runs(workflow: Dict[str, Any]) -> List[Tuple[SweepKind, Dict[str, Any]]]:
    """Generate sweep configurations from workflow."""
    
    # Check for per-class mode
    per_class_config = workflow.get("per_class_config")
    if per_class_config:
        # Check if any class has sweeps enabled
        has_epistemic_sweep = any(cfg.sweep_epistemic for cfg in per_class_config.values())
        has_aleatoric_sweep = any(cfg.sweep_aleatoric for cfg in per_class_config.values())
        
        if has_epistemic_sweep or has_aleatoric_sweep:
            # Generate per-class sweep experiments
            from uqlab_orchestrator.per_class_sweep import generate_per_class_experiments
            
            epistemic_preset = workflow.get("epistemic_sweep_preset", "quick")
            aleatoric_preset = workflow.get("aleatoric_sweep_preset", "quick")
            dataset_name = workflow.get("dataset_config", {}).get("dataset_name", "cifar10")
            noise_type = workflow.get("dataset_config", {}).get("noise_type", "worse_label")
            eval_per_group = workflow.get("evaluation_config", {}).get("eval_per_group", 600)
            
            data_configs = generate_per_class_experiments(
                per_class_config=per_class_config,
                epistemic_preset=epistemic_preset,
                aleatoric_preset=aleatoric_preset,
                dataset_name=dataset_name,
                noise_type=noise_type,
                eval_per_group=eval_per_group,
            )
            
            # Convert DataConfig objects to YAML dicts
            runs = []
            for data_config in data_configs:
                yaml_dict = build_run_yaml_from_data_config(workflow, data_config)
                sweep_kind = "per_class_epistemic" if has_epistemic_sweep else "per_class_aleatoric"
                runs.append((sweep_kind, yaml_dict))
            return runs
    
    # Fall back to legacy sweep logic
    return _generate_legacy_sweep_runs(workflow)
```

---

## Benefits of Simplification

### Before (Current)
- **3 modules**: `per_class_launcher.py`, `per_class_sweep.py`, `experiment_launcher.py`
- **Circular data flow**: workflow → DataConfig → workflow → DataConfig
- **Duplicate work**: Generates configs twice
- **Confusing**: Two different launch paths (legacy vs per-class)

### After (Simplified)
- **2 modules**: `per_class_sweep.py`, `experiment_launcher.py`
- **Linear data flow**: workflow → run_spec → DataConfig → experiments
- **No duplication**: Configs generated once
- **Unified**: Single launch path handles both modes

### Code Reduction
- **Delete**: 172 lines ([`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1))
- **Add**: ~40 lines (per-class sweep detection in [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1))
- **Net**: -132 lines, simpler architecture

---

## Migration Path

### Phase 1: Add Per-Class Support to run_spec.py (30 min)
1. Update [`generate_sweep_runs()`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1) to detect per-class sweeps
2. Call [`generate_per_class_experiments()`](uqlab-streamlit/src/uqlab_orchestrator/per_class_sweep.py:87-177) when needed
3. Convert DataConfig objects to YAML dicts

### Phase 2: Update UI to Use Unified Launcher (15 min)
1. Remove imports from [`per_class_launcher`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1)
2. Call [`launch_workflow_experiments()`](uqlab-streamlit/src/uqlab_orchestrator/experiment_launcher.py:89-114) directly
3. Remove per-class mode branching logic

### Phase 3: Delete per_class_launcher.py (5 min)
1. Delete [`src/uqlab_orchestrator/per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1)
2. Update `__all__` exports in [`src/uqlab_orchestrator/__init__.py`](uqlab-streamlit/src/uqlab_orchestrator/__init__.py:1)

### Phase 4: Test (15 min)
1. Test legacy mode (under_supported_classes)
2. Test per-class mode (per_class_config)
3. Test per-class sweeps (epistemic + aleatoric)

**Total Time**: ~65 minutes

---

## Conclusion

The [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) module is a **premature abstraction** that adds complexity without benefit. The existing infrastructure in [`experiment_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/experiment_launcher.py:1) and [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1) already handles both legacy and per-class modes correctly.

**Recommendation**: Delete [`per_class_launcher.py`](uqlab-streamlit/src/uqlab_orchestrator/per_class_launcher.py:1) and integrate per-class sweep detection directly into [`run_spec.py`](uqlab-streamlit/src/uqlab_orchestrator/run_spec.py:1).

This will:
- ✅ Reduce code by 132 lines
- ✅ Eliminate circular data flow
- ✅ Remove duplicate work
- ✅ Simplify architecture
- ✅ Make the system easier to understand and maintain

---

**Made with Bob**