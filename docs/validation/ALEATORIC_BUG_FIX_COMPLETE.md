# Aleatoric Noise Percentage Bug - COMPLETE FIX

## Problem Summary
All experiments had `aleatoric_noise_percentage: 0.0` in their config files, even when users selected "Add random label flipping" with custom percentages (e.g., 20%). This prevented proper aleatoric uncertainty sweeps.

## Root Causes Found

### Bug #1: Missing Field in API ExperimentConfig Class
**Location:** `backend/app/api/routes/experiments.py:65-88`

**Problem:** The `ExperimentConfig` Pydantic model was missing the `aleatoric_noise_percentage` field entirely.

**Fix Applied:**
```python
class ExperimentConfig(BaseModel):
    """Experiment configuration matching YAML structure."""
    
    # Data parameters
    noise_type: str = "worse_label"
    aleatoric_noise_percentage: float = 0.0  # ← ADDED THIS LINE
    under_supported_classes: str = "3,5"
    # ... rest of fields
```

### Bug #2: Missing Field in YAML Config Builder
**Location:** `backend/app/api/routes/experiments.py:148-154`

**Problem:** The `_create_experiment_impl()` function manually built the config_dict but forgot to include `aleatoric_noise_percentage` in the `data` section.

**Fix Applied:**
```python
config_dict = {
    "seed": 42,
    "device": "auto",
    "data": {
        "noise_type": experiment.config.noise_type,
        "aleatoric_noise_percentage": experiment.config.aleatoric_noise_percentage,  # ← ADDED THIS LINE
        "under_supported_classes": experiment.config.under_supported_classes,
        # ... rest of fields
    },
    # ... rest of config
}
```

## Complete Data Flow (Now Fixed)

### 1. UI Layer (Streamlit)
```python
# ui_components/experiment_config.py:142-152
noise_source = st.radio(
    "Label Noise Strategy",
    [
        "No noise (0%, clean labels)",
        "CIFAR-10N pre-existing noise (~18-40%, not sweepable)",
        "Custom random flipping (0-50%, sweepable)"  # ← Default (index=2)
    ],
    index=2,
    key=f'{key_prefix}noise_source_selection'
)

# Returns custom_noise_rate (0-100 percentage)
if noise_source.startswith("Custom random"):
    custom_noise_rate = st.slider("Noise Percentage", 0, 50, 20)  # e.g., 20
```

### 2. Form Submission (Streamlit)
```python
# streamlit_app.py:365-380
base_config = build_base_experiment_config(
    # ... other params
    aleatoric_noise_percentage=custom_noise_rate,  # ← Passes 20.0
)
```

### 3. Config Builder (UI Components)
```python
# ui_components/experiment_config.py:489
return {
    # ... other fields
    "aleatoric_noise_percentage": aleatoric_noise_percentage,  # ← 20.0
}
```

### 4. API Request (Streamlit → FastAPI)
```python
# streamlit_app.py:393-400
experiment_data = {
    "name": exp_name,
    "config": base_config  # ← Contains aleatoric_noise_percentage: 20.0
}

response = requests.post(
    f"{API_BASE_URL}/api/v1/experiments/no-auth",
    json=experiment_data
)
```

### 5. API Endpoint (FastAPI)
```python
# backend/app/api/routes/experiments.py:65-70
class ExperimentConfig(BaseModel):
    noise_type: str = "worse_label"
    aleatoric_noise_percentage: float = 0.0  # ✅ NOW DEFINED
    # ... other fields
```

### 6. YAML Config Generation (FastAPI)
```python
# backend/app/api/routes/experiments.py:148-154
config_dict = {
    "data": {
        "noise_type": experiment.config.noise_type,
        "aleatoric_noise_percentage": experiment.config.aleatoric_noise_percentage,  # ✅ NOW INCLUDED
        # ... other fields
    }
}
```

