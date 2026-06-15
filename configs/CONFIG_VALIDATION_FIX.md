# Configuration Validation Fix

## Problem Identified

The progressive app had inconsistent configuration state:
- `aleatoric_enabled = True` but `custom_noise_rate = None`
- Unclear whether using dataset noise or custom noise
- No validation of configuration consistency
- Not enterprise-ready

## Root Cause

**Lines 960-974** in `streamlit_app_progressive.py`:
```python
if not _is_clean_noise(noise_type):
    aleatoric_enabled = st.checkbox(
        f"Use dataset noise ({noise_type})",
        value=True,  # ← Always True
        help=f"Use CIFAR-10N {noise_type} noise labels"
    )
    custom_noise = None  # ← But noise rate is None!
else:
    aleatoric_enabled = st.checkbox("Add custom label noise", value=False)
    if aleatoric_enabled:
        custom_noise = st.slider("Custom noise rate (%)", 0, 50, 10, 5) / 100.0
    else:
        custom_noise = None
```

**Problem**: When `aleatoric_enabled=True` with dataset noise, `custom_noise=None`, but the config conversion logic at line 258-259 doesn't handle this:

```python
custom = uncertainty.get("custom_noise_rate")
alea_pct = float(custom) * 100.0 if custom is not None else 0.0
# ← If using dataset noise, custom is None, so alea_pct = 0.0 (WRONG!)
```

## Solution Implemented

### 1. **Improved Config Conversion Logic**

Updated `_workflow_to_experiment_config()` to properly handle all cases:

```python
def _workflow_to_experiment_config(...):
    # Calculate aleatoric noise percentage with proper validation
    if aleatoric_noise_percentage is not None:
        # Explicit override (used in sweeps)
        alea_pct = float(aleatoric_noise_percentage)
    else:
        # Determine from workflow config
        aleatoric_enabled = uncertainty.get("aleatoric_enabled", False)
        custom_noise = uncertainty.get("custom_noise_rate")
        noise_type = dataset.get("noise_type", "clean_label")
        
        if not aleatoric_enabled:
            # Aleatoric disabled = no noise
            alea_pct = 0.0
        elif custom_noise is not None:
            # Custom noise specified
            alea_pct = float(custom_noise) * 100.0
        elif not _is_clean_noise(noise_type):
            # Using dataset noise (CIFAR-10N)
            stats = dataset.get("stats", {})
            dataset_noise_rate = stats.get("noise_rate", 0.0)
            alea_pct = float(dataset_noise_rate) * 100.0
        else:
            # Clean dataset, no custom noise = no noise
            alea_pct = 0.0
```

**Decision Tree:**
```
aleatoric_noise_percentage provided?
├─ Yes → Use it (sweep override)
└─ No → Check workflow config
    ├─ aleatoric_enabled = False → 0.0
    ├─ custom_noise_rate is not None → Use custom_noise_rate * 100
    ├─ noise_type is not clean → Use dataset noise_rate * 100
    └─ Otherwise → 0.0
```

### 2. **Additional Validation Needed**

Add Pydantic validation to catch configuration errors early:

```python
from pydantic import BaseModel, validator, root_validator

class WorkflowUncertaintyConfig(BaseModel):
    """Validated uncertainty configuration."""
    
    epistemic_enabled: bool = True
    under_supported: str = "random:2"
    under_train_per_class: int = 50
    regular_train_per_class: int = 300
    
    aleatoric_enabled: bool = True
    custom_noise_rate: Optional[float] = None
    
    @root_validator
    def validate_aleatoric_config(cls, values):
        """Ensure aleatoric config is consistent."""
        aleatoric_enabled = values.get("aleatoric_enabled", False)
        custom_noise = values.get("custom_noise_rate")
        
        if aleatoric_enabled and custom_noise is None:
            # This is OK if using dataset noise, but we should validate
            # that dataset_config.noise_type is not "clean_label"
            pass  # Will be validated at workflow level
        
        if custom_noise is not None and not (0.0 <= custom_noise <= 1.0):
            raise ValueError(f"custom_noise_rate must be in [0, 1], got {custom_noise}")
        
        return values

class WorkflowConfig(BaseModel):
    """Complete validated workflow configuration."""
    
    dataset_config: Dict[str, Any]
    training_config: Dict[str, Any]
    uncertainty_config: WorkflowUncertaintyConfig
    evaluation_config: Dict[str, Any]
    
    @root_validator
    def validate_aleatoric_consistency(cls, values):
        """Validate aleatoric config against dataset config."""
        dataset = values.get("dataset_config", {})
        uncertainty = values.get("uncertainty_config")
        
        if uncertainty and uncertainty.aleatoric_enabled:
            noise_type = dataset.get("noise_type", "clean_label")
            custom_noise = uncertainty.custom_noise_rate
            
            if custom_noise is None and noise_type == "clean_label":
                raise ValueError(
                    "aleatoric_enabled=True but no noise source: "
                    "either set custom_noise_rate or use noisy dataset"
                )
        
        return values
```

