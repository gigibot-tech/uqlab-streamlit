# Frozen Model Fix - Complete ✅

## Issue

When running the refactored progressive app, encountered:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for DataConfig
aleatoric_noise_percentage
  Instance is frozen [type=frozen_instance, input_value=0, input_type=int]
```

## Root Cause

The Pydantic models in `backend/app/domain/models.py` have `frozen=True` in their `Config` class:

```python
class DataConfig(BaseModel):
    # ... fields ...
    
    class Config:
        frozen = True  # Makes instances immutable
```

This means once a model is created, its fields cannot be modified. The `BatchGenerator` was trying to modify configs after copying them:

```python
# ❌ WRONG - Tries to modify frozen model
config = base_config.model_copy(deep=True)
config.data.aleatoric_noise_percentage = noise  # ERROR: Instance is frozen!
```

## Solution

Instead of modifying copied models, create new instances with updated values using Pydantic's `model_copy(update={...})`:

```python
# ✅ CORRECT - Creates new instance with updated value
new_data = base_config.data.model_copy(update={"aleatoric_noise_percentage": float(noise)})
config = base_config.model_copy(update={"data": new_data})
```

## Files Fixed

### `src/uqlab_orchestrator/batch/generator.py`

#### 1. `generate_epistemic_sweep()` (Lines 38-44)
**Before:**
```python
configs = []
for under_train in under_train_values:
    config = base_config.model_copy(deep=True)
    config.data.under_train_per_class = under_train  # ❌ Modifies frozen model
    configs.append(config)
return configs
```

**After:**
```python
configs = []
for under_train in under_train_values:
    # Create new config with modified value (models are frozen)
    new_data = base_config.data.model_copy(update={"under_train_per_class": under_train})
    config = base_config.model_copy(update={"data": new_data})
    configs.append(config)
return configs
```

#### 2. `generate_aleatoric_sweep()` (Lines 69-75)
**Before:**
```python
configs = []
for noise in noise_values:
    config = base_config.model_copy(deep=True)
    config.data.aleatoric_noise_percentage = noise  # ❌ Modifies frozen model
    configs.append(config)
return configs
```

**After:**
```python
configs = []
for noise in noise_values:
    # Create new config with modified value (models are frozen)
    new_data = base_config.data.model_copy(update={"aleatoric_noise_percentage": float(noise)})
    config = base_config.model_copy(update={"data": new_data})
    configs.append(config)
return configs
```

#### 3. `generate_2d_grid()` (Lines 94-101)
**Before:**
```python
configs = []
for under_train in under_train_values:
    for noise in noise_values:
        config = base_config.model_copy(deep=True)
        config.data.under_train_per_class = under_train  # ❌ Modifies frozen model
        config.data.aleatoric_noise_percentage = noise   # ❌ Modifies frozen model
        configs.append(config)
return configs
```

**After:**
```python
configs = []
for under_train in under_train_values:
    for noise in noise_values:
        # Create new config with both modified values (models are frozen)
        new_data = base_config.data.model_copy(update={
            "under_train_per_class": under_train,
            "aleatoric_noise_percentage": float(noise)
        })
        config = base_config.model_copy(update={"data": new_data})
        configs.append(config)
return configs
```

## Why Frozen Models?

Frozen models provide several benefits:
1. **Immutability** - Prevents accidental modifications
2. **Thread Safety** - Safe to share across threads
3. **Hashability** - Can be used as dict keys or in sets
4. **Predictability** - Config can't change after creation

## Testing

The app should now work correctly:

```bash
cd uqlab-streamlit
source .venv/bin/activate
streamlit run streamlit_app_progressive.py
```

**Expected behavior:**
- ✅ App starts without errors
- ✅ Single experiments can be created
- ✅ Epistemic sweeps generate multiple configs
- ✅ Aleatoric sweeps generate multiple configs
- ✅ 2D grid sweeps work correctly
- ✅ All configs are properly validated

## Key Takeaway

When working with frozen Pydantic models:
- ❌ **Don't** try to modify fields after creation
- ✅ **Do** use `model_copy(update={...})` to create new instances with changes

This pattern ensures type safety and immutability while still allowing flexible config generation.