### 7. Config File Saved
```yaml
# /tmp/uqlab_experiments/{exp_id}/config.yaml
data:
  noise_type: worse_label
  aleatoric_noise_percentage: 20.0  # ✅ NOW CORRECT!
  under_supported_classes: "3,5"
  # ... other fields
```

### 8. Training Script Reads Config
```python
# scripts/run_fast_uncertainty_classification.py:255
aleatoric_noise_percentage = data_config.get("aleatoric_noise_percentage", 0.0)

# Line 281-284
if aleatoric_noise_percentage > 0:
    print(f"🎯 Loading CLEAN CIFAR-10 for custom noise injection ({aleatoric_noise_percentage}%)")
    # Loads clean CIFAR-10 and injects custom noise
```

## Verification Steps

### 1. Test Single Experiment Creation
```bash
# In Streamlit UI:
# 1. Go to "Single Experiment" tab
# 2. Select "Custom random flipping (0-50%, sweepable)"
# 3. Set slider to 20%
# 4. Create experiment
# 5. Check config file:
cat /tmp/uqlab_experiments/{exp_id}/config.yaml | grep aleatoric
# Expected: aleatoric_noise_percentage: 20.0
```

### 2. Test Batch Experiment Sweep
```bash
# In Streamlit UI:
# 1. Go to "Batch Experiments (1D)" tab
# 2. Select swept parameter: "aleatoric_noise_percentage"
# 3. Set sweep: start=0, end=40, step=10
# 4. Create batch
# 5. Check generated experiments:
for exp in /tmp/uqlab_experiments/batch_*/experiments/*/config.yaml; do
    echo "=== $exp ==="
    grep "aleatoric_noise_percentage" $exp
done
# Expected: 0.0, 10.0, 20.0, 30.0, 40.0
```

### 3. Verify Backend Logs
```bash
# Watch backend logs during experiment execution:
tail -f backend_logs.txt | grep "Loading"
# Expected for 20% noise:
# "🎯 Loading CLEAN CIFAR-10 for custom noise injection (20.0%)"
# Expected for 0% noise:
# "🎯 Loading CIFAR-10N with existing noise (type: worse_label)"
```

## Files Modified

1. **`backend/app/api/routes/experiments.py`**
   - Line 70: Added `aleatoric_noise_percentage: float = 0.0` to `ExperimentConfig`
   - Line 150: Added `"aleatoric_noise_percentage": experiment.config.aleatoric_noise_percentage` to config_dict

2. **`ui_components/experiment_config.py`** (Previously fixed)
   - Lines 110-152: Added `key_prefix` parameter to `render_aleatoric_config()`
   - Line 149: Changed default index to 2 (Custom random flipping)

3. **`streamlit_app.py`** (Previously fixed)
   - Line 207: Added `key_prefix="single_"` to `render_aleatoric_config()` call

4. **`ui_components/batch_config.py`** (Previously fixed)
   - Line 207: Added `key_prefix="batch_"` to `render_aleatoric_config()` call

## Testing Hypothesis

With these fixes, we can now properly test the formal validation criteria:

### Aleatoric Sweep (0%, 10%, 20%, 30%, 40%)
**Expected Results:**
- **(C1) ✅**: `inverse_coherence` AUROC should INCREASE with noise percentage
- **(O2) ✅**: `dominance` and `inverse_mass` AUROC should remain STABLE across noise levels
- **(O1) ✅**: Aleatoric signals should NOT respond to epistemic changes

### Epistemic Sweep (under_train_per_class: 10, 50, 100, 200, 300)
**Expected Results:**
- **(C2) ✅**: `inverse_mass` and `dominance` AUROC should INCREASE with fewer samples
- **(O1) ✅**: Epistemic signals should NOT respond to aleatoric changes

## Status
✅ **COMPLETE** - Both backend bugs fixed, FastAPI auto-reloaded with `--reload` flag
⏳ **PENDING** - User needs to create new experiments to verify fixes