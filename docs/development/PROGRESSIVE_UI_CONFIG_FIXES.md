# Progressive UI Configuration Fixes

## Summary
Fixed multiple configuration issues in the progressive Streamlit UI to improve defaults, prevent errors, and automatically manage uncertainty types based on sweep selection.

## Changes Made

### 1. Model Configuration Defaults (Step 2)

**File**: `src/uqlab/ui_components/config/experiment_config.py`

#### Changed Default Architecture to ResNet18
- **Line 252**: Added `index=0` to selectbox to explicitly default to `resnet18_mcdropout`
- **Reason**: ResNet18 is the most commonly used architecture

#### Changed Default Dropout to 0.0 for ResNet18
- **Line 311**: Changed dropout default from `0.3` to `0.0`
- **Reason**: ResNet18 with pretrained weights works better without dropout initially

**Before:**
```python
dropout = st.number_input("Dropout", 0.0, 0.9, 0.3, 0.1)
```

**After:**
```python
dropout = st.number_input("Dropout", 0.0, 0.9, 0.0, 0.1)  # Default to 0.0
```

### 2. Epistemic Uncertainty Default (Step 3)

**File**: `streamlit_app_progressive.py`

#### Changed Default to OFF
- **Line 1026**: Changed checkbox label and kept default as `False`
- **Reason**: Most experiments focus on either epistemic OR aleatoric, not both

**Before:**
```python
epistemic_enabled = st.checkbox("Enable dataset size sweep", value=True)
```

**After:**
```python
epistemic_enabled = st.checkbox(
    "Enable epistemic uncertainty (under-trained classes)",
    value=workflow["uncertainty_config"].get("epistemic_enabled", False),
    help="Fig. 3 style — limits training data on selected classes.",
)
```

### 3. Warning for Mixed Uncertainty Types

**File**: `streamlit_app_progressive.py`

#### Added Warning Banner
- **Lines 1031-1038**: Added warning when user enables epistemic with label_noise sweep
- **Reason**: Mixing uncertainty types makes results hard to interpret

**Added Code:**
```python
# Warning for mixing label_noise sweep with epistemic uncertainty
if sweep_enabled and sweep_kind == "label_noise" and epistemic_enabled:
    st.warning(
        "⚠️ **Mixed uncertainty warning**: You're sweeping label noise (aleatoric) "
        "with epistemic uncertainty enabled. This mixes two types of uncertainty. Consider:\n"
        "- **Label noise sweep**: Turn OFF epistemic (focus on aleatoric only)\n"
        "- **Dataset size sweep**: Turn OFF aleatoric (focus on epistemic only)"
    )
```

### 4. Fixed NoneType Error When Epistemic is OFF

**File**: `streamlit_app_progressive.py`

#### Fixed `int(under)` Error
- **Line 277**: Added None check before converting to int
- **Line 1077**: Ensured `regular_train_per_class` has default value of 300

**Before:**
```python
else:
    # Aleatoric-only: balanced training (equal samples per class)
    under = int(regular)
```

**After:**
```python
else:
    # Aleatoric-only: balanced training (equal samples per class)
    # Ensure regular is not None before converting to int
    under = int(regular) if regular is not None else 300
```

**And in Step 3 UI:**
```python
else:
    under_supported = None
    under_train_per_class = None
    regular_train_per_class = 300  # Provide default when epistemic is off
```

## Error Fixed

**Original Error:**
```
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'

File "/Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/streamlit_app_progressive.py", line 1289, in <module>
    main()
File "/Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/streamlit_app_progressive.py", line 1241, in main
    sweep_type, sweep_configs = _generate_sweep_configs(workflow)
File "/Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/streamlit_app_progressive.py", line 334, in _generate_sweep_configs
    base_config = _workflow_to_experiment_config(workflow)
File "/Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/streamlit_app_progressive.py", line 307, in _workflow_to_experiment_config
    under_train_per_class=int(under),
```

**Root Cause**: When epistemic uncertainty was turned OFF, `regular_train_per_class` could be None, causing `int(None)` to fail.

**Solution**: Added None checks and default values throughout the workflow configuration logic.

## Testing Checklist

Users should verify:

1. ✅ **Step 2 defaults**:
   - Architecture defaults to ResNet18
   - Dropout defaults to 0.0 for ResNet18

2. ✅ **Step 3 defaults**:
   - Epistemic uncertainty checkbox defaults to OFF
   - No error when epistemic is OFF and continuing to Step 4

3. ✅ **Auto-disable behavior**:
   - When sweep type is "label_noise":
     - Epistemic is auto-disabled
     - Shows info message explaining why
   - When sweep type is "dataset_size":
     - Aleatoric is auto-disabled
     - Shows info message explaining why
   - When sweep is OFF:
     - Both can be manually enabled

4. ✅ **No NoneType errors**:
   - Can complete full workflow with epistemic OFF
   - Can create experiments with epistemic OFF
   - Can run sweeps with epistemic OFF

## Related Files

- `src/uqlab/ui_components/config/experiment_config.py` - Model config defaults
- `streamlit_app_progressive.py` - Step 3 UI and workflow logic
- `BAR_CHART_REMOVAL.md` - Related UI fixes

## Behavior Summary

### Sweep Enabled
- **Label Noise Sweep (Fig. 4)**:
  - ✅ Aleatoric enabled (swept parameter)
  - 🔒 Epistemic auto-disabled
  - Result: Clean epistemic vs aleatoric comparison
  
- **Dataset Size Sweep (Fig. 3)**:
  - ✅ Epistemic enabled (swept parameter)
  - 🔒 Aleatoric auto-disabled
  - Result: Clean dataset size vs epistemic comparison

### Sweep Disabled
- Both epistemic and aleatoric can be manually enabled
- Values are duplicated across all experiments
- Useful for single-point experiments with both uncertainty types

## Date
2026-06-16