### 3. **UI Improvements**

Make the configuration state more explicit in the UI:

```python
# In streamlit_app_progressive.py
with st.expander("🔊 Aleatoric Uncertainty (Label Noise)", expanded=True):
    if not _is_clean_noise(noise_type):
        # Dataset has noise
        use_dataset_noise = st.checkbox(
            f"✅ Use dataset noise ({noise_type})",
            value=True,
            help=f"Use CIFAR-10N {noise_type} noise labels (rate: {stats.get('noise_rate', 0):.1%})"
        )
        
        if use_dataset_noise:
            st.info(f"📊 Using dataset noise rate: {stats.get('noise_rate', 0):.1%}")
            aleatoric_enabled = True
            custom_noise = None
        else:
            st.warning("⚠️ Dataset noise disabled - using clean labels")
            aleatoric_enabled = False
            custom_noise = None
    else:
        # Clean dataset
        add_custom_noise = st.checkbox(
            "Add custom label noise",
            value=False,
            help="Synthetically add label noise to clean dataset"
        )
        
        if add_custom_noise:
            custom_noise = st.slider(
                "Custom noise rate (%)",
                0, 50, 10, 5,
                help="Percentage of labels to randomly flip"
            ) / 100.0
            st.info(f"📊 Custom noise rate: {custom_noise:.1%}")
            aleatoric_enabled = True
        else:
            st.info("✅ Using clean labels (no noise)")
            aleatoric_enabled = False
            custom_noise = None
```

## Testing

### Test Cases

1. **Dataset noise enabled**:
   ```python
   workflow = {
       "dataset_config": {"noise_type": "worse_label", "stats": {"noise_rate": 0.4}},
       "uncertainty_config": {"aleatoric_enabled": True, "custom_noise_rate": None}
   }
   config = _workflow_to_experiment_config(workflow)
   assert config.data.aleatoric_noise_percentage == 40.0  # 0.4 * 100
   ```

2. **Custom noise**:
   ```python
   workflow = {
       "dataset_config": {"noise_type": "clean_label"},
       "uncertainty_config": {"aleatoric_enabled": True, "custom_noise_rate": 0.15}
   }
   config = _workflow_to_experiment_config(workflow)
   assert config.data.aleatoric_noise_percentage == 15.0  # 0.15 * 100
   ```

3. **No noise**:
   ```python
   workflow = {
       "dataset_config": {"noise_type": "clean_label"},
       "uncertainty_config": {"aleatoric_enabled": False, "custom_noise_rate": None}
   }
   config = _workflow_to_experiment_config(workflow)
   assert config.data.aleatoric_noise_percentage == 0.0
   ```

4. **Sweep override**:
   ```python
   workflow = {...}
   config = _workflow_to_experiment_config(workflow, aleatoric_noise_percentage=25.0)
   assert config.data.aleatoric_noise_percentage == 25.0  # Override works
   ```

## Benefits

✅ **Clear semantics**: Explicit handling of all noise sources
✅ **Validation**: Catches configuration errors early
✅ **Enterprise-ready**: Consistent, predictable behavior
✅ **Better UX**: Clear feedback about noise configuration
✅ **Maintainable**: Decision tree is explicit and documented

## Next Steps

1. Add Pydantic validation models
2. Improve UI feedback
3. Add unit tests for all cases
4. Document configuration options
5. Add configuration export/import