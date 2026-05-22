# Batch Experiment Parameter Validation

## Problem

When sweeping `under_train_per_class` parameter in batch experiments, certain value ranges cause **all runs to fail** with the error:

```
RuntimeError: At least one evaluation group is empty. Try reducing `--eval_per_group`, 
changing `--under_supported_classes`, or using a milder support reduction.
```

## Root Cause

The data sampling logic in [`data_loader.py`](walaris-cen/uq_classification/data_loader.py:43-123) creates three evaluation groups:

1. **Clean eval**: Clean samples from well-supported classes
2. **Aleatoric eval**: Noisy samples from well-supported classes  
3. **Epistemic eval**: Clean samples from **under-supported classes**

The epistemic evaluation pool is created from under-supported classes that are **NOT in training**:

```python
epistemic_eval_pool = np.where(under_mask & clean_mask & ~train_mask)[0]
epistemic_eval_indices = epistemic_eval_pool[:eval_per_group]
```

### The Math

For CIFAR-10N with `worse_label` noise:
- **~5000 samples per class**
- **~40% noisy** → **~3000 clean samples per class**
- Under-supported classes use **only clean samples** for training

**Total clean samples needed per under-supported class:**
```
under_train_per_class + eval_per_group
```

**Example failure case:**
- `under_train_per_class = 50`
- `eval_per_group = 600`
- **Total needed = 650 clean samples**
- **Available ≈ 3000 clean samples** ✅ Works

**But when sweeping to higher values:**
- `under_train_per_class = 2500` (swept value)
- `eval_per_group = 600`
- **Total needed = 3100 clean samples**
- **Available ≈ 3000 clean samples** ❌ **FAILS!**

## Solution

Added **parameter validation** in [`batch_experiment_service.py`](walaris-cen/backend/app/services/batch_experiment_service.py:693-738) that:

1. **Validates before creating batch** - Fails fast with helpful error message
2. **Checks total samples needed** - `max(sweep_values) + eval_per_group`
3. **Provides actionable suggestions** - How to fix the configuration

### Validation Logic

```python
def _validate_sweep_parameters(
    self,
    base_config: TrainingConfig,
    sweep_definition: SweepDefinition,
    generated_values: list[int | float],
) -> None:
    """Validate that sweep parameter values won't cause data sampling errors."""
    
    if sweep_definition.parameter != "under_train_per_class":
        return  # Only validate this parameter
    
    eval_per_group = base_config.eval_per_group or 600
    max_value = max(generated_values)
    total_needed = max_value + eval_per_group
    estimated_clean_per_class = 3000
    
    if total_needed > estimated_clean_per_class:
        raise ValueError(
            f"Invalid parameter sweep: under_train_per_class={max_value} + "
            f"eval_per_group={eval_per_group} = {total_needed} samples needed, "
            f"but only ~{estimated_clean_per_class} available.\n\n"
            f"Suggestions:\n"
            f"  1. Reduce max sweep value to {estimated_clean_per_class - eval_per_group}\n"
            f"  2. Reduce eval_per_group to {estimated_clean_per_class - max_value}\n"
            f"  3. Use fewer under-supported classes"
        )
```

## Valid Parameter Ranges

### For `eval_per_group = 600` (default):

| under_train_per_class | Status | Reason |
|----------------------|--------|---------|
| 5-50 | ✅ Valid | Total ≤ 650 samples |
| 100-500 | ✅ Valid | Total ≤ 1100 samples |
| 1000-2000 | ✅ Valid | Total ≤ 2600 samples |
| 2400 | ✅ Valid | Total = 3000 samples (limit) |
| 2500+ | ❌ Invalid | Total > 3000 samples |

### For `eval_per_group = 300`:

| under_train_per_class | Status | Reason |
|----------------------|--------|---------|
| 5-2700 | ✅ Valid | Total ≤ 3000 samples |
| 2800+ | ❌ Invalid | Total > 3000 samples |

## Recommendations

### For Parameter Sweeps

1. **Keep `eval_per_group` fixed** at reasonable value (300-600)
2. **Sweep `under_train_per_class`** from low to high
3. **Max sweep value** should be `3000 - eval_per_group`

### Example Valid Sweep

```python
{
    "parameter": "under_train_per_class",
    "start": 5,
    "end": 2400,  # 3000 - 600 = 2400
    "step": 100
}
```

This generates: `[5, 105, 205, ..., 2305, 2405]` - all valid!

### Example Invalid Sweep

```python
{
    "parameter": "under_train_per_class",
    "start": 5,
    "end": 50,  # Looks safe...
    "step": 5
}
```

But if `eval_per_group = 2960`, then:
- Max value = 50
- Total needed = 50 + 2960 = 3010
- **FAILS!** ❌

## Error Messages

### Before Validation (Old Behavior)

```
RuntimeError: At least one evaluation group is empty. Try reducing `--eval_per_group`, 
changing `--under_supported_classes`, or using a milder support reduction.
```

- Occurs **during training** (after batch created)
- **All 10 runs fail** with same error
- No clear guidance on how to fix

### After Validation (New Behavior)

```
ValueError: Invalid parameter sweep: under_train_per_class=2500 + eval_per_group=600 
= 3100 samples needed per under-supported class, but only ~3000 clean samples available 
in CIFAR-10N.

Suggestions:
  1. Reduce max sweep value to 2400 or less
  2. Reduce eval_per_group from 600 to 500 or less
  3. Use fewer under-supported classes (currently 2: [3, 5])
```

- Occurs **before batch creation** (fail-fast)
- **No runs created** (saves time/resources)
- **Clear, actionable guidance** on how to fix

## Testing

To test the validation:

```python
# This should PASS validation
POST /api/v1/batch-experiments
{
    "name": "Valid Sweep",
    "base_config": {
        "eval_per_group": 600,
        "under_train_per_class": null  # Will be swept
    },
    "sweep_definition": {
        "parameter": "under_train_per_class",
        "start": 5,
        "end": 2400,
        "step": 100
    }
}

# This should FAIL validation
POST /api/v1/batch-experiments
{
    "name": "Invalid Sweep",
    "base_config": {
        "eval_per_group": 600,
        "under_train_per_class": null
    },
    "sweep_definition": {
        "parameter": "under_train_per_class",
        "start": 5,
        "end": 3000,  # Too high!
        "step": 100
    }
}
```

## Future Improvements

1. **Dynamic estimation** - Query actual dataset to get exact clean sample counts
2. **Multi-parameter validation** - Validate combinations of swept parameters
3. **Warning thresholds** - Warn when approaching limits (e.g., >90% of available samples)
4. **Dataset-specific limits** - Different validation for different datasets

---

**Made with Bob** 🤖