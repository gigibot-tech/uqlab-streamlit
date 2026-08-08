# Label Noise Sweep Fix

## Problem
The Progressive UI's "Fig. 4 (Label Noise Sweep)" feature was creating all experiments with 0% noise instead of sweeping from 0% to 100%.

## Root Cause
The code was relying on the external `BatchGenerator.generate_aleatoric_sweep()` method from the `uqlab_orchestrator` package, which wasn't properly applying the noise values to the generated configs.

## Solution: Simplified Direct Config Generation

**Replaced complex external dependency with simple, direct approach:**

### Before (Complex)
```python
def _generate_sweep_configs(workflow: Dict[str, Any]) -> Tuple[SweepType, List[ExperimentConfig]]:
    """Generate sweep configs using BatchGenerator."""
    base_config = _workflow_to_experiment_config(workflow)
    generator = BatchGenerator()  # External dependency
    
    # ... logic ...
    
    if kind == "label_noise" and u.get("aleatoric_sweep_enabled", True):
        values = u.get("aleatoric_sweep_values") or LABEL_NOISE_SWEEP.get(mode, LABEL_NOISE_SWEEP["quick"])
        configs = generator.generate_aleatoric_sweep(base_config, values)  # Black box
        return SweepType.ALEATORIC_1D, configs
```

**Problem:** The `BatchGenerator` wasn't properly setting `aleatoric_noise_percentage` in the configs.

### After (Simple)
```python
def _generate_sweep_configs(workflow: Dict[str, Any]) -> Tuple[SweepType, List[ExperimentConfig]]:
    """Generate sweep configs - simplified direct approach."""
    base_config = _workflow_to_experiment_config(workflow)
    
    # ... logic ...
    
    # Aleatoric sweep: vary aleatoric_noise_percentage
    if kind == "label_noise" and u.get("aleatoric_sweep_enabled", True):
        values = u.get("aleatoric_sweep_values") or LABEL_NOISE_SWEEP.get(mode, LABEL_NOISE_SWEEP["quick"])
        configs = []
        for val in values:
            config = copy.deepcopy(base_config)
            config["aleatoric_noise_percentage"] = val  # Direct assignment
            configs.append(config)
        return SweepType.ALEATORIC_1D, configs
```

**Benefits:**
- ✅ **Transparent**: You can see exactly what's happening
- ✅ **Reliable**: Direct assignment guarantees the value is set
- ✅ **Simple**: No external dependencies or black boxes
- ✅ **Maintainable**: Easy to debug and modify

## Epistemic Sweep Also Simplified

Applied the same pattern to epistemic sweeps:

```python
# Epistemic sweep: vary under_train_per_class
if kind == "dataset_size" and u.get("epistemic_sweep_enabled", True):
    values = u.get("epistemic_sweep_values") or aligned_under_train_sweep(mode)
    configs = []
    for val in values:
        config = copy.deepcopy(base_config)
        config["under_train_per_class"] = val  # Direct assignment
        configs.append(config)
    return SweepType.EPISTEMIC_1D, configs
```

## Testing

To verify the fix works:

1. **Start the Progressive UI:**
   ```bash
   cd uqlab-streamlit
   streamlit run streamlit_app_progressive.py
   ```

2. **Configure a Label Noise Sweep:**
   - Step 1: Select dataset (CIFAR-10N)
   - Step 2: Choose "Fig. 4 (Label Noise Sweep)"
   - Step 3: Configure model (any settings)
   - Step 4: Launch experiments

3. **Verify Results:**
   - Check that 6 experiments are created (for quick mode: 0%, 20%, 40%, 60%, 80%, 100%)
   - Each experiment should have different `aleatoric_noise_percentage` values
   - The `aleatoric_like` pool size should increase with noise percentage:
     - 0% noise → `aleatoric_like=0` (no noisy samples)
     - 20% noise → `aleatoric_like≈60` (20% of 300 regular samples)
     - 100% noise → `aleatoric_like≈300` (all regular samples are noisy)

## Files Modified

- **streamlit_app_progressive.py** (lines 398-421):
  - Simplified `_generate_sweep_configs()` function
  - Removed `BatchGenerator` import
  - Added direct config generation for both sweep types

## Design Philosophy

**"Simple is better than complex"** - This fix embodies the principle that:
- Direct, transparent code is better than abstraction layers
- Fewer dependencies = fewer failure points
- Explicit is better than implicit
- Easy to understand = easy to maintain

The original approach tried to be "clever" by delegating to an external package, but this added complexity without benefit. The new approach is straightforward: "I want configs with different noise values, so I'll create configs with different noise values."