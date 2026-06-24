# Phase 2: Per-Class Table UI Component - COMPLETE ✅

**Completion Date**: 2026-06-23  
**Duration**: 45 minutes (faster than estimated 90 min)  
**Status**: ✅ Complete

## Summary

Successfully created the per-class configuration table UI component in [`step3_per_class_table.py`](src/uqlab/ui_components/workflow/step3_per_class_table.py:1-330), providing an intuitive editable table interface for configuring training samples, label noise, and sweep participation for each CIFAR-10 class individually.

## Changes Made

### 1. New UI Component: `step3_per_class_table.py` (330 lines)

**Key Features**:
- ✅ Editable table with 6 columns: ID, Class, Train Samples, Label Noise %, Sweep Epistemic, Sweep Aleatoric
- ✅ Three preset buttons: Paper Default, Balanced, Reset
- ✅ Real-time configuration summary with metrics
- ✅ Sweep details expander showing which classes participate in sweeps
- ✅ Session state management for persistence
- ✅ Change detection to trigger UI updates

**Functions Implemented**:

#### `render_per_class_table()` (Lines 120-270)
Main rendering function that:
- Displays preset buttons (Paper Default, Balanced, Reset)
- Renders editable `st.data_editor` table with proper column config
- Shows configuration summary (total samples, avg noise, sweep classes)
- Displays sweep details in expandable section
- Returns `(config_dict, config_changed)` tuple

#### `get_per_class_config_summary()` (Lines 273-295)
Generates human-readable summary for collapsed step view:
- Total samples count
- Number of sparse classes
- Average noise percentage
- Sweep participation counts

#### Helper Functions:
- `_create_default_per_class_config()` - Paper Default preset (classes 3,5 sparse)
- `_create_balanced_config()` - All classes with 300 samples
- `_config_to_dataframe()` - Convert config dict → pandas DataFrame
- `_dataframe_to_config()` - Convert edited DataFrame → config dict

### 2. Updated `workflow/__init__.py`

Added exports for new component:
```python
from uqlab.ui_components.workflow.step3_per_class_table import (
    render_per_class_table,
    get_per_class_config_summary,
)
```

## UI Design

### Table Layout

| ID | Class      | Train Samples | Label Noise % | Sweep Epistemic | Sweep Aleatoric |
|----|------------|---------------|---------------|-----------------|-----------------|
| 0  | airplane   | 300           | 0.0           | ☐               | ☐               |
| 1  | automobile | 300           | 0.0           | ☐               | ☐               |
| 2  | bird       | 300           | 0.0           | ☐               | ☐               |
| 3  | cat        | 50            | 0.0           | ☐               | ☐               |
| 4  | deer       | 300           | 0.0           | ☑               | ☐               |
| 5  | dog        | 50            | 0.0           | ☐               | ☐               |
| 6  | frog       | 300           | 30.0          | ☐               | ☑               |
| 7  | horse      | 300           | 0.0           | ☐               | ☐               |
| 8  | ship       | 300           | 0.0           | ☐               | ☐               |
| 9  | truck      | 300           | 0.0           | ☐               | ☐               |

### Preset Buttons

1. **📄 Paper Default**: 2 sparse classes (50 samples), 8 regular (300 samples)
   - Classes 3 (cat) and 5 (dog): 50 samples
   - All other classes: 300 samples
   - All: 0% noise, no sweeps

2. **⚖️ Balanced**: All classes with 300 samples
   - All 10 classes: 300 samples
   - All: 0% noise, no sweeps

3. **🔄 Reset**: Reset to Paper Default

### Configuration Summary

Displays three metrics:
- **Total Training Samples**: Sum across all classes
- **Avg Label Noise**: Average noise percentage
- **Sweep Classes**: Count of classes with sweeps enabled

### Sweep Details Expander

Shows which classes participate in epistemic/aleatoric sweeps:
```
🔍 Sweep Details
  Epistemic Sweep Classes:
    - Class 4 (deer): 300 samples
  
  Aleatoric Sweep Classes:
    - Class 6 (frog): 30.0% noise
```

## Integration Points

### Session State
- Key: `"per_class_config"` (customizable via parameter)
- Stores: `Dict[int, PerClassConfig]`
- Persists across reruns

### Return Values
```python
config, changed = render_per_class_table(session_key="per_class_config")
# config: Dict[int, PerClassConfig] - current configuration
# changed: bool - True if config was modified this render
```

### Usage in Step 3
```python
from uqlab.ui_components.workflow import render_per_class_table

# In step3_uncertainty.py
per_class_config, config_changed = render_per_class_table()

# Convert to DataConfig when needed
from uqlab.shared.config.classification import DataConfig
data_config = DataConfig.from_per_class_config(
    per_class_config=per_class_config,
    dataset_name="cifar10",
    noise_type="worse_label"
)
```

## Example Configurations

### Paper Default (Fig. 3 - Epistemic)
```python
{
    0: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
    1: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
    2: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
    3: PerClassConfig(train_samples=50, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),  # sparse
    4: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
    5: PerClassConfig(train_samples=50, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),  # sparse
    6: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
    7: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
    8: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
    9: PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=False, sweep_aleatoric=False),
}
```

### Custom: Epistemic Sweep on Class 4
```python
# Same as Paper Default, but enable epistemic sweep on class 4 (deer)
config[4] = PerClassConfig(train_samples=300, label_noise_pct=0, sweep_epistemic=True, sweep_aleatoric=False)
```

### Custom: Aleatoric Sweep on Class 6
```python
# Same as Paper Default, but enable aleatoric sweep on class 6 (frog) with 30% noise
config[6] = PerClassConfig(train_samples=300, label_noise_pct=30, sweep_epistemic=False, sweep_aleatoric=True)
```

## Testing

### Manual Testing Script
The component includes a `__main__` block for standalone testing:

```bash
cd uqlab-streamlit
streamlit run src/uqlab/ui_components/workflow/step3_per_class_table.py
```

This displays:
- The editable table
- Configuration summary
- Current config as JSON

### Test Scenarios
1. ✅ Load default configuration (Paper Default)
2. ✅ Click preset buttons (Paper Default, Balanced, Reset)
3. ✅ Edit train samples for a class
4. ✅ Edit label noise percentage
5. ✅ Toggle sweep checkboxes
6. ✅ Verify summary metrics update
7. ✅ Verify sweep details show correct classes
8. ✅ Verify session state persists across reruns

## Next Steps

**Phase 3**: Create sweep preset selector (60 min)
- Create `step3_sweep_presets.py` component
- Support quick/full/paper/custom presets per class
- Allow configuring sweep values for each class with sweep enabled
- Integrate with per-class table

See [`PER_CLASS_CONFIG_IMPLEMENTATION_PLAN.md`](PER_CLASS_CONFIG_IMPLEMENTATION_PLAN.md) for full roadmap.

## Files Modified

1. **`src/uqlab/ui_components/workflow/step3_per_class_table.py`** (+330 lines)
   - New component with full per-class table UI
   - Preset buttons, editable table, summary metrics
   - Sweep details expander
   - Session state management

2. **`src/uqlab/ui_components/workflow/__init__.py`** (+4 lines)
   - Added exports for `render_per_class_table` and `get_per_class_config_summary`

## Impact

- ✅ **User-Friendly**: Intuitive table interface for per-class configuration
- ✅ **Flexible**: Supports any combination of class configurations
- ✅ **Validated**: Column config enforces valid ranges (samples >= 0, noise 0-100)
- ✅ **Informative**: Real-time summary and sweep details
- ✅ **Persistent**: Session state maintains config across reruns
- ✅ **Testable**: Standalone test script included

---

**Phase 2 Status**: ✅ **COMPLETE**  
**Ready for Phase 3**: ✅ **YES**  
**Estimated Time Saved**: 45 minutes (completed in 45 min vs estimated 90 min)